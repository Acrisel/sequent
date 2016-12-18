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

import eventor
import logging 

from .step import Step
from .sequent_types import RunMode

module_logger=logging.getLogger(__name__)

module_logger.setLevel(logging.DEBUG)

#class Sequent(Step):
class Sequent(object):
    
    #def __init__(self, name='', store='', run_mode=RunMode.restart, recovery_run=None, dedicated_logging=False, logging_level=logging.INFO, config={},):
    def __init__(self, name='', store='', *args, **kwargs):
        """initializes step object            
        """
        
        self.args=args
        self.kwargs=kwargs
        #self.repeat=repeat
        #super().__init__(name=name, args=args, kwargs=kwargs)
        self.root_step=Step(name=name,)
        calling_module=eventor.calling_module()
        self.store=store if store else eventor.store_from_module(calling_module)
        #self.__steps=self.steps
                
    def __repr__(self):
        return Step.__repr__(self)
    
    def add_step(self, name=None, func=None, args=[], kwargs={}, require=None, acquires=[], releases=None, config={}, recovery=None, repeat=[1,]):
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
                
            repeat: (iterator) list of value to repeat 
            
        """
        
        #step=Step.add_step(self, name=name, func=func, args=args, kwargs=kwargs, require=require, config=config, recovery=recovery, repeat=repeat) 
        step=self.root_step.add_step(name=name, func=func, args=args, kwargs=kwargs, require=require, acquires=acquires, releases=releases, config=config, recovery=recovery, repeat=repeat)
        return step
    
    def add_event(self, require):
        #event=Event(require=require)
        #self.__events.append(event)
        event=self.root_step.add_event(require)
        return event
    
    def get_step_sequence(self):
        if self.evr:
            return self.evr.get_step_sequence()
    
    def get_step_name(self):
        if self.evr:
            return self.evr.get_step_name()
    
    def __call__(self):
        
        self.evr=eventor.Eventor(*self.args, name=self.root_step.path, store=self.store, **self.kwargs)
        #for step in self.__steps.values():
        #    step.create_flow(evr)
        self.root_step.create_flow(self.evr)
        result=self.evr()
        return result
        