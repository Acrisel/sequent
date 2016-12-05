'''
Created on Oct 19, 2016

@author: arnon
'''
from inspect import isfunction
import logging
import threading
import os
from acris import MergedChainedDict, Sequence
import collections
from .sequent_types import SequentError, LogocalOp
from .event import Event
from eventor.eventor_types import StepStatus
from eventor.utils import decorate_all, print_method
import functools

module_logger=logging.getLogger(__name__)


class IterGen(object):
    def __init__(self, l):
        self.l=l
        
    def __call__(self):
        return (x for x in self.l)

class Container(object):
    def __init__(self, ev, progname, repeat=[1,], iter_triggers=(), end_triggers=()):
        module_logger.debug("[ step %s ] Container initialization\n    iter_triggers: %s\n    end_triggers: %s\n    repeat: %s" % (progname, iter_triggers, end_triggers, repeat) )
        self.ev=ev
        self.progname=progname
        self.starters=iter_triggers
        self.enders=end_triggers
        if isinstance(repeat, collections.Iterable):
            repeat=IterGen(repeat)
        self.repeat=repeat
        self.loop_index=0
        self.initiating_sequence=None
        
    def __call__(self, initial=False): 
        if initial:
            self.iter=self.repeat()
            todos=1
            self.initiating_sequence=self.ev.get_task_sequence()
        else:
            todos=self.ev.count_todos() 
        
        module_logger.debug("[ Step %s ] todos count: %s" % (self.progname, todos))
        if todos ==1 or initial:     
            try:
                item=next(self.iter)
            except StopIteration:
                item=None
                
            if item:
                os.environ['SEQUENT_LOOP_VALUE']=str(item)
                self.loop_index+=1
                for trigger in self.starters:
                    module_logger.debug("[ Step %s ] triggering starter: %s" % (self.progname, repr(trigger),))
                    self.ev.remote_trigger_event(trigger, self.loop_index,)
            else:
                for trigger in self.enders:
                    module_logger.debug("[ Step %s ] triggering ender: %s" % (self.progname, repr(trigger),))
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

    def __init__(self, parent=None, name=None, func=None, args=[], kwargs={}, config={}, require=(), recovery={}, repeat=[1,]):
        '''
        Constructor
        '''
        
        self.id=id
        self.func=func
        self.args=args
        self.kwargs=kwargs
        self.config=config
        self.parent=parent
        self.require=require
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
    
    def add_step(self, name=None, func=None, args=[], kwargs={}, require=None, config={}, recovery={}, repeat=[1,]):
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
                
            require: (iterator) list of require objects for this step to be activated.  object can be either Event
                or tuple pair of (step, status)

            config: parameters can include the following keys:
                - stop_on_exception=True 
                
            recovery: map step status to recovery option
                
            repeat: (iterator) list of value to repeat 
            
        """
         
        config=MergedChainedDict(config, os.environ, self.config)
        if repeat is None:
            repeat=list()        
        result=Step( parent=self, name=name, func=func, args=args, kwargs=kwargs, config=config, require=require, recovery=recovery, repeat=repeat)
        
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
        try:
            trigger_map=step.triggers
        except:
            trigger_map=dict()
            step.triggers=trigger_map
           
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
            elif type(arg) == tuple:
                if len(arg) == 0:
                    result=''
                elif len(arg) == 1:
                    result= self.expr_to_str(*arg)
                elif arg[0] == LogocalOp.or_:
                    result=self.or_(evr, *arg[1:])
                elif len(arg) == 2 and isinstance(arg[0], Step):
                    result=self.get_require_step_event(evr, arg[0], arg[1])
                    self.__ender_steps[arg[0].path]=arg[0]
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
        self.__ender_steps=dict()
        
        todo=[self,]
        todo.extend(self.__steps.values())
        
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
                for status in [StepStatus.success, StepStatus.failure,]:
                    event_name="%s_%s" % (step.path, status.name)
                    event=evr.add_event(event_name)
                    step.triggers.update({status: (event,)})
                
            if step.is_container():
                #event=evr.add_event(step.get_next_event_name())
                #events[event.id_]=event
                if step != self:
                    step.__create_eventor_events(evr)
                    
        self.__eventor_events=events
        enders=list(set(self.__steps.keys())-set(self.__ender_steps.keys()))
        self.__ender_events=dict()
        self.__ender_steps=dict()
        for step_path in enders:
            #if step.path not in self.__ender_steps.keys():
            step=self.__steps[step_path]
            event=evr.add_event(step.get_complete_event_name())
            self.__ender_events[step_path]=event
            self.__ender_steps[step_path]=step

        module_logger.debug("[ Step %s ] Starter and enders events\n    Starter: %s\n    Ender:%s" % (self.path, self.__starter_events, self.__ender_events))
            
            
    def __get_eventor_step_start_event(self, step):
        return self.__events[step.get_start_event_name()]
    
    def __get_eventor_step_next_event(self, step):
        return self.__events[step.get_next_event_name()]
    
    def __create_eventor_steps(self, evr):
        steps=dict()
        todo=list(self.__steps.values())
                
        for step in todo:
            try:
                triggers=step.triggers
            except:
                triggers={}
            
            container=step.parent.__container
            #module_logger.debug("[ Step %s ] Found container of parent %s" %(step.path, step.parent.path))
            
            module_logger.debug("[ Step %s ] Creating Eventor steps\n    Starter: %s\n    Ender:%s\n    Triggers: %s" % (step.path,step.parent.__starter_steps, step.parent.__ender_steps, triggers))                   
                
            step_is_ender=step.path in self.__ender_steps.keys()
            
            if step_is_ender and container is not None:
                parent=step.parent
                next_id="%s_%s"% (parent.get_next_event_name(), parent.__sequence_next_step())
                next_step=evr.add_step(next_id, func=container, config={'task_construct': threading.Thread})
                steps[next_step.path]=next_step
                next_event=evr.add_event(next_id)
                triggers={StepStatus.complete : (next_event, ),}
                module_logger.debug("[ Step %s ] Add triggers: %s" % (step.path, triggers)) 
                evr.add_assoc(next_event, next_step)
            
            if not step.is_container():                    
                evr_step=evr.add_step(step.get_step_name(), func=step.func, args=step.args, kwargs=step.kwargs, triggers=triggers, config=step.config)
                steps[step.path]=evr_step
                start_event=self.__eventor_events[step.get_start_event_name()]
                evr.add_assoc(start_event, evr_step)
            else:
                try:
                    startes=tuple(step.__starter_events.values())
                except:
                    startes=tuple()
                
                try:
                    enders=tuple(functools.reduce(lambda x, y: x+y,  triggers.values()))
                except:
                    enders=tuple()
                container=Container(ev=evr, progname=step.path, repeat=step.loop, iter_triggers=startes, end_triggers=enders)
                step.__container=container
                module_logger.debug("[ Step %s ] Set container" % (step.path, ))
                # create first step and event
                first_step=evr.add_step(step.get_start_event_name(), func=container, 
                                        kwargs={'initial': True}, config={'task_construct': threading.Thread})
                steps[first_step.path]=first_step
                start_event=self.__eventor_events[step.get_start_event_name()]
                evr.add_assoc(start_event, first_step)

                if self != step and step.is_container():
                    module_logger.debug('[ Step %s ] Steps: %s' %(step.path, step.__steps))
                    step.__create_eventor_steps(evr)
                
        self.__eventor_steps=steps
        return start_event
    
    def create_flow(self, evr):
        self.__create_eventor_events(evr)
        start_event=self.__create_eventor_steps(evr)   
        evr.trigger_event(start_event)
        #print('start event', repr(start_event))       
    
