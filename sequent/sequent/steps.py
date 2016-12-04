# -*- encoding: utf-8 -*-
##############################################################################
#
#    Acrisel LTD
#    Copyright (C) 2008- Acrisel (acrisel.com) . All Rights Reserved
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
"""

About
=========
:synopsis:     framework that ease the build and operate
:moduleauthor: Arnon Sela
:date:         Oct 18, 2016
:description:  Steps class is the entry point to the features of gradior.
   

Artifacts:
-------------------
As part of using this module the following artifacts may be created.
1. <program>.run: file containing information about the last execution of program 

Dependencies:
-------------------
None.
      
**History:**
-------------------

:Author: Arnon Sela
:Modification:
   - Initial entry
:Date: 2016-10-18

   
"""

from collections import OrderedDict, ChainMap
import logging
import os
import pprint
import multiprocessing as mp
import time
import inspect
import sys

from sequent import start_logger, stop_logger
from sequent import Step
#import gradior.dbapi as db # create_db, add_step
from sequent import LoopEvent #, step_loop, 
from sequent import LoopTask
from sequent import StepsError, AssocType, LoopControl
from sequent import StepBase, db
from sequent import Event

from sequent_types import Start

module_logger=logging.getLogger(__name__)

module_runner_file = None



interactive=False
try:
    if sys.ps1: interpreter = True
except AttributeError:
    interpreter = False
    if sys.flags.interactive: interpreter = True
       
       
    
defaults={'start': Start.resume, 
          'workdir':'/tmp', 
          'logdir': '/tmp', 
          'task_construct': mp.Process, 
          'max_parallel': -1, 
          'stop_on_exception': True,
          'sleep_between_iterations': 1,
          }    
#StepsElement = namedtuple('StepsElement', ['step', 'require']) 

#Step = namedtuple( 'Step', ['name', 'path', 'is_stepss', 'func', 'func_args', 'func_kwargs', 'config', 'require'])   

