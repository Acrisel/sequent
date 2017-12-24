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
import sequent_examples.run_progs as rprogs
from sequent_examples.run_progs import Step

class Prog(Step):
    def main(self, *args, **kwargs):
        return rprogs.prog(*args, **kwargs)

logger=logging.getLogger(__name__)

config_file = os.path.abspath('runly.conf')
myflow = seq.Sequent()
# myflow = seq.Sequent(config=config_file, store='sqfile00', config_tag='SEQUENT', )
# myflow = seq.Sequent(logging_level=logging.DEBUG, config=config, store='pgdb2', eventor_config_tag='SEQUENT')

s1 = myflow.add_step('s1', repeats=[1,] )

s11 = s1.add_step('s11', repeats=[1,])

s111 = s1.add_step('s111', func=Prog(), kwargs={'progname': 'prog1'}, repeats=[1,]) 
s112 = s1.add_step('s112', func=Prog(), kwargs={'progname': 'prog2',}, 
                  requires=( (s111, seq.StepStatus.success), )) 

s12 = s1.add_step('s12', func=Prog(), kwargs={'progname': 'prog3'}, 
                requires=( (s11, seq.StepStatus.success), )) 

s2 = myflow.add_step('s2', func=Prog(), kwargs={'progname': 'prog4'}, 
                   requires=( (s1, seq.StepStatus.success), )) 

if __name__ == '__main__':
    import multiprocessing as mp
    mp.freeze_support()
    mp.set_start_method('spawn')
    myflow.run()
    #myflow.close()
