'''
Created on Oct 31, 2016

@author: arnon
'''

from .sequent_types import SequentError
import logging
from acris import Sequence

module_logger=logging.getLogger(__name__)

class Event(object):
    
    event_sequence=Sequence('SequentEvent')
    
    def __init__(self, require ):
        self.require=require
        self.id=Event.event_sequence()
