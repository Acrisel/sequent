
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
import time
import os

logger=logging.getLogger(__name__)

def prog(flow, progname, success=True):
    logger.info("doing what %s is doing" % progname)
    time.sleep(1)
    if not success:
        raise Exception("%s failed" % progname)
    return progname

config_file = os.path.abspath('example00.conf')
#conf = os.path.join(os.path.dirname(__file__), config_file)
myflow = seq.Sequent(logging_level=logging.DEBUG, config=config_file, shared_db=True, store='sqfile00', eventor_config_tag='SEQUENT')
#myflow = seq.Sequent(logging_level=logging.DEBUG, config=config, store='pgdb2', eventor_config_tag='SEQUENT')

s1 = myflow.add_step('s1', repeats=range(2) )

s11 = s1.add_step('s11', repeats=[1,2,])

s111 = s1.add_step('s111', func=prog, kwargs={'flow': myflow, 'progname': 'prog1'}) 
s112 = s1.add_step('s112', func=prog, kwargs={'flow': myflow, 'progname': 'prog2',}, 
                  requires=( (s111, seq.StepStatus.success), )) 

s12 = s1.add_step('s12', func=prog, kwargs={'flow': myflow, 'progname': 'prog3'}, 
                requires=( (s11, seq.StepStatus.success), )) 

s2 = myflow.add_step('s2', func=prog, kwargs={'flow': myflow, 'progname': 'prog4'}, 
                   requires=( (s1, seq.StepStatus.success), )) 

myflow.run()
myflow.close()
