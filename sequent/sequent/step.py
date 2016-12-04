'''
Created on Oct 19, 2016

@author: arnon
'''
from inspect import isfunction
import logging
import threading
import os
from acris import MergedChainedDict
import collections
from .sequent_types import SequentError, LogocalOp
from .event import Event
from eventor.eventor_types import StepStatus

module_logger=logging.getLogger(__name__)


class IterGen(object):
    def __init__(self, l):
        self.l=l
        
    def __call__(self):
        return (x for x in self.l)

class Container(object):
    def __init__(self, ev, progname, loop=[1,], iter_triggers=(), end_triggers=()):
        self.ev=ev
        self.progname=progname
        self.starters=iter_triggers
        self.enders=end_triggers
        if isinstance(loop, collections.Iterable):
            loop=IterGen(loop)
        self.loop=loop
        self.loop_index=0
        
    def __call__(self, initial=False): 
        todos=True
        if initial:
            self.iter=self.loop()
        else:
            todos=self.ev.count_todos() 
        
        module_logger.debug("todos count: %s" % todos)
        if todos >1 or initial:     
            try:
                item=next(self.iter)
            except StopIteration:
                item=None
            if item:
                self.loop_index+=1
                for trigger in self.starters:
                    module_logger.debug("triggering: %s" % (repr(trigger),))
                    self.ev.remote_trigger_event(trigger, self.loop_index,)
            else:
                for trigger in self.enders:
                    self.ev.remote_trigger_event(trigger, self.loop_index,)
            
        return True


class Step(object):
    """A step in steps structure.  
       
        Each step has unique id that identifies it within Steps.
       
        A step is considered completed if it returns gradior.complete.
        step can also return gradior.failed or gradior.active.
       
        If step generate exception, it is considered gradior.FAILED.  The exception is
        also registered and could be referenced.
        
    """

    def __init__(self, parent=None, name=None, func=None, args=[], kwargs={}, config={}, require=(), recovery={}, loop=[1,]):
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
        self.loop=loop
        self.path=name 
        if self.parent and parent.path:
            self.path='%s_%s' % (parent.path, name)
        
        self.__steps=dict()
        self.__events=list()
        
    def __repr__(self):
        if hasattr(self.func, '__name__'):
            oname=self.func.__name__
        else:
            oname=self.func.__class__.__name__
            
        return "Step( path(%s), step(%s),)" % (self.path, self.__steps)
    
    def __str__(self):
        return repr(self)
    
    def is_container(self):
        return len(self.__steps) >0
    
    def add_step(self, name=None, func=None, args=[], kwargs={}, require=None, config={}, recovery={}, loop=None):
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
                
            loop: (iterator) list of value to loop 
            
        """
         
        config=MergedChainedDict(config, os.environ, self.config)
                
        result=Step( parent=self, name=name, func=func, args=args, kwargs=kwargs, config=config, require=require, recovery=recovery, loop=loop)
        
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
            self.update_step_triggers(trigger_map, status, event)
        else:
            success="%s_%s" % (step.path, StepStatus.success.name)
            faiulre="%s_%s" % (step.path, StepStatus.failure.name)
            result= "( %s or %s )" %( success, faiulre) 
            event_success=evr.add_event(success)
            event_failure=evr.add_event(faiulre)
            self.update_step_triggers(trigger_map, StepStatus.success, event_success)
            self.update_step_triggers(trigger_map, StepStatus.failure, event_failure)
               
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
                else:
                    expr=self.convert_require(evr, step.require)
                    event=evr.add_event(step.get_start_event_name(), expr=expr)
                events[event.id_]=event
                
            if step.is_container():
                event=evr.add_event(step.get_next_event_name())
                events[event.id_]=event
                if step != self:
                    step.__create_eventor_events(evr)
        self.__eventor_events=events
        self.__enders_events=list()
        for step in self.__ender_steps.values():
            event=evr.add_event(step.get_complete_event_name())
            self.__enders_events.append(event)
            
            
    def __get_eventor_step_start_event(self, step):
        return self.__events[step.get_start_event_name()]
    
    def __get_eventor_step_next_event(self, step):
        return self.__events[step.get_next_event_name()]
    
    def __create_eventor_steps(self, evr):
        steps=dict()
        todo=list(self.__steps.values())
        #if self.path and self.path not in self.__steps.keys():
        #    print(self.path, list(self.__steps.keys()))
        #    todo=[self, ]+todo
        #    print(len(todo))
        
        for step in todo:
            try:
                triggers=step.triggers
            except:
                triggers={}
                    
            if not step.is_container():
                # self, parent=None, name=None, func=None, args=[], kwargs={}, config={}, require=(), loop=[1,]
                # args=(), kwargs={}, triggers={}, recovery={}, config={}
                evr_step=evr.add_step(step.get_step_name(), func=step.func, args=step.args, kwargs=step.kwargs, triggers=triggers, config=step.config)
                steps[step.path]=evr_step
                start_event=self.__eventor_events[step.get_start_event_name()]
                evr.add_assoc(start_event, evr_step)
            else:
                try:
                    startes=tuple(step.__starter_events.values())
                except:
                    startes=tuple()
                container=Container(ev=evr, progname=step.path, loop=step.loop, iter_triggers=startes, )
                first_step=evr.add_step(step.get_start_event_name(), func=container, 
                                        kwargs={'initial': True}, config={'task_construct': threading.Thread})
                next_step=evr.add_step(step.get_next_event_name(), func=container, 
                                       config={'task_construct': threading.Thread})
                steps[first_step.path]=first_step
                steps[next_step.path]=next_step
                start_event=self.__eventor_events[step.get_start_event_name()]
                evr.add_assoc(start_event, first_step)
                evr.add_assoc(self.__eventor_events[step.get_next_event_name()], next_step)
                if self != step:
                    step.__create_eventor_steps(evr)
                
        self.__eventor_steps=steps
        return start_event
    
    def create_flow(self, evr):
        self.__create_eventor_events(evr)
        start_event=self.__create_eventor_steps(evr)   
        evr.trigger_event(start_event)
        #print('start event', repr(start_event))       
    
