 
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
import sequent.examples.run_progs as rprogs

appname = os.path.basename(__file__)
logger = logging.getLogger(appname)

config=os.path.abspath('runly.conf')
# because OSX adds /var -> /private/var
if config.startswith('/private'):
    config = config[8:]


myflow = seq.Sequent(name=appname, config=config, store='pgdb2', config_tag='SEQUENT', )

s = myflow.add_step('s0', repeats=[1])

s1 = s.add_step('s1', repeats=[1, 2])
s11 = s1.add_step('s11', func=rprogs.prog, kwargs={'progname': 'prog11'}, hosts=['ubuntud01_sequent']) 
s12 = s1.add_step('s12', func=rprogs.prog, kwargs={'progname': 'prog12'}, requires=( ( s11, seq.STEP_COMPLETE ), ))

s2 = s.add_step('s2', requires=( (s1, seq.STEP_COMPLETE), ),)
s21 = s2.add_step('s21', func=rprogs.prog, kwargs={'progname': 'prog21'})
s22 = s2.add_step('s22', func=rprogs.prog, kwargs={'progname': 'prog21'}, requires=( ( s21, seq.STEP_COMPLETE ), ))

e1 = s.add_event( ( (s1, seq.STEP_COMPLETE), (s2, seq.STEP_COMPLETE), ) )
s3 = s.add_step('s3', func=rprogs.prog, kwargs={'progname': 'prog3'}, requires=(e1,))


if __name__ == '__main__':
    # import multiprocessing as mp
    # mp.freeze_support()
    # mp.set_start_method('spawn')
    myflow.run()
    #myflow.close()
