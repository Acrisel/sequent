
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
import sequent_examples.run_progs as rprogs

logger=logging.getLogger(__name__)

config=os.path.abspath('runly.conf')
if config.startswith('/private'):
    config = config[8:]

myflow = seq.Sequent(config=config, store='pgdb2', config_tag='SEQUENT',)

s1 = myflow.add_step('s1', repeats=range(2) )

s11 = s1.add_step('s11', repeats=[1,2,])

s111 = s11.add_step('s111', func=rprogs.prog, kwargs={'progname': 'prog1'}) 
s112 = s11.add_step('s112', func=rprogs.prog, kwargs={'progname': 'prog2',}, 
                  requires=( (s111, seq.STP_SUCCESS), )) 

s12 = s1.add_step('s12', func=rprogs.prog, kwargs={'progname': 'prog3'}, 
                requires=( (s11, seq.STP_SUCCESS), ), delay=30, ) 

s2 = myflow.add_step('s2', func=rprogs.prog, kwargs={'progname': 'prog4'}, 
                   requires=( (s1, seq.STP_SUCCESS), )) 

myflow.run()
myflow.close()
