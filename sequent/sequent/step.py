'''
Created on Oct 19, 2016

@author: arnon
'''
import logging
import os
from acris import MergedChainedDict, Sequence, Mediator
import collections
from .sequent_types import SequentError, LogocalOp
from .event import Event
from eventor.eventor_types import StepStatus, StepReplay, Invoke
from eventor.utils import decorate_all, print_method
import eventor
from collections.abc import Sequence as AbcSequence

module_logger=logging.getLogger(__name__)

def evaluate_status(enders_status):
    result=StepStatus.success
    for status in enders_status.values():
        if StepStatus[status.name] == StepStatus.failure:
            result=StepStatus.failure
    return result

class IterGen(object):
    def __init__(self, l):
        self.l=l
        
    def __call__(self):
        return (x for x in self.l)

class Container(object):
    def __init__(self, ev, step, progname, repeat=[1,], iter_triggers=(), end_triggers=(),):
        module_logger.debug("[ step %s ] Container initialization\n    iter_triggers: %s\n    end_triggers: %s\n    repeat: %s" % (progname, iter_triggers, end_triggers, repeat) )
        self.ev=ev
        self.progname=progname
        self.starters=iter_triggers
        self.enders=end_triggers
        if isinstance(repeat, AbcSequence):
            repeat=IterGen(repeat)
        self.repeat=repeat
        self.loop_index=0
        self.initiating_sequence=None
        self.step=step
        self.max_concurrent=self.step.config['max_concurrent']
        self.triggers=None
        
    def __call__(self, initial=False, eventor_task_sequence=''): 
        if initial:
            self.iter=Mediator(self.repeat())
            todos=1
            self.triggers=self.step.create_flow(self.ev, trigger=False,)
            self.initiating_sequence=eventor_task_sequence #self.ev.get_task_sequence()
            self.loop_index=0
            # eventor_task_sequence is parent sequence, take as is
            sequence=eventor_task_sequence
            module_logger.debug("[ Step %s ] Setting sequence: %s" % (self.progname, sequence, ))
        else:
            # this is child sequence - convert to parent
            sequence=str(eventor_task_sequence)
            parts=sequence.rpartition('.')
            #sequence=parts[0]
            sequence=parts[0] if parts[0] else parts[2]
            if sequence:
                todos=self.ev.count_todos_like("%s.%%" % (sequence)) 
            else:
                todos=self.ev.count_todos() 
            module_logger.debug("[ Step %s/%s ] TODOs count: %s" % (self.progname, sequence, todos))
        
        # for sequential: if it is finished, it can check if there is another item to to.
        # TODO: for concurrent, need to check if max concurrent reached.  If not, activated another.
        # TODO: if resources are required, before starting, need to grab resource. 
        if todos <2 or initial:    
            module_logger.debug("[ Step %s/%s ] Trying to get next sequence" % (self.progname, eventor_task_sequence)) 
            try:
                item=next(self.iter)
            except StopIteration :
                module_logger.debug("[ Step %s ] Received StopIteration (%s)" % (self.progname, self.loop_index,))
                item=None
            else:
                module_logger.debug("[ Step %s ] Received NextIteration: %s (%s)" % (self.progname, repr(item), self.loop_index,))    
                
            if item is not None:
                # TODO - values need to specific to  task sequence
                #os.environ['SEQUENT_LOOP_VALUE']=str(item)
                self.loop_index+=1
                if str(sequence):
                    sequence="%s." % sequence
                else:
                    sequence=''
                sequence="%s%s" % (sequence, self.loop_index) 
                for trigger in self.triggers:
                    module_logger.debug("[ Step %s ] Triggering starter %s/%s" % (self.progname, repr(trigger), self.loop_index,))
                    self.ev.remote_trigger_event(trigger, sequence,)
                #for trigger in self.starters:
                #    module_logger.debug("[ Step %s ] triggering starter: %s" % (self.progname, repr(trigger),))
                #    self.ev.remote_trigger_event(trigger, self.loop_index,)
            else:
                module_logger.debug("[ Step %s ] Enders: %s" % (self.progname, list(self.step.ender_steps.keys()),))
                enders_status=self.ev.get_task_status(self.step.ender_steps.keys(), self.loop_index)
                status=evaluate_status(enders_status)
                #self.ev.update_task()
                module_logger.debug("[ Step %s ] Container step status for triggering: %s" % (self.progname, status.name,))
                for trigger in self.enders[status]:
                    module_logger.debug("[ Step %s ] Triggering ender: %s" % (self.progname, repr(trigger),))
                    self.ev.remote_trigger_event(trigger, self.initiating_sequence,)
            
        return True


