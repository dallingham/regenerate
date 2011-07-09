#
# Manage registers in a hardware design
#
# Copyright (C) 2008  Donald N. Allingham
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from .assert_base import AssertBase

class AssertSva(AssertBase):

    def __init__(self, dbase):
        AssertBase.__init__(self, dbase)

    def write_assertions(self, ofile):

        self.sorted_regs = [ 
            self.dbase.get_register(key) 
            for key in self.dbase.get_keys() 
            if not self.dbase.get_register(key).do_not_generate_code ]

        ofile.write('\n`ifdef USE_ASSERTIONS\n')
        if self.dbase.enable_ovm_messaging:
            ofile.write('  import ovm_pkg::*;\n\n')

        polarity = "" if self.polarity else "~"

        for register in self.sorted_regs:

            address = register.address
            control = "write_r%02x" % address
            
            ofile.write('   property prop_%s_data;\n' % control)
            ofile.write('      @(posedge %s)\n' % self.clock)
            ofile.write('      disable iff (%s%s)\n' % 
                        (polarity, self.reset))
            ofile.write('      %s && $stable(%s) |-> $stable(%s);\n' % 
                        (control, control, self.data_in))
            ofile.write('   endproperty\n\n')
            
            ofile.write('   property prop_%s_be;\n' % control)
            ofile.write('      @(posedge %s)\n' % self.clock)
            ofile.write('      disable iff (%s%s)\n' % 
                        (self.polarity, self.reset))
            ofile.write('      %s && $stable(%s) |-> $stable(%s);\n' % 
                        (control, control, self.byte_enables))
            ofile.write('   endproperty\n\n')
            
            ofile.write('   assert_%s_data : assert property(prop_%s_data)\n' %
                        (control, control))
            if self.dbase.enable_ovm_messaging:
                ofile.write('     else ovm_report_error("ASSERTION", ')
                ofile.write('"Address %h: data changed while write strobe')
                ofile.write(' active.");\n')
            ofile.write('   assert_%s_be : assert property(prop_%s_be)\n' %
                        (control, control))
            if self.dbase.enable_ovm_messaging:
                ofile.write('     else ovm_report_error("ASSERTION", ')
                ofile.write('"Address %h: byte enables changed while ')
                ofile.write('write strobe active.");\n')
            ofile.write('\n')
        ofile.write('\n`endif\n')

        
