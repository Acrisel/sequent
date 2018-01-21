'''
Created on Oct 19, 2016

@author: arnon
'''
import logging
import os
from acris import MergedChainedDict, Sequence, Mediator
from .sequent_types import SequentError, LogocalOp
from .event import Event
from eventor import StepStatus, StepReplay #, Invoke
#from eventor.utils import decorate_all, print_method
import eventor
from collections.abc import Sequence as AbcSequence
from copy import deepcopy

mlogger = logging.getLogger(__name__)

import socket
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
    except OSError:
        address = 'localhost'
    else:
        address = s.getsockname()[0]
    s.close()
    return address


def get_hostname(full=False):
    ip = get_ip_address()
    if full == False:
        try:
            name = socket.gethostbyaddr(ip)[0]
        except:
            name = ip
    else:
        name = socket.getfqdn(ip)
    return name

DEFAULT_HOST = get_hostname()

def evaluate_status(enders_status):
    result = StepStatus.success
    for status in enders_status.values():
        if StepStatus[status.name] == StepStatus.failure:
            result = StepStatus.failure
    return result

class Container(object):
    ''' Representation for package task that incorporate one or more other tasks.
    '''
    
    class IterGen(object):
        def __init__(self, level):
            self.level = level
            
        def __call__(self):
            return (x for x in self.level)

    def __init__(self, step, progname, repeat=[1,], iter_triggers=(), end_triggers=(), app_config={}, logger=None):
        self.app_config = app_config
        self.progname = progname
        self.starters = iter_triggers
        self.enders = end_triggers
        if isinstance(repeat, AbcSequence):
            repeat = Container.IterGen(repeat)
        self.repeat = repeat
        self.loop_index = 0
        self.initiating_sequence = None
        self.step = step
        self.max_concurrent = self.step.config['max_concurrent']
        self.triggers = None
        self.__name__ = 'Container'
            
        
    def __call__(self, initial=False, eventor_task_sequence='', eventor=None, logger=None): 
        if initial:
            self.iter = Mediator(self.repeat())
            todos = 1
            self.initiating_sequence = eventor_task_sequence 
            self.loop_index = 0
            
            # eventor_task_sequence is parent sequence, take as is
            sequence = eventor_task_sequence
            logger.debug("[ Step {} ] Container setting sequence: {}.".format(self.progname, sequence, ))
        else:
            # this is child sequence - convert to parent
            sequence = str(eventor_task_sequence)
            parts = sequence.rpartition('.')
            sequence = parts[0] if parts[0] else parts[2]
            if sequence:
                todos, _ = eventor.count_todos_like("{}.%".format(sequence)) 
            else:
                todos, _ = eventor.count_todos() 
            logger.debug("[ Step {}/{} ] Container TODOs count {}: {}.".format(self.progname, sequence, repr(sequence), todos))
        
        # for sequential: if it is finished, it can check if there is another item to to.
        # TODO: for concurrent, need to check if max concurrent reached.  If not, activated another.
        # TODO: if resources are required, before starting, need to grab resource. 
        if todos <2 or initial:    
            logger.debug("[ Step {}/{} ] Container trying to get next sequence.".format(self.progname, eventor_task_sequence)) 
            try:
                item = next(self.iter)
            except StopIteration :
                logger.debug("[ Step {} ] Container received StopIteration ({}).".format(self.progname, self.loop_index,))
                item = None
            else:
                logger.debug("[ Step {} ] Container received NextIteration: {} ({}).".format(self.progname, repr(item), self.loop_index,))    
                
            if item is not None:
                # TODO - values need to specific to  task sequence
                #os.environ['SEQUENT_LOOP_VALUE']=str(item)
                self.loop_index += 1
                if str(sequence):
                    sequence = "{}." .format(sequence)
                else:
                    sequence = ''
                sequence = "{}{}".format(sequence, self.loop_index) 
                for trigger in self.step.start_evensts:
                    logger.debug("[ Step {} ] Container triggering starter {}/{}.".format(self.progname, repr(trigger), self.loop_index,))
                    eventor.remote_trigger_event(trigger, sequence,)
                #for trigger in self.starters:
                #    mlogger.debug("[ Step %s ] triggering starter: %s" % (self.progname, repr(trigger),))
                #    self.ev.remote_trigger_event(trigger, self.loop_index,)
            else:
                logger.debug("[ Step {} ] Container Enders: {}.".format(self.progname, list(self.step.ender_steps.keys()),))
                enders_status = eventor.get_task_status(self.step.ender_steps.keys(), self.loop_index)
                status = evaluate_status(enders_status)
                #self.ev.update_task()
                logger.debug("[ Step {} ] Container step status for triggering: {}".format(self.progname, status.name,))
                for trigger in self.enders[status]:
                    logger.debug("[ Step {} ] Container triggering ender: {}".format(self.progname, repr(trigger),))
                    eventor.remote_trigger_event(trigger, self.initiating_sequence,)
            
        return True


