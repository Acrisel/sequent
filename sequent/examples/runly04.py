
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

logger=logging.getLogger(__name__)

def prog(flow, progname, step_to_fail=None, iteration_to_fail=''):
    step_name=flow.get_step_name() 
    step_sequence=flow.get_step_sequence()
    logger.info("doing what %s is doing (%s/%s)" % (progname, step_name, step_sequence))
    if step_to_fail == step_name and step_sequence== iteration_to_fail:
        raise Exception("%s failed (%s/%s)" % (progname, step_name, step_sequence))
    return progname

def build_flow(run_mode=sqnt.RunMode.restart, step_to_fail=None, iteration_to_fail=''):
    myflow=sqnt.Sequent(logging_level=logging.INFO, run_mode=run_mode, config={'sleep_between_loops': 0.05,}, )
    

    s1=myflow.add_step('s1', repeats=[1,2], )
    
    s11=s1.add_step('s11', repeats=[1,2,], )
    
    s111=s11.add_step('s111', func=prog, kwargs={'flow': myflow, 'progname': 'prog1', 
                                                 'step_to_fail':step_to_fail, 
                                                 'iteration_to_fail':iteration_to_fail,}) 
    s112=s11.add_step('s112', func=prog, kwargs={'flow': myflow, 'progname': 'prog2', 
                                                 'step_to_fail':step_to_fail, 
                                                 'iteration_to_fail':iteration_to_fail,}, 
                      requires=( (s111, sqnt.StepStatus.success), )) 
    
    s12=s1.add_step('s12', func=prog, kwargs={'flow': myflow, 'progname': 'prog3', 
                                              'step_to_fail':step_to_fail, 
                                              'iteration_to_fail':iteration_to_fail,}, 
                    requires=( (s11, sqnt.StepStatus.success), )) 
    
    s2=myflow.add_step('s2', func=prog, kwargs={'flow': myflow, 'progname': 'prog4', 
                                                'step_to_fail':step_to_fail, 
                                                'iteration_to_fail':iteration_to_fail,}, 
                       requires=( (s1, sqnt.StepStatus.success), )) 
    return myflow

myflow=build_flow(step_to_fail='s1_s11_s111', iteration_to_fail='1.2.2')
result=myflow.run()
myflow.close()
print('run result: %s' % repr(result))

myflow=build_flow(run_mode=sqnt.RunMode.recover, )
result=myflow.run()
myflow.close()
print('run result: %s' % repr(result))