#class Step(metaclass=decorate_all(print_method(module_logger.debug))):
class Step(object):
    """A step in steps structure.  
       
        Each step has unique id that identifies it within Steps.
       
        A step is considered completed if it returns gradior.complete.
        step can also return gradior.failed or gradior.active.
       
        If step generate exception, it is considered gradior.FAILED.  The exception is
        also registered and could be referenced.
        
    """
    
    config_defaults=eventor.Eventor.config_defaults

    def __init__(self, parent=None, name=None, func=None, args=[], kwargs={}, config={}, require=(), acquires=[], releases=None, recovery={}, repeat=[1,]):
        
        self.id=id
        self.func=func
        self.args=args
        self.kwargs=kwargs
        self.config=MergedChainedDict(config, os.environ, Step.config_defaults)
        self.parent=parent
        self.require=require
        self.acquires=acquires
        self.releases=releases if releases is not None else acquires
        self.recovery=recovery
        self.loop=repeat
        self.path=name 
        if self.parent and parent.path:
            self.path='%s_%s' % (parent.path, name)
            
        self.__sequence_next_step=Sequence("SequentNextStep")
        
        self.__steps=dict()
        self.steps=self.__steps
        self.__events=list()
        self.__container=None
        
    def __repr__(self):
        return "Step( path(%s), step(%s),)" % (self.path, self.__steps)
    
    def __str__(self):
        return repr(self)
    
    def is_container(self):
        return len(self.__steps) >0
    
    def add_step(self, name=None, func=None, args=[], kwargs={}, require=None, acquires=[], releases=None, config={}, recovery={}, repeat=[1,], resources=[]):
        """add a step to steps object
        
        Args:
            
            name: (string) unique identifier for this step
            
            func: (callable) optional function to execute when step is activated
            
            args: replacing super-step args.  
                If None, super-step args will be used.  
                Otherwise, this will be used
            
            kwargs: overriding super-step kwargs.
                If None, None will be used
                Otherwise, override super-step with this.
                
            require: (iterator) list of require objects for this step to be activated.  object can be either 
                Event or tuple pair of (step, status)
                
            acquires: (iterator) list of resource requirements.  Each resource requirements is a tuple of 
                Resource type and amount.

            releases: (iterator) list of resource to release.  Each resource requirements is a tuple of 
                Resource type and amount. If not provided, defaults to acquires.

            config: parameters can include the following keys:
                - stop_on_exception=True 
                
            recovery: map step status to recovery option
                
            repeat: (iterator) list of value to repeat 
            
        """
         
        config=MergedChainedDict(config, os.environ, self.config)
        if repeat is None:
            repeat=list()        
        result=Step( parent=self, name=name, func=func, args=args, kwargs=kwargs, config=config, require=require, acquires=acquires, releases=releases, recovery=recovery, repeat=repeat)

        if name:
            step=self.__steps.get(result.path, None)
            if step:
                raise SequentError("Attempting to add step, but name already used: '%s'" % (name))
          
        
        self.__steps[result.path]=result

        return result

    def add_event(self, require):
        event=Event(require=require)
        return event
            
    def get_start_event_name(self,):
        return '%s_start' % self.path
    
    def get_next_event_name(self, ):
        return '%s_next' % self.path
    
    def get_complete_event_name(self, ):
        return '%s_complete' % self.path
    
    def get_end_event_name(self, ):
        return '%s_end' % self.path
    
    def get_step_name(self, ):
        return '%s' % self.path
    
    def update_step_triggers(self, trigger_map, status, event):
        try:
            triggers=trigger_map[status]
        except:
            triggers=list()
            trigger_map[status]=triggers
        triggers.append(event)

    def get_require_step_event(self, evr, step, status):
        #try:
        #    trigger_map=step.triggers
        #except:
        #    trigger_map=dict()
        #    step.triggers=trigger_map
           
        if status != StepStatus.complete:
            result="%s_%s" % (step.path, status.name)
            event=evr.add_event(result)
            #step.update_step_triggers(trigger_map, status, event)
            module_logger.debug("[ Step %s ] Adding triggers: %s > %s" % (step.path, status, event)) 
        else:
            names=["%s_%s" % (step.path, status.name) for status in [StepStatus.success, StepStatus.failure,]]
            result= "( " + " or ".join(names) + " )" 
            #for status, name in [(StepStatus.success), (StepStatus.failure)]:
            #    name=success="%s_%s" % (step.path, status.name)
            #    event=evr.add_event(name)
            #    #step.update_step_triggers(trigger_map, status, event)
            #    module_logger.debug("[ Step %s ] Adding triggers: %s > %s" % (step.path, status, event)) 
                              
        return result
        
    def convert_require(self, evr, require):
        #require=step.require
        items=list()
        for arg in require:
            if type(arg) == str:
                result=arg
            elif isinstance(arg, Event):
                #result=arg.id
                #evr.add_event(result)
                result=self.convert_require(evr, arg.require)
            elif isinstance(arg, tuple):
                if len(arg) == 0:
                    result=''
                elif len(arg) == 1:
                    result= self.expr_to_str(*arg)
                elif arg[0] == LogocalOp.or_:
                    result=self.or_(evr, *arg[1:])
                elif len(arg) == 2 and isinstance(arg[0], Step):
                    result=self.get_require_step_event(evr, arg[0], arg[1])
                    # add to steps that are NOT enders
                    self.ender_steps[arg[0].path]=arg[0]
                else:    
                    result= "(" + self.expr_to_str(*arg) +")" 
            else:
                raise SequentError("unknown variable in require: %s" % repr(arg))
            items.append(result)
                
        expr="(" + ") and (".join(items) + ")"
        return expr
        
    def or_(self, evr, *args):
        items=list()
        for arg in args:
            result= self.convert_require(evr, arg)
            items.append(result)
                
        expr=" or ".join(items)
        return expr
    
    def __create_eventor_events(self, evr):
        events=dict()
        self.__starter_events=dict()
        self.__starter_steps=dict()
        self.ender_steps=dict()
        
        todo=[self,]
        todo.extend(self.__steps.values())
        
        # convert require into event's expression and fill potential ender_steps
        for event in self.__events:
            expr=self.convert_require(evr, event.require)
            evr.add_event(expr)
        # dive into steps
        for step in todo:
            if self != step:
                if not step.require:
                    event=evr.add_event(step.get_start_event_name())
                    self.__starter_events[step.path]=event
                    self.__starter_steps[step.path]=step
                else:
                    expr=self.convert_require(evr, step.require)
                    event=evr.add_event(step.get_start_event_name(), expr=expr)
                events[event.id_]=event
                
                # Add success and failure events
                step.triggers=dict()
                statuses=[StepStatus.success, StepStatus.failure]                
                for status in statuses:
                    event_name="%s_%s" % (step.path, status.name)
                    event=evr.add_event(event_name)
                    step.triggers.update({status: (event,)})
                    events[event.id_]=event
                    
                # add end event for container steps
                if step.is_container():
                    event_name=step.get_end_event_name()
                    event=evr.add_event(event_name)
                    step.triggers.update({status: (event,)})
                    events[event.id_]=event
                      
        self.__eventor_events=events
        # since 'convert_requireed' filled ender_steps with those steps that can NOT be enders!!!!
        # so we remove to be left with enders only steps
        enders=list(set(self.__steps.keys())-set(self.ender_steps.keys()))
        self.__ender_events=dict()
        self.ender_steps=dict()
        for step_path in enders:
            # if step.path not in self.__ender_steps.keys():
            step=self.__steps[step_path]
            event=evr.add_event(step.get_complete_event_name())
            self.__ender_events[step_path]=event
            self.ender_steps[step_path]=step

        module_logger.debug("[ Step %s ] Starter and enders events\n    Starter: %s\n    Ender:%s" % (self.path, self.__starter_events, self.__ender_events))
            
    def __get_eventor_step_start_event(self, step):
        return self.__events[step.get_start_event_name()]
    
    def __get_eventor_step_next_event(self, step):
        return self.__events[step.get_next_event_name()]
    
    def __get_eventor_step_end_event(self, step):
        return self.__events[step.get_end_event_name()]
    
    def __create_eventor_steps(self, evr,):
        steps=dict()
        todo=list(self.__steps.values())
        
        start_events=list()
        
        container_recovery={
            StepStatus.ready: StepReplay.rerun, 
            StepStatus.active: StepReplay.rerun, 
            StepStatus.failure: StepReplay.rerun, 
            StepStatus.success: StepReplay.rerun,
            StepStatus.allocate: StepReplay.rerun,
            StepStatus.fueled: StepReplay.rerun,
            }  

        for step in todo:
            try:
                triggers=step.triggers
            except:
                triggers={}
            
            container=step.parent.__container
            #module_logger.debug("[ Step %s ] Found container of parent %s" %(step.path, step.parent.path))
            
            module_logger.debug("[ Step %s ] Creating Eventor steps\n    Starter: %s\n    Ender:%s\n    Triggers: %s" % (step.path,step.parent.__starter_steps, step.parent.ender_steps, triggers))                   
                
            step_is_ender=step.path in self.ender_steps.keys()
            event_is_starter=False if step.require else True
            
            # If it is ender step, and it is within super-step, it must trigger next.
            if step_is_ender and container is not None:
                parent=step.parent
                #next_id="%s_%s"% (parent.get_next_event_name(), parent.__sequence_next_step())
                next_id=parent.get_next_event_name()
                next_step=evr.add_step(next_id, func=container, kwargs={'initial': False,}, recovery=container_recovery,
                                       config={'task_construct': Invoke, 'max_concurrent':1, 'sequence_arg_name':'eventor_task_sequence',})
                steps[next_step.path]=next_step
                next_event=evr.add_event(next_id)
                triggers={StepStatus.complete: (next_event, ),}
                module_logger.debug("[ Step %s ] Add ender trigger: %s" % (step.path, triggers)) 
                evr.add_assoc(next_event, next_step)
            
            if not step.is_container():                    
                evr_step=evr.add_step(step.get_step_name(), func=step.func, args=step.args, kwargs=step.kwargs, 
                                      acquires=step.acquires, releases=step.releases, triggers=triggers, config=step.config)
                steps[step.path]=evr_step
                start_event=self.__eventor_events[step.get_start_event_name()]
                evr.add_assoc(start_event, evr_step)
                if event_is_starter:
                    start_events.append(start_event)
            else:
                try:
                    startes=tuple(step.__starter_events.values())
                except:
                    startes=tuple()
                
                try:
                    #enders=tuple(functools.reduce(lambda x, y: x+y,  triggers.values()))
                    enders=triggers
                except:
                    enders=tuple()
                    
                # create end step
                end_step=evr.add_step(step.get_end_event_name(), recovery=container_recovery, releases=step.releases,
                                      config={'task_construct': Invoke, 'max_concurrent':1,}, triggers=enders)
                #                      config={'task_construct': Invoke, 'max_concurrent':1,}, triggers=enders)
                end_event=self.__eventor_events[step.get_end_event_name()]
                evr.add_assoc(end_event, end_step)
                
                #container=Container(ev=evr, step=step, progname=step.path, repeat=step.loop, iter_triggers=startes, end_triggers=enders)
                container=Container(ev=evr, step=step, progname=step.path, repeat=step.loop, iter_triggers=startes, 
                                    end_triggers={StepStatus.success:(end_event,), StepStatus.failure:(end_event,),})
                step.__container=container
                module_logger.debug("[ Step %s ] Set container" % (step.path, ))
                # create first step and event

                first_step=evr.add_step(step.get_start_event_name(), func=container, kwargs={'initial': True,}, recovery=container_recovery,
                                        acquires=step.acquires, config={'task_construct': Invoke, 'max_concurrent':1, 'sequence_arg_name': 'eventor_task_sequence',})
                steps[first_step.path]=first_step
                start_event=self.__eventor_events[step.get_start_event_name()]
                evr.add_assoc(start_event, first_step)
                if event_is_starter:
                    start_events.append(start_event)
                '''
                if self != step and step.is_container():
                    module_logger.debug('[ Step %s ] Steps: %s' %(step.path, step.__steps))
                    step.__create_eventor_steps(evr)
                '''
        
        module_logger.debug("[ Step %s ] Starter events: %s" % (self.path, start_events, ))        
        self.__eventor_steps=steps
        return start_events
    
    def create_flow(self, evr, trigger=True,):
        module_logger.debug("[ Step %s ] Creating flow (trigger: %s)" % (self.path, trigger))
        self.__create_eventor_events(evr)
        start_evensts=self.__create_eventor_steps(evr,)   
        if trigger:
            for trigger in start_evensts:
                module_logger.debug("[ Step %s ] Triggering event %s" % (self.path, trigger,))
                evr.trigger_event(trigger, '1')
        module_logger.debug('[ Step %s ] Flow: %s' % (self.path, repr(self)))  
        return start_evensts
             
    
