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
"""
Actual program. Parses the arguments, and initiates the main window
"""

from regenerate.db import BitField
from regenerate.db import GroupMapData
from writer_base import WriterBase
from regenerate.extras import find_addresses

support_code = [
    "",
    "// Macros to handle base addresses and types",
    "#define REG_UINT8_PTR(addr)     ( (volatile uint8  *)(ADDRBASE + addr))",
    "#define REG_UINT16_PTR(addr)    ( (volatile uint16 *)(ADDRBASE + addr))",
    "#define REG_UINT32_PTR(addr)    ( (volatile uint32 *)(ADDRBASE + addr))",
    "#define REG_UINT64_PTR(addr)    ( (volatile uint64 *)(ADDRBASE + addr))",
    "",
    "typedef unsigned long long uint64;",
    "typedef unsigned long      uint32;",
    "typedef unsigned short     uint16;",
    "typedef unsigned char      uint8;",
    "",
]
code_reg32 = [
    "static uint32",
    "check_reg32(volatile uint32* addr_ptr, uint32 defval, uint32 ro_mask)",
    "{",
    "  if (*addr_ptr     != defval) return 1;",
    ""
    "  *addr_ptr = 0xffffffff;",
    "  if ((*addr_ptr & ro_mask) != ro_mask) return 1;",
    ""
    "  *addr_ptr = 0x0;"
    "  if ((*addr_ptr & ro_mask) != 0x0) return 3;"
    "",
    "  *addr_ptr = defval;",
    "  if (*addr_ptr != defval) return 4;",
    "",
    "  return 0;",
    "}",
]
code_reg64 = [
    "static uint32",
    "check_reg64(volatile uint64* addr_ptr, uint64 defval, uint64 ro_mask)",
    "{",
    "  uint32 status;",
    "  uint32 current_address;",
    "",
    "  current_address = (uint32) addr_ptr;",
    "  ",
    "  status = check_reg32((uint32*)current_address, ",
    "		       (uint32)defval & 0xffffffff, ",
    "		       (uint32)ro_mask& 0xffffffff);",
    "  if (status) return status;",
    "  status = check_reg32(((uint32*)current_address)+1, ",
    "		       (uint32)(defval>>32) & 0xffffffff, ",
    "		       (uint32)(ro_mask>>32)& 0xffffffff);",
    "  return status;",
    "}",
]
code_reg16 = [
    "static uint32",
    "check_reg16(volatile uint16* addr_ptr, uint16 defval, uint16 ro_mask)",
    "{",
    "  uint32 current_address;",
    "  volatile uint8* byte_ptr = (volatile uint8*) addr_ptr;",
    "",
    "  current_address = (uint32) addr_ptr;",
    "",
    "  if (*addr_ptr     != defval) return 1;",
    "",
    "  *addr_ptr = 0xffff;",
    "  if ((*addr_ptr & ro_mask) != ro_mask) return 2;",
    "",
    "  *addr_ptr = 0x0;"
    "  if ((*addr_ptr & ro_mask) != 0x0) return 3;"
    "",
    "  *addr_ptr = defval;",
    "  if (*addr_ptr != defval) return 4;",
    "",
    "  return 0;",
    "}",
]
code_reg8 = [
    "static uint32",
    "check_reg8(volatile uint8* addr_ptr, uint8 defval, uint8 ro_mask)",
    "{",
    "  if (*addr_ptr != defval) return 1;",
    "",
    "  *addr_ptr = 0xff;",
    "  if ((*addr_ptr & ro_mask) != ro_mask) return 2;",
    "",
    "  *addr_ptr = 0x0;"
    "  if ((*addr_ptr & ro_mask) != 0x0) return 3;"
    "",
    "  *addr_ptr = defval;",
    "  if (*addr_ptr != defval) return 4;",
    "",
    "  return 0;",
    "}", ]


