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


config_file = os.path.abspath('runly.conf')
myflow = seq.Sequent(config=config_file, store='sqfile00', config_tag='SEQUENT', )

s1 = myflow.add_step('s1', repeats=[1, ] )

s11 = s1.add_step('s11', repeats=[1, ])

kwargs111 = {'progname': 'prog111'}
kwargs112 = {'progname': 'prog112'}
kwargs12 = {'progname': 'prog12'}
kwargs2 = {'progname': 'prog2'}

s111 = s1.add_step('s111', func=rprogs.prog, kwargs=kwargs111, repeats=[1, ]) 
s112 = s1.add_step('s112', func=rprogs.prog, kwargs=kwargs112, 
                  requires=( (s111, seq.STEP_SUCCESS), )) 

s12 = s1.add_step('s12', func=rprogs.prog, kwargs=kwargs12, 
                requires=( (s11, seq.STEP_SUCCESS), )) 

s2 = myflow.add_step('s2', func=rprogs.prog, kwargs=kwargs2, 
                   requires=( (s1, seq.STEP_SUCCESS), )) 

if __name__ == '__main__':
    myflow.run()
