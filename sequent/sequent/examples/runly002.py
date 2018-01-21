
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

appname = os.path.basename(__file__)
logger = logging.getLogger(appname)

import sequent.examples.run_progs as rprogs

config_file = os.path.abspath('runly.conf')

myflow = seq.Sequent(name=appname, config=config_file, store='sqfile00', config_tag='SEQUENT')

s1 = myflow.add_step('s1', repeats=[1, 2] )

s11 = s1.add_step('s11', func=rprogs.prog, kwargs={'progname': 'prog11', 'success': True}, repeats=[1,]) 
s12 = s1.add_step('s12', func=rprogs.prog, kwargs={'progname': 'prog12',}, repeats=[1,]) 

s2 = myflow.add_step('s2', func=rprogs.prog, kwargs={'progname': 'prog2'}, 
                   requires=( (s1, seq.STEP_SUCCESS), )) 

if __name__ == '__main__':
    import multiprocessing as mp
    mp.freeze_support()
    mp.set_start_method('spawn')
    myflow.run()
    myflow.close()
