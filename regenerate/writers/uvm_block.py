#! /usr/bin/python
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

from regenerate.db import BitField, TYPES, LOGGER
from regenerate.writers.writer_base import WriterBase

access_map = {BitField.TYPE_READ_ONLY: "RO",
              BitField.TYPE_READ_ONLY_LOAD: "RO",
              BitField.TYPE_READ_ONLY_VALUE: "RO",
              BitField.TYPE_READ_ONLY_CLEAR_LOAD: "RC",
              BitField.TYPE_READ_ONLY_VALUE_1S: "RO",
              BitField.TYPE_READ_WRITE: "RW",
              BitField.TYPE_READ_WRITE_1S: "RW",
              BitField.TYPE_READ_WRITE_1S_1: "RW",
              BitField.TYPE_READ_WRITE_LOAD: "RW",
              BitField.TYPE_READ_WRITE_LOAD_1S: "RW",
              BitField.TYPE_READ_WRITE_LOAD_1S_1: "RW",
              BitField.TYPE_READ_WRITE_SET: "RW",
              BitField.TYPE_READ_WRITE_SET_1S: "RW",
              BitField.TYPE_READ_WRITE_SET_1S_1: "RW",
              BitField.TYPE_READ_WRITE_CLR: "RW",
              BitField.TYPE_READ_WRITE_CLR_1S: "RW",
              BitField.TYPE_READ_WRITE_CLR_1S_1: "RW",
              BitField.TYPE_WRITE_1_TO_CLEAR_SET: "W1C",
              BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S: "W1C",
              BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S_1: "W1C",
              BitField.TYPE_WRITE_1_TO_CLEAR_LOAD: "W1C",
              BitField.TYPE_WRITE_1_TO_CLEAR_LOAD_1S: "W1C",
              BitField.TYPE_WRITE_1_TO_CLEAR_LOAD_1S_1: "W1C",
              BitField.TYPE_WRITE_1_TO_SET: "W1S",
              BitField.TYPE_WRITE_ONLY: "WO",
              }


