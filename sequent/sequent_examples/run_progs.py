'''
Created on Sep 12, 2017

@author: arnon
'''

import logging
import time
import os


class Step(object):
    '''
    Basic building block for sequent steps with precistency
    '''

    def __init__(self,):
        pass
    
    def __call__(self, *args, **kwargs):
        try:
            self.at_start(*args, **kwargs)
        except Exception:
            raise
        
        try:
            _status = self.main(*args, **kwargs)
        except Exception:
            raise
        
        try:
            self.at_end(*args, _status=_status, **kwargs)
        except Exception:
            raise
        
    def at_start(self, *args, **kwargs):
        pass
        
    def main(self, *args, **kwargs):
        pass
        
    def at_end(self, _status, *args, **kwargs):
        pass
    


def prog(progname, success=True,):
    logger = logging.getLogger(os.getenv("SEQUENT_LOGGER_NAME"))
    logger.info("doing what %s is doing." % progname)
    time.sleep(1)
    if not success:
        raise Exception("%s failed." % progname)
    return progname

