
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

import sequent as seq
import eventor as evr
import logging
import math

logger=logging.getLogger(__name__)

logger.setLevel(logging.DEBUG)

def square(x):
    y=x*x
    return y

def square_root(x):
    y=math.sqrt(x)
    return y

def divide(x,y):
    z=x/y
    return z

def build_flow(run_mode=evr.RunMode.restart, param=9):
    myflow=seq.Sequent(logging_level=logging.DEBUG, run_mode=run_mode, config={'sleep_between_loops': 0.05,})
    
    s0 = myflow.add_step('s0', repeats=[1], ) 
    
    s1 = s0.add_step('s1', func=square, kwargs={'x': 3}, ) 
    
    s2 = s0.add_step('s2', square_root, kwargs={'x': param}, requires=[(s1,seq.StepStatus.success), ],
                   recovery={evr.TaskStatus.failure: evr.StepReplay.rerun, 
                             evr.TaskStatus.success: evr.StepReplay.skip})
    
    s3=s0.add_step('s3', divide, kwargs={'x': 9, 'y': 3}, requires=[(s2, seq.StepStatus.success), ])
    
    return myflow

# start regularly; it would fail in step 2

ev=build_flow(param=-9)
ev.run()
ev.close()

# rerun in recovery
ev=build_flow(evr.RunMode.recover, param=9)
ev.run()
ev.close()
