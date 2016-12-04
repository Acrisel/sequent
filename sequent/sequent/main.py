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

import os
from acris import MergedChainedDict
import eventor
import inspect

from .sequent_types import SequentError, StepStatus
from .step import Step
from .event import Event

class Sequent(Step):
    
    def __init__(self, name='', store='', *args, **kwargs):
        """initializes step object            
        """
        
        self.args=args
        self.kwargs=kwargs
        Step.__init__(self, name=name, args=args, kwargs=kwargs)
        calling_module=eventor.calling_module()
        self.store=store if store else eventor.store_from_module(calling_module)
                
    def __repr__(self):
        return Step.__repr__(self)
    
    def add_step(self, name=None, func=None, args=[], kwargs={}, require=None, config={}, recovery=None, loop=None):
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
                
            loop: (iterator) list of value to loop 
            
        """
        
        result=Step.add_step(self, name=name, func=func, args=args, kwargs=kwargs, require=require, config=config, recovery=recovery, loop=loop) 
        return result
    
    def add_event(self, require):
        event=Event(require=require)
        self.__events.append(event)
        return event
    
    def __call__(self):
        evr=eventor.Eventor(*self.args, name=self.path, store=self.store, **self.kwargs)
        self.create_flow(evr)
        result=evr()
        return result
        