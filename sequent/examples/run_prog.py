'''
Created on Sep 9, 2017

@author: arnon
'''

import logging
logger = logging.getLogger(__name__)
import time

def prog(flow, progname, success=True,):
    
    logger.info("doing what %s is doing" % progname)
    time.sleep(1)
    if not success:
        raise Exception("%s failed" % progname)
    return progname