ActiveProps=namedlist('ActiveProps', ['loop', 'sequence'])

        
class Steps(StepBase):
    """Steps manages program steps.  
       
        Each program step is self contained.  It may use as inputs, data artifacts 
        from previous steps.  It usually creates data artifacts for downstream steps.
       
        A step is considered completed if it returns gradior.COMPLETE.
        step can also return gradior.FAILED or gradior.SUSPENDED.
       
        If step generate exception, it is considered gradior.FAILED.  The exception is
        also registered and could be referenced.
        
        :func:__init__()
              :param start: instruct Steps how to start (resume, restart)
              :param workdir: path to folder where 
              :type start: Start enumerator value
              :type workdir: type description
              :return: Steps object
              :rtype: Steps
         
        :func:add_step()
              :param start: instruct Steps how to start (resume, restart)
              :param workdir: path to folder where 
              :type start: Start enumerator value
              :type workdir: type description
              :return: Steps object
              :rtype: Steps
         
        :func:add_require()
              :param start: instruct Steps how to start (resume, restart)
              :param workdir: path to folder where 
              :type start: Start enumerator value
              :type workdir: type description
              :return: Steps object
              :rtype: Steps
         
        :func:__call__() 
              :return: Steps object
              :rtype: Steps    
    
        :Example:
    
              followed by a blank line !
    
          which appears as follow:
    
          :Example:
    
          followed by a blank line
    
        - Finally special sections such as **See Also**, **Warnings**, **Notes**
          use the sphinx syntax (*paragraph directives*)::
    
              .. seealso:: blabla
              .. warnings also:: blabla
              .. note:: blabla
              .. todo:: blabla
    
        .. note::
            There are many other Info fields but they may be redundant:
                * param, parameter, arg, argument, key, keyword: Description of a
                  parameter.
                * type: Type of a parameter.
                * raises, raise, except, exception: That (and when) a specific
                  exception is raised.
                * var, ivar, cvar: Description of a variable.
                * returns, return: Description of the return value.
                * rtype: Return type.
    
        .. note::
            There are many other directives such as versionadded, versionchanged,
            rubric, centered, ... See the sphinx documentation for more details.
    
        Here below is the results of the :func:`function1` docstring.
    
    """
    
    # holds Step(s) composing this object; 
    # this is done in the class level
    # 
    #all_events=dict()
    
    #depth=0
    
    def __init__(self, name=None, func_args=[], func_kwargs={}, config={}, require=None, loop=[1,]):
        """initializes steps object
        
            config parameters can include the following keys:
                - start= Start.resume, 
                - workdir='/tmp', 
                - logdir='/tmp', 
                - stop_on_exception=True
                
            func_args would be passed to sub-steps as is, unless overridden by its relative add_step.
            
            func_kwargs would be passed to sub=steps after ChainMap allowing hierarchical override 
        
            :param name: the first value
            :param config: the first value
            :param func_args: substep argument list
            :param func_kwargs: substep key words map
            :type name: str
            :type config: dict
            :type func_args: list
            :type func_kwargs: dict
            :returns:  Steps meta structure that holds steps
            :rtype: Steps
        
        """
        self.config = ChainMap(config, os.environ, defaults) 
        
        self.sleep_loop=self.config['sleep_between_iterations']
        self.requiries=list() # holds these Step(s) that are required by others.
        self.eloop=None
        
        # TODO: remove the need for these queues
        self.event_loop_q=mp.Queue()
        self.task_loop_q=mp.Queue()
        
        self.controlq=mp.Queue()
        self.func_args=func_args
        self.func_kwargs=func_kwargs
        self.path=None 
        self.sequence=-1
        self.parent=None
        self.root=None
        #self.step_op=dict()
        
        # initial setup for depth; when running
        # prepare steps would fill in right depth
        self.depth=0
        
        #if not isinstance(loop, types.GeneratorType):
        #    loop=(x for x in loop)
        self.loop=loop
            
        if require:
            self.event=Event(require)
        else:
            self.event=None
        
        self.steps=OrderedDict() 
        
        self.all_steps=None
        
        super().__init__(name=name)
        
        start_logger(logging_level=logging.DEBUG)
        
    def __repr__(self):
        steps=', '.join([ repr(step) for step in self.steps.values()])
        result="Steps( name( {} ), {}, steps( {} )  )".format(self.path, self.event, steps)
        return result
        
    def __str__(self):
        steps='\n    '.join([ str(step) for step in self.steps.values()])
        result="Steps( name( {} )\n    {}\n    steps( \n    {}\n   )  )".format(self.path, self.event, steps)
        #result="Steps( name({})\n    require({}))".format(self.path, self.require)
        #for step in self.steps.values():
        #    result += '\n %s' % step.path
        return result
        
    def add_step(self, name=None, func=None, func_args=[], func_kwargs={}, require=None, config={}, loop=None):
        """add a step to steps object
        
            config parameters can include the following keys:
                - stop_on_exception=True
                
            func_args, replacing super-step args.  
                If None, super-step args will be used.  
                Otherwise, this will be used
            
            func_kwargs, overriding super-step kwargs.
                If None, None will be used
                Otherwise, override super-step with this.
        
            :param name: the first value
            :param config: the first value
            :param func_args: substep argument list
            :param func_kwargs: substep key words map
            :type name: str
            :type config: dict
            :type func_args: list
            :type func_kwargs: dict
            :returns:  Steps meta structure that holds steps
            :rtype: Steps
        
        """
         
        config = ChainMap(config, os.environ, self.config)
        
        # If None, super-step args will be used.  
        # Otherwise, this will be used
        if func_args is None:
            func_args=self.func_args
        
        # If None, None will be used
        # Otherwise, override super-step with this.
        if func_kwargs is not None:
            func_kwargs = ChainMap(func_kwargs, self.func_kwargs)
        else:
            func_kwargs=self.func_args
        
        if name:
            if self.steps.get(name):
                raise grd.StepsError("Attempting to add step, but name already used: '%s'" % (name))
          
        try:
            is_steps=isinstance(func, Steps) 
        except:
            is_steps=False
        
        self_require=(self, 'active')
        if require:
            require=('and', self_require, require)    
        else:
            require=self_require
        
        event=self.add_event(require)
        #print('new event: %s: %s' % (event.event_id, repr(event.structured_require)))
        if not is_steps:
            if loop:
                raise grd.StepsError("loop argument provided, but object is not Steps: '%s'" % (name))
            result=Step( name=name, is_steps=is_steps, func=func, func_args=func_args, 
                         func_kwargs=func_kwargs, config=config, event=event, ) 
        else:
            # this is Steps, just update its parameters.
            # when address, its __call__ will be 
            result=func
            result.event=event
            result.func_args=func_args
            result.func_kwargs=func_kwargs
            result.config=config
            result.is_steps=is_steps
            if loop is not None:
                #if not isinstance(loop, types.GeneratorType):
                #    loop=(x for x in loop)
                result.loop=loop
        
        # set parent 
        result.parent=self
                
        self.steps[result.step_id]=result
        #self.all_steps[result.step_id]=result
        
        return result
    
    def add_event(self, require):
        """add an event to steps object
        
            :param require: tuple of required event triggers
            :type require: tuple
            :returns:  created event
            :rtype: Event
        
        """
        event=Event(require=require)
        return event
    
    def __get_gen(self):
        if hasattr(self.loop, '__iter__'):
            result=(x for x in self.loop)
        elif inspect.isfunction(self.loop): 
            result=self.loop()
        return result
    
    def __activate_next(self, seq_path, from_parent):
        added=False
        try:
            props=self.root.active_props[seq_path]
        except KeyError:
            # this is the first time this is called
            genfunc=self.__get_gen()
            props=ActiveProps(loop=genfunc, sequence=0)
            self.root.active_props[seq_path]=props
        else:
            genfunc=props.loop 
            
        try:
            loop_value=next(genfunc)
        except StopIteration:
            loop_value=None
        else:
            self.loop_value = loop_value
            props.sequence+=1
            new_seq_path=self._set_iter_path(seq_path=seq_path, sequence=props.sequence)
            trigger=Event( require=(self, grd.TaskStatus.active.name) )
            added=Event.trigger_event( db, trigger, new_seq_path)
            #db.commit_db()
        return added
    
    def __controller(self, seq_path=''):
        ''' governs execution of steps  
        
        When any step in Steps is completed, that Steps controller is triggered.
        Controller scans tasks of same sequence.
        If there is no task that is active, and there is no trigger, 
        Next sequence would be triggered.
        
        If there is no next sequence, task is complete and proper event would be triggered. 
        
        Example Scenario: A ( B ( C ) )
        A: single iteration
        B: double iterations
        
        Run    Trigger        Task
        ---    -------        ----
        A      A/1/Active     B/1
        B/1    B/1,1/Active   C/1,1
        C/1,1  C/1,1/Complete B/1,1
        B/1,1  B/1,2/Active   C/1,2
        C/1,2  C/1,2/Complete B/1,2
        B/1,2  B/1,2/Complete A/1,2
        A/1,2  A/1,2 Complete
        
        '''
                        
        move_to_next=True
        # TODO: first check that it is time to move to next sequence
        # set move_to_next to false in case not ready yet
        
        # We here because parent Steps became active or child step(s) is done 
        from_parent=True
        if seq_path:
            seq_path_parts=seq_path.split('.')
            from_parent=len(seq_path_parts) < self.depth
            if self.depth > 0:
                seq_path='.'.join(seq_path_parts[:self.depth])
            else:
                seq_path='' 
        
        # when time to next sequence
        # if not, nothing to do
        added=False
        if move_to_next:
            added=self.__activate_next(seq_path=seq_path, from_parent=from_parent)
            
        return added
                                                
    def __set_module_runner_file(self, calling_module, start):
        global module_runner_file
        parts=calling_module.rpartition('.')
        if parts[0]:
            if parts[2] == 'py':
                module_runner_file=parts[0]
            else:
                module_runner_file=calling_module
        else:
            module_runner_file=parts[2]
        module_runner_file='.'.join([module_runner_file, 'run.db'])  
        
        self.__runfile=module_runner_file
        
    def __create_db(self, runner_file=None, ):
        global db
        global module_runner_file       
           
        if runner_file is not None:
            module_runner_file=runner_file
        elif module_runner_file is None:
            module_runner_file=self.__get_runner_file() 
            
        module_logger.info("STEPS - Runner file: %s" % (module_runner_file,)) 
        
        db.open(module_runner_file)            
        try:
            db.create_db(module_runner_file)
        except Exception:
            raise
        
    def __join_loop(self, ):     
        for loop in [self.eloop, self.tloop]:
            if loop:
                loop.join()     
    
    def __set_path(self, super_name):
        if super_name:
            self.path="%s.%s" % (super_name, self.name) 
        else:
            self.path=self.name

    #def __add_path(self, super_name=''):
    #    #print('__add_path [%s] [%s]' % (super_name, self.name))
    #    self.__set_path(super_name)
    #    
    #    for step in self.steps.values():
    #        #print(self.path, isinstance(step, Step))
    #        if isinstance(step, Step):
    #            # step is Step, hence no derivatives, just fix its path
    #            step.path="%s.%s" % (self.path, step.name)
    #        else:
    #            # step is Steps, handle is as self is.
    #            step.__add_path(super_name=self.path)
                
    def __prepare_steps(self, all_steps, depth, super_name='',):
        # Since original name is in the context of its immediate super-step
        # Need to adjust name to include full path to prevent name
        #
        #self.processed_require=self.__require_restructured(self.require) 
        self.__set_path(super_name)
        all_steps.update(self.steps)
        
        self.depth=depth 
        if depth != 0:
            self.root = self.parent.root
        
        for step in self.steps.values():
            if not isinstance(step, Steps):
                # step is Step, hence no derivatives, just fix its path
                step.path="%s.%s" % (self.path, step.name)
            else:
                # step is Steps, handle is as self is.
                step.__set_path(super_name=self.path) 
                step.__prepare_steps(all_steps, depth+1, super_name)  
                        
    
    def write(self,):
        """writes runner representation into runner_file
        
            write creates sqlite representation of the program.  
        
            :param runner_file: path to file
            :type runner_file: str
            :returns: N/A
            :rtype: N/A
        """
            
        #if create:
        #    self.__create_db(runner_file) 
                                        
        db.add_step(step_id=self.step_id, name=self.path)
        
        # If depth is 0 - this is the top guy, no need to analyze require.
        if self.event is not None:
            self._add_assoc()
            
        for step in self.steps.values():
            step.write()

        db.commit_db()

    def __start_loop(self, continuous_loop=False,):
        ''' Initiate loops over triggers to produce action.
        
        Events
        /- while active
        |  |- execute event loop
        |  |- execute step loop
                
        '''
              
        module_logger.debug('STEPS - Starting event loop, continuous: {}'.format(continuous_loop))
        self.__eloop=LoopEvent(runfile=self.__runfile, continuous_loop=continuous_loop, controlq=self.event_loop_q,) # construct=self.config['construct'])
        self.__eloop.start()
        
        self.__tloop=LoopTask(runfile=self.__runfile, continuous_loop=continuous_loop, max_parallel=self.config['max_parallel'],
                            task_construct=self.config['task_construct'], steps=self.all_steps, controlq=self.task_loop_q,)
        self.__tloop.start()
        
    def __check_control(self):
        result=None
        if not self.controlq.empty():
            result=self.controlq.get()        
            if result:
                self.loop=result not in [LoopControl.stop]
                self.act=result in [LoopControl.start]

    def __run_loops(self, continuous_loop=False):
        module_logger.debug('STEPS - Starting processing loops, continuous: {}'.format(continuous_loop))
        eloop=LoopEvent(runfile=self.__runfile, continuous_loop=continuous_loop,)
        tloop=LoopTask(runfile=self.__runfile, continuous_loop=continuous_loop, max_parallel=self.config['max_parallel'],
                            task_construct=self.config['task_construct'], steps=self.all_steps,)
        
        self.loop=True
        while self.loop:
            event_seqs, step_seqs =  eloop.loop_event_iteration(db)
            path_seqs=tloop.loop_task_iteration(db)
                                            
            if continuous_loop:   
                self.__check_control()
                if self.loop:
                    time.sleep(self.sleep_loop)
                    self.__check_control()
            else:
                self.loop=False
            
        return True

    def __join_loops(self):
        if self.__eloop:
            self.__eloop.join()
        if self.__tloop:
            self.__tloop.join()
            
    def __initiate_root_step(self, start): 
        self.all_steps=dict()     
        #self.depth=1
        frame_records = inspect.stack()[2]
        calling_module = frame_records.filename
        self.root=self
        # TODO: change to that all Steps points to root Steps.  No need to pass all_steps when that is accomplished.
        self.__prepare_steps(self.all_steps, depth=self.depth)
        Event.prepare_events()
        #print(str(self))
        #exit()
        self.__set_module_runner_file(calling_module, start)
        
        self.all_steps[self.step_id]=self
        self.active_props=dict()
        
        if start == Start.restart:
            try:
                os.remove(module_runner_file)
            except FileNotFoundError:
                pass
            
            self.__create_db(module_runner_file) 
            Event.write_events(db)
            self.write()
        else:
            # TODO:  needs to read DB and resume
            pass
        
            
    def __call__(self, ):
        """runs Steps algorithm
        
            If top of the hierarchy:
                    Create DB on restart (including program structure)
                    Read DB on resume
                    start two managing threads - task and event managers
                    
            Trigger event (self, running)
            
            Wait for managing threads to finish
        
            Args:
                start: (sequent.Start) instruct 
                
        """
        global module_runner_file
        
        if self.depth == 0 and seq_path is None:
            self.__initiate_root_step(start)  
                     
        added=self.__controller(seq_path)  
                 
        if self.depth == 0 and seq_path is None and added:        
            #self.__start_loop(continuous_loop=True,) 
            #self.__join_loops()
            self.__run_loops(continuous_loop=True,) 