 
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
import os
from sequent_examples import run_progs as rprog

logger = logging.getLogger(__name__)

config = os.path.abspath('example00.conf')
myflow = seq.Sequent(logging_level=logging.DEBUG, config=config, shared_db=False, store='pgdb2', eventor_config_tag='SEQUENT', )

s1 = myflow.add_step('s1', repeats=[1,2] )

s11 = s1.add_step('s11', repeats=[1,2,])

s111 = s11.add_step('s111', func=rprog.prog, kwargs={'progname': 'prog1'}, hosts=['ubuntud01_sequent']) 
s112 = s11.add_step('s112', func=rprog.prog, kwargs={'progname': 'prog2',}, 
                  requires=( (s111, seq.StepStatus.success), )) 

s12 = s1.add_step('s12', func=rprog.prog, kwargs={'progname': 'prog3'}, 
                requires=( (s11, seq.StepStatus.success), )) 

s2 = myflow.add_step('s2', func=rprog.prog, kwargs={'progname': 'prog4'}, 
                   requires=( (s1, seq.StepStatus.success), )) 

if __name__ == '__main__':
    import multiprocessing as mp
    mp.freeze_support()
    mp.set_start_method('spawn')
    myflow.run()
    #myflow.close()
