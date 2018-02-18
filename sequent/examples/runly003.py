
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

appname = os.path.basename(__file__)
logger = logging.getLogger(appname)

import examples.run_progs as rprogs

myflow = seq.Sequent(name=appname, config={'LOGGING': {'logging_level': 20}})

s11 = myflow.add_step('s11', func=rprogs.prog, kwargs={'progname': 'prog11', 'success': True}, 
                      repeats=[1,], 
                      recovery={seq.STEP_FAILURE: seq.STEP_RERUN,
                                seq.STEP_SUCCESS: seq.STEP_RERUN}) 
s12 = myflow.add_step('s12', func=rprogs.prog, kwargs={'progname': 'prog12',}, 
                      repeats=[1,],
                      requires=( (s11, seq.STEP_SUCCESS), )) 

if __name__ == '__main__':
    myflow.run(run_mode=seq.RUN_RESTART, )
    print("\nCOMPETED RESTART; STARTING RECOVER.\n")
    myflow.run(run_mode=seq.RUN_RECOVER, )
    myflow.close()