class CTest(WriterBase):
    def __init__(self, project, dbase):
        WriterBase.__init__(self, project, dbase)
        self._offset = 0
        self._ofile = None
        self.module_set = set()

    def calc_default_value(self, register):
        value = 0

        for rng in [register.get_bit_field(key)
                    for key in register.get_bit_field_keys()]:
            value = value | (rng.reset_value << rng.start_position)
        return value

    def calc_ro_mask(self, register):
        value = 0x0

        for rng in [register.get_bit_field(key)
                    for key in register.get_bit_field_keys()]:
            if rng.field_type in (
                BitField.TYPE_READ_WRITE, BitField.TYPE_READ_WRITE_1S,
                BitField.TYPE_READ_WRITE_1S_1, BitField.TYPE_READ_WRITE_LOAD,
                BitField.TYPE_READ_WRITE_LOAD_1S,
                BitField.TYPE_READ_WRITE_LOAD_1S_1,
                BitField.TYPE_READ_WRITE_SET, BitField.TYPE_READ_WRITE_SET_1S,
                BitField.TYPE_READ_WRITE_SET_1S_1,
                BitField.TYPE_READ_WRITE_CLR, BitField.TYPE_READ_WRITE_CLR_1S,
                BitField.TYPE_READ_WRITE_PROTECT,
                BitField.TYPE_READ_WRITE_PROTECT_1S,
                BitField.TYPE_READ_WRITE_CLR_1S_1):
                for i in range(rng.lsb, rng.msb + 1):
                    value = value | (1 << i)
        return value

    def gen_test(self, cfile, dbase):

        first = True

        ext_opt = {8: "", 16: "", 32: "", 64: "LL"}

        cfile.write("\n")
        cfile.write("uint32\n")
        cfile.write("check_{0} (void)\n".format(dbase.module_name))
        cfile.write("{\n")

        index = 1
        for register in dbase.get_all_registers():
            
            if register.do_not_test:
                continue

            default = self.calc_default_value(register)
            mask = self.calc_ro_mask(register)
            if first:
                cfile.write("   uint32 val;\n\n")
                first = False
            width = register.width
            ext = ext_opt[width]
            
            cfile.write("  // %s\n" % register.register_name)
                
            for addr in find_addresses(self._project, dbase.set_name, register):
                cfile.write(
                    "   val = check_reg%d(REG_UINT%d_PTR(0x%x), 0x%x%s, 0x%x%s);\n"
                    % (width, width, addr, default, ext, mask, ext))
                cfile.write("   if (val) return (val | 0x%x00);\n\n" % index)
                index += 1

        cfile.write("   return 0;\n")
        cfile.write("}\n")

    def write(self, filename):
        """
        Actually runs the program
        """
        address_maps = self._project.get_address_maps()

        cfile = open(filename, "w")

        if address_maps:
            token = "#ifdef"
            for amap in address_maps:
                cfile.write("%s %s_MAP\n" % (token, amap.name.upper()))
                token = "#elif"
                cfile.write(" #define ADDRBASE (0x%x)\n" % amap.base)
            cfile.write("#else\n")
            cfile.write(" #define ADDRBASE (0)\n")
            cfile.write("#endif\n")
        else:
            cfile.write(" #define ADDRBASE (0)\n")

        for line in support_code:
            cfile.write(line + "\n")
        cfile.write("\n")

        use = {8: False, 16: False, 32: False, 64: False}

        for temp_reg in self._dbase.get_all_registers():
            if not temp_reg.do_not_test:
                use[temp_reg.width] = True
        if use[64]:
            use[32] = True

        if use[8]:
            cfile.write("\n".join(code_reg8) + "\n")
        if use[16]:
            cfile.write("\n".join(code_reg16) + "\n")
        if use[32]:
            cfile.write("\n".join(code_reg32) + "\n")
        if use[64]:
            cfile.write("\n".join(code_reg64) + "\n")

        self.gen_test(cfile, self._dbase)

        cfile.close()