class UVM_Block_Registers(WriterBase):

    REMAP_NAME = {
        'interface': 'interface_',
        'class': 'class_',
        'package': 'package_',
        'edge': 'edge_',
        }

    def __init__(self, project, dblist):
        WriterBase.__init__(self, project, None)
        self.endian = "UVM_LITTLE_ENDIAN"
        self.dblist = dblist

    def _fix_name(self, field):
        name = field.field_name.lower()
        name = "_".join(name.split())

        if name in self.REMAP_NAME:
            return self.REMAP_NAME[name]
        else:
            return name

    def mk_coverpt(self, value):
        if value[1]:
            return (value[1], int(value[0], 16))
        else:
            return (value[0], int(value[0], 16))

    def write(self, filename):

        of = open(filename, "w")

        of.write(' /* \\defgroup registers Registers */\n')

        of.write("package %s_reg_pkg;\n\n" % self._project.short_name)
        of.write("  import uvm_pkg::*;\n\n")
        of.write('  `include "uvm_macros.svh"\n')

        for dbase in self.dblist:

            self.generate_coverage(of, dbase)

            for key in dbase.get_keys():
                reg = dbase.get_register(key)
                self.write_register(reg, dbase, of)

            in_groups = set()
            in_maps = set()
            for group in self._project.get_grouping_list():
                for grp in self._project.get_group_map(group.name):
                    if grp.set == dbase.set_name:
                        in_groups.add(group.name)

            for addr_map in self._project.get_address_maps():
                map_list = self._project.get_address_map_groups(addr_map.name)
                for group_name in in_groups:
                    if not map_list or group_name in map_list:
                        in_maps.add(addr_map.name)
            self.write_dbase_block(dbase, of, in_maps)

        for group in self._project.get_grouping_list():
            in_maps = set()
            for addr_map in self._project.get_address_maps():
                map_list = self._project.get_address_map_groups(addr_map.name)
                if not map_list or group.name in map_list:
                    in_maps.add(addr_map.name)

            self.write_group_block(group, of, in_maps)

        self.write_toplevel_block(of)

        of.write('endpackage : %s_reg_pkg\n' % self._project.short_name)
        of.close()

    def write_toplevel_block(self, of):

        sname = self._project.short_name

        of.write("/*\n * Top level register block\n */\n\n")
        of.write("class %s_reg_block extends uvm_reg_block;\n" % sname)
        of.write("\n")
        of.write("   `uvm_object_utils(%s_reg_block)\n" % sname)
        of.write("\n")

        for group_name in self._project.get_grouping_list():
            of.write("   %s_group_reg_block %s;\n" %
                     (group_name[0], group_name[0]))

        for data in self._project.get_address_maps():
            of.write('   uvm_reg_map %s_map;\n' % data.name)

        of.write('   function new(string name = "%s_reg_block");\n' % sname)
        of.write("      super.new(name, "
                 "build_coverage(UVM_CVR_ADDR_MAP));\n")
        of.write("   endfunction : new\n")
        of.write("\n")
        of.write("   function void build();\n")
        of.write("      if(has_coverage(UVM_CVR_ADDR_MAP)) begin\n")
        of.write("         void'(set_coverage(UVM_CVR_ADDR_MAP));\n")
        of.write("      end\n")
        of.write("\n")

        for data in self._project.get_address_maps():
            name = "%s_map" % data.name
            of.write('      %s = create_map("%s", \'h%x, %d, %s);\n' %
                     (name, name, data.base, data.width, self.endian))
        of.write("\n")

        for group in self._project.get_grouping_list():
            name = group.name

            of.write('      %s = %s_group_reg_block::type_id::create("%s");\n' %
                     (name, name, name))
            of.write('      %s.configure(this, "%s");\n' %
                     (name, group.hdl))
            of.write("      %s.build();\n" % name)

        for data in self._project.get_address_maps():
            map_list = self._project.get_address_map_groups(data.name)
            if not map_list:
                map_list = [group.name
                            for group in self._project.get_grouping_list()]
            for name in map_list:
                of.write("      %s_map.add_submap(%s.%s_map, 0);\n" %
                         (data.name, name, data.name))
        of.write("\n")
        of.write("   endfunction: build\n")
        of.write("\n")
        of.write("endclass: %s_reg_block\n\n" % sname)

    def write_group_block(self, group, of, in_maps):

        sname = group[0]
        of.write("class %s_group_reg_block extends uvm_reg_block;\n" %
                 sname)
        of.write("\n")
        of.write("   `uvm_object_utils(%s_group_reg_block)\n" % sname)
        of.write("\n")

        for group_entry in self._project.get_group_map(group[0]):
            if group_entry.repeat > 1:
                of.write("   %s_reg_block %s[%d];\n" %
                         (group_entry.set, group_entry.set,
                          group_entry.repeat))
            else:
                of.write("   %s_reg_block %s;\n" %
                         (group_entry.set, group_entry.set))

        of.write("\n")
        for item in in_maps:
            of.write("   uvm_reg_map %s_map;\n" % item)

        of.write("\n")
        of.write('   function new(string name = "%s_group_reg_block");\n' %
                 sname)
        of.write("      super.new(name, build_coverage(UVM_CVR_ADDR_MAP));\n")
        of.write("   endfunction : new\n")
        of.write("\n")
        of.write("   function void build();\n")
        of.write("      if(has_coverage(UVM_CVR_ADDR_MAP)) begin\n")
        of.write("         void'(set_coverage(UVM_CVR_ADDR_MAP));\n")
        of.write("      end\n")
        of.write("\n")

        for item in in_maps:
            of.write('      %s_map = create_map("%s_map", 0, %d, %s);\n' %
                     (item, item, self._project.get_address_width(item),
                      self.endian))
        of.write("\n")

        for group_entry in self._project.get_group_map(group[0]):
            if group_entry.repeat > 1:
                name = group_entry.set
                of.write('      for(int i = 0; i < %d; i++) begin\n' %
                         group_entry.repeat)
                of.write('         %s[i] = %s_reg_block::type_id::create($sformatf("%s[%%0d]", i));\n' %
                         (name, name, name))
                of.write('         %s[i].configure(this, $sformatf("%s", i));\n' %
                         (name, group_entry.hdl))
                of.write("         %s[i].build();\n" % name)
                for item in in_maps:
                    of.write("         %s_map.add_submap(%s[i].%s_map, 'h%x + (i * 'h%x));\n" %
                             (item, name, item, group_entry.offset, group_entry.repeat_offset))
                of.write('      end\n')
            else:
                name = group_entry.set
                of.write('      %s = %s_reg_block::type_id::create("%s");\n' %
                         (name, name, name))
                of.write('      %s.configure(this, "%s");\n' %
                         (name, group_entry.hdl))
                of.write("      %s.build();\n" % name)
                for item in in_maps:
                    of.write("      %s_map.add_submap(%s.%s_map, 'h%x);\n" %
                             (item, name, item, group_entry.offset))
            of.write("\n")

        of.write("   endfunction: build\n")
        of.write("\n")
        of.write("endclass: %s_group_reg_block\n\n" % sname)

    def write_dbase_block(self, dbase, of, in_maps):
        of.write('  class %s_reg_block extends uvm_reg_block;\n\n'
                 % dbase.module_name)
        of.write('    `uvm_object_utils(%s_reg_block)\n\n'
                 % dbase.module_name)

        for key in dbase.get_keys():
            reg = dbase.get_register(key)
            field_keys = reg.get_bit_field_keys()
            for key in field_keys:
                field = reg.get_bit_field(key)
                if field.reset_parameter:
                    name = field.reset_parameter
                else:
                    name = "p%s" % field.field_name.upper()
                if field.reset_type == BitField.RESET_PARAMETER:
                    if field.width == 1:
                        of.write("    bit %s;\n" % name)
                    else:
                        of.write("    bit [%d:0] %s;\n"
                                 % (field.width - 1, name))

        for key in dbase.get_keys():
            reg = dbase.get_register(key)
            rname = "reg_%s_%s" % (dbase.module_name, reg.token.lower())
            of.write("    %s %s;\n" % (rname, reg.token.lower()))

        for item in in_maps:
            of.write("    uvm_reg_map %s_map;\n" % item)

        mod = dbase.module_name
        of.write('    %s_reg_access_wrapper %s_access_cg;\n\n' % (mod, mod))
        of.write('\n')
        of.write('    function new(string name = "%s_reg_block");\n' % mod)
        of.write('      super.new(name,build_coverage(UVM_CVR_ALL));\n')
        of.write('    endfunction\n\n')

        of.write('    virtual function void build();\n\n')

        of.write('      if(has_coverage(UVM_CVR_ALL)) begin\n')
        of.write('        %s_access_cg = %s_reg_access_wrapper::type_id::create("%s_access_cg");\n'
                 % (mod, mod, mod))
        of.write("        void'(set_coverage(UVM_CVR_ALL));\n")
        of.write('      end\n')

        for key in dbase.get_keys():
            reg = dbase.get_register(key)
            rname = "reg_%s_%s" % (dbase.module_name, reg.token.lower())

            of.write('      %s = %s::type_id::create("%s", , get_full_name());\n' %
                     (reg.token.lower(), rname, reg.token.lower()))
            for field_key in reg.get_bit_field_keys():
                field = reg.get_bit_field(field_key)
                if field.reset_type == BitField.RESET_PARAMETER:
                    if field.reset_parameter:
                        name = field.reset_parameter
                    else:
                        name = "p%s" % field.field_name.upper()
                    of.write('      %s.%s = %s;\n' % (reg.token.lower(),
                                                         name, name))

            of.write('      %s.configure(this);\n' % reg.token.lower())
            of.write('      %s.build();\n' % reg.token.lower())
            if not reg.do_not_generate_code:
                for key in reg.get_bit_field_keys():
                    field = reg.get_bit_field(key)
                    of.write('      %s.add_hdl_path_slice("r%02x_%s", %d, %d );\n'
                             % (reg.token.lower(), reg.address,
                                self._fix_name(field),
                                field.start_position, field.width))
                    of.write("\n")

        of.write("\n")

        for item in in_maps:
            of.write('      %s_map = create_map("%s_map", \'h0, %d, %s, 1);\n' %
                     (item, item, self._project.get_address_width(item), self.endian))

        for key in dbase.get_keys():
            reg = dbase.get_register(key)
            for item in in_maps:
                of.write('      %s_map.add_reg(%s, \'h%04x, "RW");\n' %
                         (item, reg.token.lower(), reg.address))
        of.write('\n')

        of.write('      lock_model();\n')
        of.write('    endfunction : build\n\n')

        of.write('    function void sample(uvm_reg_addr_t offset, '
                 'bit is_read, uvm_reg_map  map);\n')
        of.write('       if(get_coverage(UVM_CVR_ALL)) begin\n')
        of.write('          if(map.get_name() == "default_map") begin\n')
        of.write('             %s_access_cg.sample(offset, is_read);\n' %
                 dbase.module_name)
        of.write('          end\n')
        of.write('       end\n')
        of.write('    endfunction: sample\n\n')

        of.write('  endclass : %s_reg_block\n\n' % dbase.module_name)

    def write_register(self, reg, dbase, of):

        rname = "reg_%s_%s" % (dbase.module_name, reg.token.lower())

        of.write("/*! \\class %s\n" % rname)
        of.write(" *  \\brief %s\n" % reg.description)
        of.write(" *\n * \\addtogroup registers\n")
        of.write(" * * @{\n")
        of.write(" */\n")
        of.write("  class %s extends uvm_reg;\n\n" % rname)
        of.write("    `uvm_object_utils(%s);\n\n" % rname)
        field_keys = reg.get_bit_field_keys()
        field_list = []
        for key in field_keys:
            field = reg.get_bit_field(key)
            of.write("    uvm_reg_field %s;\n" % self._fix_name(field))
            if field.reset_type == BitField.RESET_PARAMETER:
                field_list.append(field)

        for field in field_list:
            if field.reset_parameter:
                name = field.reset_parameter
            else:
                name = "p%s" % field.field_name.upper()

            if field.width == 1:
                of.write("    bit %s = 1'b0;\n" % name)
            else:
                of.write("    bit [%d:0] %s = '0;\n" % (field.width - 1,
                                                        name))

        grps = set()

        for key in field_keys:
            field = reg.get_bit_field(key)
            if field.values:
                n = self._fix_name(field)
                grps.add("cov_%s" % n)
                of.write("\n      covergroup cov_%s;\n" % n)
                of.write("         option.per_instance = 1;\n")
                of.write("         %s: coverpoint %s.value {\n" %
                         (n.upper(), n.lower()))
                for value in field.values:
                    of.write("            bins bin_%s = {'h%x};\n" %
                             self.mk_coverpt(value))
                of.write("      }\n")
                of.write("      endgroup : cov_%s\n" % n)

        of.write('\n    function new(string name = "%s");\n' %
                 reg.token.lower())
        if grps:
            of.write('       super.new(name, %d, ' % reg.width)
            of.write('build_coverage(UVM_CVR_FIELD_VALS));\n')
            for item in grps:
                of.write('       %s = new;\n' % item)
        else:
            of.write('      super.new(name, %d' % reg.width)
            of.write(', UVM_NO_COVERAGE);\n')

        of.write('    endfunction : new\n\n')

        if grps:
            of.write('\n')
            of.write('    function void sample(uvm_reg_data_t data,\n')
            of.write('                         uvm_reg_data_t byte_en,\n')
            of.write('                         bit            is_read,\n')
            of.write('                         uvm_reg_map    map);\n')
            for item in grps:
                of.write('     %s.sample();\n' % item)
            of.write('    endfunction: sample\n\n')

        of.write('    virtual function void build();\n')

        field_keys = reg.get_bit_field_keys()

        for key in field_keys:
            field = reg.get_bit_field(key)
            of.write('      %s = uvm_reg_field::type_id::create("%s"' %
                     (self._fix_name(field), self._fix_name(field)))
            of.write(', , get_full_name());\n')

        dont_test = False

        field_keys = reg.get_bit_field_keys()
        for key in field_keys:
            field = reg.get_bit_field(key)
            size = field.width
            if field.start_position >= reg.width:
                lsb = field.start_position % reg.width
                tok = reg.token
                msg = "%s has bits that exceed the register width" % tok
                LOGGER.warning(msg)
            else:
                lsb = field.start_position

            access = access_map.get(field.field_type, None)
            if access is None:
                dont_test = True
                continue

            volatile = is_volatile(field)
            has_reset = 1
            if field.reset_type == BitField.RESET_PARAMETER:
                if field.reset_parameter:
                    reset = field.reset_parameter
                else:
                    reset = "p%s" % field.field_name.upper()
            else:
                reset = "%d'h%x" % (field.width, field.reset_value)
            is_rand = 0
            ind_access = individual_access(field, reg)

            of.write('      %s.configure(this, %d, %d, "%s", %d, %s, %d, %d, %d);\n' %
                     (self._fix_name(field), size, lsb, access, volatile,
                      reset, has_reset, is_rand, ind_access))

        if reg.do_not_test or dont_test:
            of.write('      uvm_resource_db #(bit)::set({"REG::", '
                     'get_full_name()}, "NO_REG_HW_RESET_TEST", 1);\n')
        if reg.do_not_test or dont_test:
            of.write('      uvm_resource_db #(bit)::set({"REG::", '
                     'get_full_name()}, "NO_REG_BIT_BASH_TEST", 1);\n')

        of.write('      reset();\n')
        of.write('    endfunction : build\n\n')
        of.write('  endclass : %s\n\n' % rname)
        of.write('/*!@}*/\n')

    def generate_coverage(self, of, dbase):

        base = dbase.module_name
        of.write("\n\n")
        of.write("class %s_reg_access_wrapper extends uvm_object;\n" % base)
        of.write("\n   `uvm_object_utils(%s_reg_access_wrapper)\n" % base)
        of.write("\n   static int s_num = 0;\n\n")
        of.write("   covergroup ra_cov(string name) with function "
                 "sample(uvm_reg_addr_t addr, bit is_read);\n\n")
        of.write("   option.per_instance = 1;\n")
        of.write("   option.name = name;\n\n")
        of.write("   ADDR: coverpoint addr {\n")
        for key in dbase.get_keys():
            reg = dbase.get_register(key)
            of.write("     bins r_%s = {'h%x};\n" % (reg.token.lower(),
                                                        reg.address))
        of.write("   }\n\n")
        of.write("   RW: coverpoint is_read {\n")
        of.write("      bins RD = {1};\n")
        of.write("      bins WR = {0};\n")
        of.write("   }\n\n")
        of.write("   ACCESS: cross ADDR, RW;\n\n")
        of.write("   endgroup : ra_cov\n\n")
        of.write('   function new(string name = "%s_reg_access_wrapper");\n' %
                 base)
        of.write('      ra_cov = new($sformatf("%s_%0d", name, s_num++));\n')
        of.write('   endfunction : new\n\n')
        of.write('   function void sample(uvm_reg_addr_t offset, bit is_read);\n')
        of.write('      ra_cov.sample(offset, is_read);\n')
        of.write('   endfunction: sample\n\n')
        of.write('endclass : %s_reg_access_wrapper\n\n' % base)


def is_volatile(field):
    return TYPES[field.field_type].input or field.volatile


def is_readonly(field):
    return TYPES[field.field_type].readonly


def individual_access(field, reg):
    """
    Make sure that the bits in the field are not in the same byte as any
    other field that is writable.
    """
    used_bytes = set()

    # get all the fields in the register
    flds = [reg.get_bit_field(key) for key in reg.get_bit_fields()]

    # loop through all fields are are not read only and are not the original
    # field we are checking for. Calculate the bytes used, and add them to the
    # used_bytes set

    for f in [fld for fld in flds if fld != field and not is_readonly(fld)]:
        for pos in range(f.start_position, f.stop_position + 1):
            used_bytes.add(pos / 8)

    # loop through the bytes used by the current field, and make sure they
    # do match any of the bytes used by other fields
    for pos in range(field.start_position, field.stop_position + 1):
        if (pos / 8) in used_bytes:
            return False
    return True
