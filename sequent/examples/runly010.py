
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

logger=logging.getLogger(__name__)

def prog(progname, success=True):
    logger.info("doing what %s is doing" % progname)
    if not success:
        raise Exception("%s failed" % progname)
    return progname

config_file = os.path.abspath('example00.conf')
#conf = os.path.join(os.path.dirname(__file__), config_file)
#myflow = seq.Sequent(logging_level=logging.DEBUG, config=config_file, shared_db=False, store='sqfile00', eventor_config_tag='SEQUENT')
myflow = seq.Sequent(logging_level=logging.DEBUG, config=config_file, shared_db=False, store='sqfile00', eventor_config_tag='SEQUENT')

s = myflow.add_step('s0', repeats=[1,2,])

s1 = s.add_step('s1', repeats=[1,2,])
s11 = s1.add_step('s11', func=prog, kwargs={'progname': 'prog11'}) 
s12 = s1.add_step('s12', func=prog, kwargs={'progname': 'prog12'}, requires=( ( s11, seq.StepStatus.complete ), ))

s2 = s.add_step('s2', requires=( (s1, seq.StepStatus.complete), ),)
s21 = s2.add_step('s21', func=prog, kwargs={'progname': 'prog21'})
s22 = s2.add_step('s22', func=prog, kwargs={'progname': 'prog21'}, requires=( ( s21, seq.StepStatus.complete ), ))

e1 = s.add_event( ( (s1, seq.StepStatus.complete), (s2, seq.StepStatus.complete), ) )
s3 = s.add_step('s3', func=prog, kwargs={'progname': 'prog3'}, requires=(e1,))

myflow.run()
myflow.close()
