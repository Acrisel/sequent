
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

logger=logging.getLogger(__name__)

def prog(progname, success=True):
    logger.info("doing what %s is doing" % progname)
    time.sleep(3)
    if not success:
        raise Exception("%s failed" % progname)
    return progname

myflow=seq.Sequent(logging_level=logging.INFO)

s0=myflow.add_step('s0', repeat=[1,2])
s00=s0.add_step('s00', repeat=[1,2,])

s1=s00.add_step('s1', func=prog, kwargs={'progname': 'prog1'}) 
s2=s00.add_step('s2', func=prog, kwargs={'progname': 'prog2'}, require=( (s1, seq.StepStatus.success), )) 

s3=s0.add_step('s3', func=prog, kwargs={'progname': 'prog3'}, require=( (s00, seq.StepStatus.success), )) 

myflow()
