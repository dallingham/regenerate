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

import os
from regenerate.db import BitField, RegisterDb
from writer_base import WriterBase

support_code = [
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
    "static int",
    "check_reg32(volatile uint32* addr_ptr, uint32 defval, uint32 ro_mask)",
    "{",
    "  uint32 current_address;",
    "",
    "#ifndef FAST",
    "  volatile uint8* byte_ptr = (volatile uint8*) addr_ptr;",
    "  volatile uint16* word_ptr = (volatile uint16*) addr_ptr;",
    "#endif",
    "",
    "  current_address = (uint32) addr_ptr;",
    "",
    "  if (*addr_ptr     != defval) return 1;",
    ""
    "#ifndef FAST",
    "  if (*word_ptr     != (uint16) (defval & 0xffff)) return 2;",
    "  if (*(word_ptr+1) != (uint16) ((defval>>16) & 0xffff)) return 3;",
    "  if (*byte_ptr     != (uint8) (defval & 0xff)) return 4;",
    "  if (*(byte_ptr+1) != (uint8) ((defval>>8) & 0xff)) return 5;",
    "  if (*(byte_ptr+2) != (uint8) ((defval>>16) & 0xff)) return 6;",
    "  if (*(byte_ptr+3) != (uint8) ((defval>>24) & 0xff)) return 7;",
    "#endif",
    ""
    "  *addr_ptr = 0xffffffff;",
    "  if ((*addr_ptr & ro_mask) != ro_mask) return 8;",
    ""
    "  *addr_ptr = 0x0;"
    "  if ((*addr_ptr & ro_mask) != 0x0) return 8;"
    "",
    "  *addr_ptr = defval;",
    "  if (*addr_ptr != defval) return 9;",
    "",
    "#ifndef FAST",
    "  *word_ptr = 0xffff;",
    "  if ((*word_ptr & ro_mask & 0xffff) != (uint16) (ro_mask & 0xffff)) return 10;",
    ""
    "  *word_ptr = 0x0;"
    "  if ((*addr_ptr & ro_mask & 0xffff) != 0x0) return 10;"
    ""
    "  *(word_ptr+1) = 0xffff;",
    "  if ((*(word_ptr+1) & (ro_mask >> 16) & 0xffff) != (uint16) ((ro_mask >> 16) & 0xffff)) return 11;",
    "",
    "  *(word_ptr+1) = 0x0;"
    "  if ((*(word_ptr+1) & (ro_mask >> 16) & 0xffff) != 0x0) return 11;"
    ""
    "  *word_ptr = defval & 0xffff;",
    "  *(word_ptr+1) = (defval >> 16) & 0xffff;",
    "",
    "  *addr_ptr = defval;",
    "  if (*addr_ptr != defval) return 12;",
    "",
    "  *byte_ptr = 0xff;",
    "  if ((*byte_ptr & ro_mask & 0xff) != (uint8) (ro_mask & 0xff)) return 13;",
    "",
    "  *byte_ptr = 0x0;",
    "  if ((*byte_ptr & ro_mask & 0xff) != 0x0) return 13;",
    "",
    "  *(byte_ptr+1) = 0xff;",
    "  if ((*(byte_ptr+1) & (ro_mask >> 8) & 0xff) != (uint8) ((ro_mask >> 8) & 0xff)) return 14;",
    "",
    "  *(byte_ptr+1) = 0x0;",
    "  if ((*(byte_ptr+1) & (ro_mask >> 8) & 0xff) != 0x0) return 14;",
    "",
    "  *(byte_ptr+2) = 0xff;",
    "  if ((*(byte_ptr+2) & (ro_mask >> 16) & 0xff) != (uint8) ((ro_mask >> 16) & 0xff)) return 15;",
    "",
    "  *(byte_ptr+2) = 0x0;",
    "  if ((*(byte_ptr+2) & (ro_mask >> 16) & 0xff) != 0x0) return 15;",
    "",
    "  *(byte_ptr+3) = 0xff;",
    "  if ((*(byte_ptr+3) & (ro_mask >> 24) & 0xff) != (uint8) ((ro_mask >> 24) & 0xff)) return 16;",
    "",
    "  *(byte_ptr+3) = 0x0;",
    "  if ((*(byte_ptr+3) & (ro_mask >> 24) & 0xff) != 0x0) return 16;",
    "",
    "  *byte_ptr = defval & 0xff;",
    "  *(byte_ptr+1) = (defval >> 8) & 0xff;",
    "  *(byte_ptr+2) = (defval >> 16) & 0xff;",
    "  *(byte_ptr+3) = (defval >> 24) & 0xff;",
    "",
    "  *addr_ptr = defval;",
    "  if (*addr_ptr != defval) return 17;",
    "#endif",
    "",
    "  return 0;",
    "}",
]
code_reg64 = [
    "static int",
    "check_reg64(volatile uint64* addr_ptr, uint64 defval, uint64 ro_mask)",
    "{",
    "  int status;",
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
    "static int",
    "check_reg16(volatile uint16* addr_ptr, uint16 defval, uint16 ro_mask)",
    "{",
    "  uint32 current_address;",
    "  volatile uint8* byte_ptr = (volatile uint8*) addr_ptr;",
    "",
    "  current_address = (uint32) addr_ptr;",
    "",
    "  if (*addr_ptr     != defval) return 1;",
    "  if (*byte_ptr     != (uint8) (defval & 0xff)) return 2;",
    "  if (*(byte_ptr+1) != (uint8) ((defval>>8) & 0xff)) return 3;",
    "",
    "  *addr_ptr = 0xffff;",
    "  if ((*addr_ptr & ro_mask) != ro_mask) return 4;",
    "",
    "  *addr_ptr = defval;",
    "  if (*addr_ptr != defval) return 5;",
    "",
    "  *addr_ptr = defval;",
    "  if (*addr_ptr != defval) return 6;",
    "",
    "  *byte_ptr = 0xff;",
    "  if ((*byte_ptr & ro_mask & 0xff) != (uint8) (ro_mask & 0xff)) return 7;",
    "",
    "  *(byte_ptr+1) = 0xff;",
    "  if ((*(byte_ptr+1) & (ro_mask >> 8) & 0xff) != (uint8) ((ro_mask >> 8) & 0xff)) return 8;",
    "",
    "  *byte_ptr = defval & 0xff;",
    "  *(byte_ptr+1) = (defval >> 8) & 0xff;",
    "",
    "  *addr_ptr = defval;",
    "  if (*addr_ptr != defval) return 9;",
    "",
    "  return 0;",
    "}",
    ]
