
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

import sequent as sqnt
import logging
import os
from acris import virtual_resource_pool as vrp

appname = os.path.basename(__file__)
logger = logging.getLogger(appname)


def prog(progname, step_to_fail=None, iteration_to_fail=''):
    logger = logging.getLogger(os.getenv("SEQUENT_LOGGER_NAME"))
    step_name = os.environ["SEQUENT_STEP_NAME"]
    step_sequence = os.environ["SEQUENT_STEP_SEQUENCE"]
    logger.info("doing what %s is doing (%s/%s)" % (progname, step_name, step_sequence))
    if step_to_fail == step_name and step_sequence== iteration_to_fail:
        raise Exception("%s failed (%s/%s)" % (progname, step_name, step_sequence))
    return progname


class Resources1(vrp.Resource):
    pass


class Resources2(vrp.Resource):
    pass


def build_flow(run_mode=sqnt.RUN_RESTART, step_to_fail=None, iteration_to_fail='', run_id=None):
    myflow = sqnt.Sequent(name=appname, run_mode=run_mode, run_id=run_id, config={'sleep_between_loops': 0.05, 'LOGGING': {'logging_level': logging.INFO, }}, )
    
    rp1 = vrp.ResourcePool('rp1', resource_cls=Resources1, policy={'resource_limit': 4, })
    rp2 = vrp.ResourcePool('rp2', resource_cls=Resources2, policy={'resource_limit': 4, })

    s1 = myflow.add_step('s1', repeats=[1,2], acquires=[(rp1, 2), ])
    
    s11 = s1.add_step('s11', repeats=[1,2,], acquires=[(rp2, 2), ])
    
    s111 = s11.add_step('s111', func=prog, kwargs={'progname': 'prog1', 
                                                 'step_to_fail': step_to_fail, 
                                                 'iteration_to_fail': iteration_to_fail,}) 
    s112 = s11.add_step('s112', func=prog, kwargs={'progname': 'prog2', 
                                                 'step_to_fail':step_to_fail, 
                                                 'iteration_to_fail': iteration_to_fail,}, 
                      requires=( (s111, sqnt.STEP_SUCCESS), )) 
    
    s12 = s1.add_step('s12', func=prog, kwargs={'progname': 'prog3', 
                                              'step_to_fail': step_to_fail, 
                                              'iteration_to_fail': iteration_to_fail,}, 
                    requires=( (s11, sqnt.STEP_SUCCESS), )) 
    
    s2 = myflow.add_step('s2', func=prog, kwargs={'progname': 'prog4', 
                                                'step_to_fail': step_to_fail, 
                                                'iteration_to_fail': iteration_to_fail,}, 
                       requires=( (s1, sqnt.STEP_SUCCESS), )) 
    return myflow

myflow = build_flow(step_to_fail='s1_s11_s111', iteration_to_fail='1.2.2')
result = myflow.run()
print('run result: %s' % repr(result))

run_id = myflow.run_id

myflow = build_flow(run_mode=sqnt.RUN_RECOVER, run_id=run_id)
#myflow = build_flow()
result = myflow.run()
myflow.close()
print('run result: %s' % repr(result))