#class Step(metaclass=decorate_all(print_method(mlogger.debug))):
class Step(object):
    """A step in steps structure.  
       
        Each step has unique id that identifies it within Steps.
       
        A step is considered completed if it returns gradior.complete.
        step can also return gradior.failed or gradior.active.
       
        If step generate exception, it is considered gradior.FAILED.  The exception is
        also registered and could be referenced.
        
    """
    
    config_defaults = eventor.Eventor.config_defaults

    def __init__(self, parent=None, name=None, func=None, args=[], kwargs={}, config={}, requires=(), delay=0, acquires=[], releases=None, recovery={}, repeats=[1,], hosts=None, import_module=None, import_file=None, app_config={}):
        
        self.id = id
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.config = MergedChainedDict(config, os.environ, Step.config_defaults)
        self.parent = parent
        self.root_step = self if parent is None else parent if self.parent.root_step is None else self.parent.root_step
        self.require = requires
        self.delay = delay
        self.acquires = acquires
        self.releases = releases if releases is not None else acquires
        self.recovery = recovery
        self.repeats = repeats
        self.hosts = hosts if hosts is not None else []
        self.path = name 
        if self.parent and parent.path:
            self.path = '%s_%s' % (parent.path, name)
            
        if hosts:
            ancestry_hosts = self.check_ancestry_host()
            if ancestry_hosts is not None:
                raise SequentError("Step ancestry has already assigned host; step: {}; ancestor: {}; hosts: {}".format(self.path, ancestry_hosts.path, ancestry_hosts.hosts))
            
        if import_file is not None and import_module is None:
            raise SequentError("Import_file is provided but not import_module.")
        self.import_module = import_module
        self.import_file = import_file
        self.app_config = app_config
            
        self.__all_requires = dict()
        
        if requires is not None:
            for require in requires:
                self.__add_all_requires(require)
                #if len(event) > 1:
                #    req_step, state = event
                #    req_list=self.root_step.all_requires.get(req_step, list())
                #    self.root_step.all_requires[req_step]=req_list
                #    req_list=list(set(req_list.append(state)))
                
        
        #print('all_requires:', repr(self.root_step.all_requires))
            
        self.__sequence_next_step = Sequence("SequentNextStep")
        
        self.__steps = dict()
        self.steps = self.__steps
        self.__events = list()
        self.__container = None
        
    def check_ancestry_host(self,):
        result = None
        if self.parent is not None:
            if self.parent.hosts:
                result = self.parent
            elif self.parent.parent is not None:
                result = self.parent.check_ancestry_host()
        return result
        
    def __add_all_requires(self, require):
        if isinstance(require, tuple):
            if len(require) == 0: return
            elif require[0] == LogocalOp.or_:
                for r in require[1:]:
                    self.__add_all_requires(r)
                return
            elif len(require) == 2 and isinstance(require[0], Step):
                req_step, state = require
                req_list = self.root_step.__all_requires.get(req_step.path, list())
                self.root_step.__all_requires[req_step.path] = req_list
                if state != StepStatus.complete:
                    req_list.append(state)
                else:
                    req_list.extend([StepStatus.success, StepStatus.failure])
                req_list = list(set(req_list))
            else:
                for r in require:
                    self.__add_all_requires(r)
                #msg = "[ Step %s ] Bad require tuple: %s." % (self.path, str(require)) 
                #mlogger.debug(msg)
                #raise SequentError(msg)
        elif  isinstance(require, Event):
            self.__add_all_requires(require.require)
        else:
            msg = "[ Step {} ] Bad require: {}.".format(self.path, str(require)) 
            mlogger.debug(msg)
            raise SequentError(msg )
        
        
    def __repr__(self):
        return "Step( path({}), step({}),)".format(self.path, self.__steps)
    
    def __str__(self):
        return repr(self)
    
    def is_container(self):
        return len(self.__steps) >0
    
    def add_step(self, name=None, func=None, args=[], kwargs={}, requires=None, delay=0, acquires=[], releases=None, config={}, recovery={}, hosts=[], repeats=[1,], resources=[], import_module=None, import_file=None):
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
            requires: (iterator) list of require objects for this step to be activated.  object can be either 
                Event or tuple pair of (step, status)
            delay: seconds to delay execution of step after its requires are met.
            acquires: (iterator) list of resource requirements.  Each resource requirements is a tuple of 
                Resource type and amount.
            releases: (iterator) list of resource to release.  Each resource requirements is a tuple of 
                Resource type and amount. If not provided, defaults to acquires.
            config: parameters can include the following keys:
                - stop_on_exception=True 
            recovery: map step status to recovery option
            repeat: (iterator) list of value to repeat 
            
        """
         
        config = MergedChainedDict(config, os.environ, self.config)
        if repeats is None:
            repeats = list()     
        result = Step(parent=self, name=name, func=func, args=args, kwargs=kwargs, config=config, requires=requires,
                      delay=delay, acquires=acquires, releases=releases, recovery=recovery, repeats=repeats, hosts=hosts,
                      import_module=import_module, import_file=import_file, app_config=self.app_config)

        if name:
            step = self.__steps.get(result.path, None)
            if step:
                raise SequentError("Attempting to add step, but name already used: '{}'".format(name))
          
        
        self.__steps[result.path] = result

        return result

    def add_event(self, require):
        event = Event(require=require)
        return event
            
    def get_start_event_name(self,):
        return '{}_start'.format(self.path)
    
    def get_next_event_name(self, ):
        return '{}_next'.format(self.path)
    
    def get_complete_event_name(self, ):
        return '{}_complete'.format(self.path)
    
    def get_success_event_name(self, ):
        return '{}_success'.format(self.path)
    
    def get_end_event_name(self, ):
        return '{}_end'.format(self.path)
    
    def get_step_name(self, ):
        return self.path
    
    def update_step_triggers(self, trigger_map, status, event):
        try:
            triggers = trigger_map[status]
        except:
            triggers = list()
            trigger_map[status] = triggers
        triggers.append(event)

    def get_require_step_event(self, evr, step, status):
        #try:
        #    trigger_map=step.triggers
        #except:
        #    trigger_map=dict()
        #    step.triggers=trigger_map
           
        if status != StepStatus.complete:
            result = "{}_{}".format(step.path, status.name)
            event = evr.add_event(result)
            #step.update_step_triggers(trigger_map, status, event)
            mlogger.debug("[ Step {} ] Adding triggers: {} > {}".format(step.path, status, event)) 
        else:
            names = ["{}_{}".format(step.path, status.name) for status in [StepStatus.success, StepStatus.failure,]]
            result = "( " + " or ".join(names) + " )" 
            #for status, name in [(StepStatus.success), (StepStatus.failure)]:
            #    name=success="%s_%s" % (step.path, status.name)
            #    event=evr.add_event(name)
            #    #step.update_step_triggers(trigger_map, status, event)
            #    mlogger.debug("[ Step %s ] Adding triggers: %s > %s" % (step.path, status, event)) 
                              
        return result
        
    def convert_require(self, evr, require):
        #require=step.require
        items = list()
        for arg in require:
            mlogger.debug("Convert requires: {}({}).".format(type(arg).__name__, arg))
            if type(arg) == str:
                result = arg
            elif isinstance(arg, Event):
                result = self.convert_require(evr, arg.require)
            elif isinstance(arg, tuple):
                if len(arg) == 0:
                    result=''
                #elif len(arg) == 1:
                #    result= self.expr_to_str(*arg)
                elif arg[0] == LogocalOp.or_:
                    result = self.or_(evr, *arg[1:])
                elif len(arg) == 2 and isinstance(arg[0], Step):
                    self.__add_all_requires(arg)
                    result = self.get_require_step_event(evr, arg[0], arg[1])
                    # add to steps that are NOT enders
                    self.ender_steps[arg[0].path]=arg[0]
                else:    
                    list_expr = [self.convert_require(a) for a in arg]
                    result = "(" + ") and (".join(list_expr) +")" 
            else:
                raise SequentError("Unknown variable in require: {}".format(repr(arg)))
            items.append(result)
                
        expr = "(" + ") and (".join(items) + ")"
        return expr
        
    def or_(self, evr, *args):
        items = list()
        for arg in args:
            result = self.convert_require(evr, arg)
            items.append(result)
                
        expr = " or ".join(items)
        return expr
    
    def make_host_copy(self, step, host, index):
        copy_step = deepcopy(step)
        copy_step.name = "{}-{}".format(step.name, index)
        copy_step.path = "{}.{}".format(step.path, step.name)
        step.hosts = [host]
    
    def __hostesize(self, evr):
        ''' rebuilds steps based on hosts rebuild steps' path as appropriate.
        
        Algorithm:
            Run down step hierarchy.
            For each step that has hosts:
                if step is container step:
                    build sub-container step for each host. 
                    Use copy to replicate step into sub steps.
                    remove previous own steps. 
                    Update self with it new 'host level' sub-steps.
                    Update down stream steps with new path.
                else: # step is callable.
                    Use copy to replicate step for each host.
                    Update self with new 'host level' steps.
                    
        Args:
            evr: Eventor object that will be use to add hidden remote hosts
            
        '''
        # hostesize self first, which must be container
        if len(self.hosts) > 1:
            index = 0
            steps = dict()
            mlogger.debug('Split {} per host: {}'.format(self.path, self.hosts))
            for host in self.hosts:
                evr.add_remote(host)
                index += 1
                copy_step = self.make_host_copy(self, host, index)
                steps[copy_step.path] = copy_step
                mlogger.debug('New sub-step {} per host: {}'.format(self.path, self.hosts))
            self.__steps = steps
            self.hosts = [DEFAULT_HOST]
        else:
            # either you hove one or None; take it or parent respectively
            if not self.hosts:
                # try to get hosts from parent
                if self.parent:
                    if self.parent.hosts:
                        self.hosts = self.parent.hosts 
                if not self.hosts:
                    self.hosts = [DEFAULT_HOST]
            
        
        for step in list(self.__steps.values()):
            if len(step.__steps) > 0:
                # step is container
                step.__hostesize(evr)
            else:
                # step is operator
                if len(step.hosts) > 1:
                    step_path = step.path
                    index = 0
                    mlogger.debug('Split child step {} per host: {}'.format(step.path, step.hosts))
                    for host in step.hosts:
                        evr.add_remote(host)
                        copy_step = self.make_host_copy(step, host, index)
                        self.__steps[copy_step.path] = copy_step
                        mlogger.debug('New sub-step {} per host: {}'.format(step.path, step.hosts))
                    del self.__steps[step_path]
                else:
                    # either you hove one or None; take it or parent respectively
                    if not step.hosts:
                        step.hosts = self.hosts 
                    evr.add_remote(step.hosts[0])
                    mlogger.debug('Adopted host for {}: {}'.format(step.path, step.hosts))
                        
                        
    def __create_eventor_events(self, evr):
        events = dict()
        self.__starter_events = dict()
        #self.__starter_steps = dict()
        self.ender_steps = dict()
        
        todo = [self,]
        todo.extend(self.__steps.values())
        
        # convert require into event's expression and fill potential ender_steps
        for event in self.__events:
            expr = self.convert_require(evr, event.require)
            evr.add_event(expr)
            
        #print('self.root_step.__all_requires', repr(self.root_step.__all_requires))
        # dive into steps
        for step in todo:
            # skip self
            if self == step: continue
            
            if not step.require:
                event = evr.add_event(step.get_start_event_name())
                self.__starter_events[step.path] = event
                #self.__starter_steps[step.path] = step
            else:
                expr = self.convert_require(evr, step.require)
                event = evr.add_event(step.get_start_event_name(), expr=expr)
            events[event.id_] = event
            
            # Add success and failure events
            step.triggers = dict()
            statuses = [StepStatus.success, StepStatus.failure] 
            all_requires = self.root_step.__all_requires.get(step.path, [])     
            mlogger.debug("[ Step {} ] all_required: {}.".format(self.path, repr(all_requires)))          
            for status in statuses:
                event_name = "{}_{}".format(step.path, status.name)
                event = evr.add_event(event_name)
                events[event.id_] = event
                if status in all_requires or step.parent is None: 
                    #print('event:', event_name)
                    step.triggers.update({status: (event,)})
                
                
            # add end event for container steps
            if step.is_container():
                event_name = step.get_end_event_name()
                event = evr.add_event(event_name)
                step.triggers.update({status: (event,)})
                events[event.id_] = event
                      
        self.__eventor_events = events
        # since 'convert_requireed' filled ender_steps with those steps that can NOT be enders!!!!
        # so we remove to be left with enders only steps
        enders = list(set(self.__steps.keys()) - set(self.ender_steps.keys()))
        self.__ender_events = dict()
        self.ender_steps = dict()
        for step_path in enders:
            # if step.path not in self.__ender_steps.keys():
            step = self.__steps[step_path]
            success_event = step.get_success_event_name()
            event = evr.add_event(success_event)
            self.__ender_events[step_path] = event
            self.ender_steps[step_path] = step
            self.__eventor_events[success_event] = event
            
            # TODO(Arnon): clean up unneeded structures

        mlogger.debug("[ Step {} ] Starter and enders events\n    Starter: {}.\n    Ender: {}.".format(self.path, self.__starter_events, self.__ender_events))
            
    def __get_eventor_step_start_event(self, step):
        return self.__events[step.get_start_event_name()]
    
    def __get_eventor_step_next_event(self, step):
        return self.__events[step.get_next_event_name()]
    
    def __get_eventor_step_end_event(self, step):
        return self.__events[step.get_end_event_name()]
    
    def __create_eventor_steps(self, evr,):
        steps = dict()
        todo = list(self.__steps.values())
        
        start_events = list()
        
        container_recovery = {
            StepStatus.ready: StepReplay.rerun, 
            StepStatus.active: StepReplay.rerun, 
            StepStatus.failure: StepReplay.rerun, 
            StepStatus.success: StepReplay.rerun,
            StepStatus.allocate: StepReplay.rerun,
            StepStatus.fueled: StepReplay.rerun,
            }  

        step_ender_events = dict()
        for step in todo:
            try:
                triggers = step.triggers
            except:
                triggers = {}
            
            container = step.parent.__container
            #mlogger.debug("[ Step %s ] Found container of parent %s" %(step.path, step.parent.path))
            
            #mlogger.debug("[ Step %s ] Creating Eventor steps\n    Ender:%s\n    Triggers: %s" % (step.path,step.parent.__starter_steps, step.parent.ender_steps, triggers))                   
            mlogger.debug("[ Step {} ] Creating Eventor steps\n    Ender: {}\n    Triggers: {}".format(step.path, step.parent.ender_steps, triggers))                   
                
            step_is_ender = step.path in self.ender_steps.keys()
            event_is_starter = False if step.require else True
            
            # If it is ender step, and it is within super-step, it must trigger next.
            if step_is_ender and container is not None:
                parent = step.parent
                #next_id="%s_%s"% (parent.get_next_event_name(), parent.__sequence_next_step())
                next_id = parent.get_next_event_name()
                next_step = evr.add_step(next_id, func=container, kwargs={'initial': False,}, recovery=container_recovery, 
                                       config={'task_construct': 'invoke', 'max_concurrent':1, 'sequence_arg_name':'eventor_task_sequence', 'pass_logger_to_task': True})
                steps[next_step.path] = next_step
                next_event = evr.add_event(next_id)
                self.__eventor_events[next_id] = next_event
                #triggers = {StepStatus.complete: (next_event, ),}
                #mlogger.debug("[ Step %s ] Add ender trigger: %s" % (step.path, triggers)) 
                mlogger.debug("[ Step {} ] Add assoc to next step: {} {}".format(step.path, repr(next_event), repr(next_step))) 
                evr.add_assoc(next_event, next_step)
                mlogger.debug("[ Step {} ] Add trigger to success: {} {}".format(step.path, repr(next_event), repr(next_step))) 
                success_event_name = step.get_success_event_name()
                success_event = self.__eventor_events[success_event_name]
                triggers = {StepStatus.success: (success_event,),}
                
                enders = step_ender_events.get(parent, list())
                enders.append(success_event)
                step_ender_events[parent] = enders
                
            if not step.is_container():               
                # at this point, hosts is a single host     
                evr_step = evr.add_step(step.get_step_name(), func=step.func, args=step.args, kwargs=step.kwargs, 
                                      acquires=step.acquires, releases=step.releases, triggers=triggers, config=step.config, 
                                      import_module=step.import_module, import_file=step.import_file, host=step.hosts[0])
                steps[step.path] = evr_step
                start_event = self.__eventor_events[step.get_start_event_name()]
                evr.add_assoc(start_event, evr_step, delay=step.delay)
                if event_is_starter:
                    start_events.append(start_event)
            else:
                try:
                    startes = tuple(step.__starter_events.values())
                except:
                    startes = tuple()
                
                try:
                    #enders=tuple(functools.reduce(lambda x, y: x+y,  triggers.values()))
                    enders = triggers
                except:
                    enders = tuple()
                    
                # create end step
                end_step = evr.add_step(step.get_end_event_name(), recovery=container_recovery, releases=step.releases,
                                      config={'task_construct': 'invoke', 'max_concurrent':1, 'pass_logger_to_task': True}, triggers=enders)
                #                      config={'task_construct': Invoke, 'max_concurrent':1,}, triggers=enders)
                end_event = self.__eventor_events[step.get_end_event_name()]
                mlogger.debug("[ Step {} ] Add end event assoc: {} {}.".format(step.path, repr(end_event), repr(end_step)))
                evr.add_assoc(end_event, end_step)
                
                container = Container(step=step, progname=step.path, repeat=step.repeats, iter_triggers=startes, 
                                    end_triggers={StepStatus.success:(end_event,), StepStatus.failure:(end_event,),},
                                    app_config=self.app_config, logger=mlogger)
                step.__container = container
                mlogger.debug("[ Step {} ] Set container.".format(step.path, ))
                # create first step and event

                first_step = evr.add_step(step.get_start_event_name(), func=container, kwargs={'initial': True,}, recovery=container_recovery,
                                        acquires=step.acquires, config={'task_construct': 'invoke', 'max_concurrent':1, 'sequence_arg_name': 'eventor_task_sequence', 'pass_logger_to_task': True})
                steps[first_step.path] = first_step
                start_event = self.__eventor_events[step.get_start_event_name()]
                evr.add_assoc(start_event, first_step, delay=step.delay)
                if event_is_starter:
                    start_events.append(start_event)
                '''
                if self != step and step.is_container():
                    mlogger.debug('[ Step %s ] Steps: %s' %(step.path, step.__steps))
                    step.__create_eventor_steps(evr)
                '''
                step.start_evensts = step.create_flow(evr, trigger=False,)
                #step.start_evensts = step.__create_eventor_steps(evr,)  

        
        for parent, ender_events in step_ender_events.items():
            mlogger.debug("[ Step {} ] Adding ender expr to 'next' event: {}.".format(parent.path, repr(ender_events)))
            next_id = parent.get_next_event_name()
            next_event = self.__eventor_events[next_id]
            next_event.add_expr(ender_events)

        mlogger.debug("[ Step {} ] Starter events: {}.".format(self.path, start_events, ))        
        self.__eventor_steps = steps
        return start_events
    
    def create_flow(self, evr, trigger=True,):
        mlogger.debug("[ Step {} ] Creating flow (trigger: {}).".format(self.path, trigger))
        self.__hostesize(evr)
        self.__create_eventor_events(evr)
        start_evensts = self.__create_eventor_steps(evr,)   
        if trigger:
            for trigger in start_evensts:
                mlogger.debug("[ Step {} ] Triggering event {}.".format(self.path, trigger,))
                evr.trigger_event(trigger, '1')
        mlogger.debug('[ Step {} ] Flow: {}.'.format(self.path, repr(self)))  
        return start_evensts
             
    
