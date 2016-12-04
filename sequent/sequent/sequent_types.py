'''
Created on Dec 1, 2016

@author: arnon
'''

from eventor import StepStatus
from eventor import RunMode, StepReplay
from enum import Enum

class SequentError(Exception):
    pass

class Start(Enum):
    resume=1
    restart=2
    
class LogocalOp(Enum):
    or_=1
    and_=2
    