code_reg8 = [
    "static int",
    "check_reg8(volatile uint8* addr_ptr, uint8 defval, uint8 ro_mask)",
    "{",
    "  uint32 current_address;",
    "  current_address = (uint32) addr_ptr;",
    "",
    "  if (*addr_ptr != defval) return 1;",
    "",
    "  *addr_ptr = 0xff;",
    "  if ((*addr_ptr & ro_mask) != ro_mask) return 2;",
    "",
    "  *addr_ptr = defval;",
    "  if (*addr_ptr != defval) return 3;",
    "",
    "  *addr_ptr = defval;",
    "  if (*addr_ptr != defval) return 4;",
    "",
    "  return 0;",
    "}",
    ]


class CTest(WriterBase):

    def __init__(self, dbase):
        WriterBase.__init__(self, dbase)
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
            if rng.field_type in (BitField.TYPE_READ_WRITE, BitField.TYPE_WRITE_1S,
                                  BitField.TYPE_READ_WRITE_1S, BitField.TYPE_READ_WRITE_1S_1,
                                  BitField.TYPE_READ_WRITE_LOAD, BitField.TYPE_READ_WRITE_LOAD_1S,
                                  BitField.TYPE_READ_WRITE_LOAD_1S_1, BitField.TYPE_READ_WRITE_SET,
                                  BitField.TYPE_READ_WRITE_SET_1S, BitField.TYPE_READ_WRITE_SET_1S_1):
                for i in range(rng.start_position, rng.stop_position + 1):
                    value = value | (1 << i)
        return value

    def gen_test(self, cfile, dbase):

        first = True

        ext_opt = {8: "", 16: "", 32: "", 64: "LL"}

        cfile.write("\nint\ncheck_%s (void)\n" % dbase.module_name)
        cfile.write("{\n")
        for (inst, offset) in self._dbase.instances:
            cfile.write("\n// %s\n\n" % inst)
            for key in dbase.get_keys():
                register = dbase.get_register(key)
                addr = offset + register.address;

                if register.do_not_test:
                    continue
                default = self.calc_default_value(register)
                mask = self.calc_ro_mask(register)
                if first:
                    cfile.write("   uint8 val;\n\n")
                    first = False
                width = register.width
                ext = ext_opt[width]
                cfile.write("   val = check_reg%d(REG_UINT%d_PTR(0x%x), 0x%x%s, 0x%x%s);\n" %
                            (width, width, addr, default, ext, mask, ext))
                cfile.write("   if (val) return val;\n\n")
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
            for key in address_maps:
                cfile.write("%s %s_MAP\n" % (token, key.upper()))
                token = "#elif"
                cfile.write(" #define ADDRBASE (0x%x)\n" % address_maps[key])
            cfile.write("#else\n")
            cfile.write(" #define ADDRBASE (0)\n")
            cfile.write("#endif\n")
        else:
            cfile.write(" #define ADDRBASE (0)\n")

        for line in support_code:
            cfile.write(line + "\n")
        cfile.write("\n")

        use = {8: False, 16: False, 32: False, 64: False}

        for key in self._dbase.get_keys():
            temp_reg = self._dbase.get_register(key)
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
