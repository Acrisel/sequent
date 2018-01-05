
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
import logging
import math
import os

appname = os.path.basename(__file__)
logger = logging.getLogger(appname)

def square(x):
    y=x*x
    return y

def square_root(x):
    y=math.sqrt(x)
    return y


def divide(x,y):
    z=x/y
    return z



def build_flow(run_mode=seq.RUN_RESTART, param=9, run_id=None):
    myflow = seq.Sequent(name=appname, run_mode=run_mode, run_id=run_id, config={'sleep_between_loops': 0.05, 'LOGGING':{'logging_level':logging.DEBUG}})
    
    s0 = myflow.add_step('s0', repeats=[1], ) 
    
    s1 = s0.add_step('s1', func=square, kwargs={'x': 3}, ) 
    
    s2 = s0.add_step('s2', square_root, kwargs={'x': param}, requires=[(s1,seq.STEP_SUCCESS), ],
                   recovery={seq.STEP_FAILURE: seq.STEP_RERUN,
                             seq.STEP_SUCCESS: seq.STEP_SKIP})
    
    s3 = s0.add_step('s3', divide, kwargs={'x': 9, 'y': 3}, requires=[(s2, seq.STEP_SUCCESS), ])
    
    return myflow

# start regularly; it would fail in step 2

ev = build_flow(param=-9)
ev.run()
ev.close()

run_id = ev.run_id

# rerun in recovery
ev=build_flow(seq.RUN_RECOVER, param=9, run_id=run_id)
ev.run()
ev.close()
