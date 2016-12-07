
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

logger=logging.getLogger(__name__)

def prog(flow, progname, success=True):
    logger.info("doing what %s is doing" % progname)
    
    if not success:
        raise Exception("%s failed" % progname)
    return progname

myflow=seq.Sequent(logging_level=logging.INFO, config={'sleep_between_loops': 0.05,}, )

s1=myflow.add_step('s1', repeat=[1,2])

s11=s1.add_step('s11', repeat=[1,2,])

s111=s11.add_step('s111', func=prog, kwargs={'flow': myflow, 'progname': 'prog1'}) 
s112=s11.add_step('s112', func=prog, kwargs={'flow': myflow, 'progname': 'prog2',}, 
                  require=( (s111, seq.StepStatus.success), )) 

s12=s1.add_step('s12', func=prog, kwargs={'flow': myflow, 'progname': 'prog3'}, 
                require=( (s11, seq.StepStatus.success), )) 

s2=myflow.add_step('s2', func=prog, kwargs={'flow': myflow, 'progname': 'prog4'}, 
                   require=( (s1, seq.StepStatus.success), )) 

myflow()
