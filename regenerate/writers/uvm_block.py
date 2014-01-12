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

#
# Map regenerate types to UVM type strings
#
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
    """
    Generates a SystemVerilog package representing the registers in
    the UVM format.
    """

    # Provide a mapping reserved SystemVerilog keywords to alternatives
    # to prevent syntax errors in the generated code.

    REMAP_NAME = {
        'interface': 'interface_',
        'class': 'class_',
        'package': 'package_',
        'edge': 'edge_',
        }

    def __init__(self, project, dblist):
        """
        Initialize the object. At the current time, only little endian is
        supported by the package
        """
        WriterBase.__init__(self, project, None)
        self.endian = "UVM_LITTLE_ENDIAN"
        self.dblist = dblist

    def _fix_name(self, field):
        """
        Creates a name from the field. If there are any spaces (which the
        UI should prevent), the are converted to underscores. We then replace
        name names that are reserved SystemVerilog words with alternatives.
        """
        name = "_".join(field.field_name.lower().split())

        if name in self.REMAP_NAME:
            return self.REMAP_NAME[name]
        else:
            return name

    def mk_coverpt(self, value):
        if value[1]:
            return (value[1], int(value[0], 16))
        else:
            return (value[0], int(value[0], 16))

    def _build_group_maps(self):
        group_maps = {}
        for group in self._project.get_grouping_list():
            in_maps = set()
            for addr_map in self._project.get_address_maps():
                map_list = self._project.get_address_map_groups(addr_map.name)
                if not map_list or group.name in map_list:
                    in_maps.add(addr_map.name)
            group_maps[group] = in_maps
        return group_maps

    def write(self, filename):
        """
        Write the data to the file as a SystemVerilog package. This includes
        a block of register definitions for each register and the associated
        container blocks.
        """

        group_maps = self._build_group_maps()

        of = open(filename, "w")
        of.write(' /* \\defgroup registers Registers */\n')
        of.write("package %s_reg_pkg;\n\n" % self._project.short_name)
        of.write("  import uvm_pkg::*;\n\n")
        of.write('  `include "uvm_macros.svh"\n')

        # Write register blocks
        for dbase in self.dblist:
            self.generate_coverage(of, dbase)

            for reg in dbase.get_all_registers():
                if reg.ram_size:
                    self.write_memory(reg, dbase, of)
                else:
                    self.write_register(reg, dbase, of)

            for group in self._project.get_grouping_list():
                used = set()
                for grp in self._project.get_group_map(group.name):
                    if grp.set == dbase.set_name and grp.set not in used:
                        used.add(grp.set)
                        self.write_dbase_block(dbase, of, group,
                                               group_maps[group])

        # Write group/subsystem blocks
        for group in group_maps:
            self.write_group_block(group, of, group_maps[group])

        # Write top level wrapper block
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

        for group in self._project.get_grouping_list():
            if group.repeat > 1:
                of.write("   %s_grp_reg_blk %s[%0d];\n" % (group.name, group.name, group.repeat))
            else:
                of.write("   %s_grp_reg_blk %s;\n" % (group.name, group.name))

        for data in self._project.get_address_maps():
            of.write('   uvm_reg_map %s_map;\n' % data.name)

        of.write('\n   function new(string name = "%s_reg_block");\n' % sname)
        of.write("      super.new(name, "
                 "build_coverage(UVM_CVR_ADDR_MAP));\n")
        of.write("   endfunction : new\n")
        of.write("\n")
        of.write("   function void build();\n\n")
        of.write("      if(has_coverage(UVM_CVR_ADDR_MAP)) begin\n")
        of.write("         void'(set_coverage(UVM_CVR_ADDR_MAP));\n")
        of.write("      end\n")
        of.write("\n")

        for data in self._project.get_address_maps():
            name = "%s_map" % data.name
            of.write('      %s = create_map("%s", \'h%x, %d, %s);\n' %
                     (name, name, data.base,
                      self._project.get_address_width(data.name), self.endian))
        of.write("\n")

        for group in self._project.get_grouping_list():
            name = group.name

            if group.repeat <= 1:
                of.write('      %s = %s_grp_reg_blk::type_id::create("%s");\n' %
                         (name, name, name))
                of.write('      %s.configure(this, "%s");\n' %
                         (name, group.hdl))
                of.write("      %s.build();\n" % name)
            else:
                of.write('      foreach (%s[i]) begin\n' % name)
                of.write('         %s[i] = %s_grp_reg_blk::type_id::create($sformatf("%s[%%d]", i));\n' %
                         (name, name, name))
                of.write('         %s[i].configure(this, "%s");\n' %
                         (name, group.hdl))
                of.write("         %s[i].build();\n" % name)
                of.write("      end\n")
                

        for data in self._project.get_address_maps():
            map_list = self._project.get_address_map_groups(data.name)
            if not map_list:
                map_list = [group.name
                            for group in self._project.get_grouping_list()]
            for name in map_list:
                grp_data = [grp for grp in self._project.get_grouping_list()
                            if grp.name == name]
                if grp_data[0].repeat <= 1:
                    of.write("      %s_map.add_submap(%s.%s_map, 'h%x);\n" %
                             (data.name, name, data.name, grp_data[0].base))
                else:
                    of.write("      foreach (%s[i]) begin\n" % name)
                    of.write("        %s_map.add_submap(%s[i].%s_map, 'h%x + (i * 'h%x));\n" %
                             (data.name, name, data.name, grp_data[0].base, grp_data[0].repeat_offset))
                    of.write("      end\n")
        of.write("\n")
        of.write("   endfunction: build\n")
        of.write("\n")
        of.write("endclass: %s_reg_block\n\n" % sname)

    def write_group_block(self, group, of, in_maps):

        sname = group[0]
        of.write("class %s_grp_reg_blk extends uvm_reg_block;\n" %
                 sname)
        of.write("\n")
        of.write("   `uvm_object_utils(%s_grp_reg_blk)\n" % sname)
        of.write("\n")

        for group_entry in self._project.get_group_map(group[0]):
            if group_entry.repeat > 1:
                of.write("   %s_%s_reg_blk %s[%d];\n" %
                         (sname, group_entry.set, group_entry.inst,
                          group_entry.repeat))
            else:
                of.write("   %s_%s_reg_blk %s;\n" %
                         (sname, group_entry.set, group_entry.inst))

        of.write("\n")
        for item in in_maps:
            of.write("   uvm_reg_map %s_map;\n" % item)

        of.write("\n")
        of.write('   function new(string name = "%s_grp_reg_blk");\n' %
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
                of.write('         %s[i] = %s_%s_reg_blk::type_id::create($sformatf("%s[%%0d]", i));\n' %
                         (group_entry.inst, sname, name, group_entry.inst))
                of.write('         %s[i].configure(this, $sformatf("%s", i));\n' %
                         (group_entry.inst, group_entry.hdl))
                of.write("         %s[i].build();\n" % group_entry.inst)
                for item in in_maps:
                    of.write("         %s_map.add_submap(%s[i].%s_map, 'h%x + (i * 'h%x));\n" %
                             (item, group_entry.inst, item, group_entry.offset,
                              group_entry.repeat_offset))
                of.write('      end\n')
            else:
                name = group_entry.set
                of.write('      %s = %s_%s_reg_blk::type_id::create("%s");\n' %
                         (group_entry.inst, sname, name, group_entry.inst))
                of.write('      %s.configure(this, "%s");\n' %
                         (group_entry.inst, group_entry.hdl))
                of.write("      %s.build();\n" % group_entry.inst)
                for item in in_maps:
                    of.write("      %s_map.add_submap(%s.%s_map, 'h%x);\n" %
                             (item, group_entry.inst, item, group_entry.offset))
            of.write("\n")

        of.write("   endfunction: build\n")
        of.write("\n")
        of.write("endclass: %s_grp_reg_blk\n\n" % sname)

    def write_dbase_block(self, dbase, of, group, in_maps):

        sname = dbase.set_name

        gmap_list = self._project.get_group_map(group.name)
        hdl_match = [grp.hdl for grp in gmap_list if grp.set == sname]

        of.write('  class %s_%s_reg_blk extends uvm_reg_block;\n\n'
                 % (group.name, sname))
        of.write('    `uvm_object_utils(%s_%s_reg_blk)\n\n'
                 % (group.name, sname))

        for reg in dbase.get_all_registers():
            for field in reg.get_bit_fields():
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

        for reg in dbase.get_all_registers():
            prefix = "mem" if reg.ram_size else "reg"
            token = reg.token.lower()
            rname = "%s_%s_%s" % (prefix, sname, token)
            of.write("    %s %s;\n" % (rname, token))

        for item in in_maps:
            of.write("    uvm_reg_map %s_map;\n" % item)

        of.write('    %s_reg_access_wrapper %s_access_cg;\n\n' % (sname, sname))
        of.write('\n')
        of.write('    function new(string name = "%s_%s_reg_blk");\n' %
                 (group.name, sname))
        of.write('      super.new(name,build_coverage(UVM_CVR_ALL));\n')
        of.write('    endfunction\n\n')

        of.write('    virtual function void build();\n\n')

        of.write('      if(has_coverage(UVM_CVR_ALL)) begin\n')
        of.write('        %s_access_cg = %s_reg_access_wrapper::type_id::create("%s_access_cg");\n'
                 % (sname, sname, sname))
        of.write("        void'(set_coverage(UVM_CVR_ALL));\n")
        of.write('      end\n')

        for reg in dbase.get_all_registers():
            token = reg.token.lower()
            prefix = "mem" if reg.ram_size else "reg"
            rname = "%s_%s_%s" % (prefix, sname, token)

            of.write('      %s = %s::type_id::create("%s", , get_full_name());\n' %
                     (token, rname, token))
            for field in reg.get_bit_fields():
                if field.reset_type == BitField.RESET_PARAMETER:
                    if field.reset_parameter:
                        name = field.reset_parameter
                    else:
                        name = "p%s" % field.field_name.upper()
                    of.write('      %s.%s = %s;\n' % (token, name, name))

            of.write('      %s.configure(this);\n' % token)
            if reg.ram_size == 0:
                of.write('      %s.build();\n' % token)
                if not reg.do_not_generate_code:
                    for field in reg.get_bit_fields():
                        of.write('      %s.add_hdl_path_slice("r%02x_%s", %d, %d );\n'
                                 % (token, reg.address, self._fix_name(field),
                                    field.start_position, field.width))
        of.write("\n")

        for item in in_maps:
            mname = "%s_map" % item
            of.write('      %s = create_map("%s", \'h0, %d, %s, 1);\n' %
                     (mname, mname, self._project.get_address_width(item),
                      self.endian))

        for reg in dbase.get_all_registers():
            for item in in_maps:
                cmd = "add_mem" if reg.ram_size else "add_reg"
                of.write('      %s_map.%s(%s, \'h%04x, "RW");\n' %
                         (item, cmd, reg.token.lower(), reg.address))

        if not hdl_match[0]:
            self.disable_access_tests(dbase, of)

        of.write('\n')

        of.write('      lock_model();\n')
        of.write('    endfunction : build\n\n')

        of.write('    function void sample(uvm_reg_addr_t offset, '
                 'bit is_read, uvm_reg_map  map);\n')
        of.write('       if (get_coverage(UVM_CVR_ALL)) begin\n')
        of.write('          %s_access_cg.sample(offset, is_read);\n' % sname)
        of.write('       end\n')
        of.write('    endfunction: sample\n\n')

        of.write('  endclass : %s_%s_reg_blk\n\n' %
                 (group.name, dbase.set_name))

    def disable_access_tests(self, dbase, of):
        for reg in dbase.get_all_registers():
            test = "MEM" if reg.ram_size else "REG"
            of.write('      uvm_resource_db #(bit)::set({"REG::", ')
            of.write('get_full_name(), ".%s"}, "NO_%s_ACCESS_TEST", 1);\n' %
                     (reg.token.lower(), test))

    def write_register(self, reg, dbase, of):

        rname = "reg_%s_%s" % (dbase.set_name, reg.token.lower())

        of.write("/*! \\class %s\n" % rname)
        of.write(" *  \\brief %s\n" % reg.description)
        of.write(" *\n * \\addtogroup registers\n")
        of.write(" * * @{\n")
        of.write(" */\n")
        of.write("  class %s extends uvm_reg;\n\n" % rname)
        of.write("    `uvm_object_utils(%s);\n\n" % rname)
        field_list = []
        for field in reg.get_bit_fields():
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

        for field in reg.get_bit_fields():
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
            of.write('    function void sample(uvm_reg_data_t data,\n')
            of.write('                         uvm_reg_data_t byte_en,\n')
            of.write('                         bit            is_read,\n')
            of.write('                         uvm_reg_map    map);\n')
            for item in grps:
                of.write('     %s.sample();\n' % item)
            of.write('    endfunction: sample\n\n')

        of.write('    virtual function void build();\n')

        for field in reg.get_bit_fields():
            of.write('      %s = uvm_reg_field::type_id::create("%s"' %
                     (self._fix_name(field), self._fix_name(field)))
            of.write(', , get_full_name());\n')

        dont_test = False
        side_effects = False
        no_reset_test = False

        for field in reg.get_bit_fields():
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

            if field.output_has_side_effect:
                side_effects = True

            volatile = is_volatile(field)
            has_reset = 1
            if field.reset_type == BitField.RESET_PARAMETER:
                no_reset_test = True
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
                     'get_full_name()}, "NO_REG_TESTS", 1);\n')
        else:
            if side_effects:
                of.write('      uvm_resource_db #(bit)::set({"REG::", '
                         'get_full_name()}, "NO_REG_BIT_BASH_TEST", 1);\n')
                of.write('      uvm_resource_db #(bit)::set({"REG::", '
                         'get_full_name()}, "NO_REG_ACCESS_TEST", 1);\n')
                of.write('      uvm_resource_db #(bit)::set({"REG::", '
                         'get_full_name()}, "NO_REG_SHARED_ACCESS_TEST", 1);\n')
            if no_reset_test:
                of.write('      uvm_resource_db #(bit)::set({"REG::", '
                         'get_full_name()}, "NO_REG_HW_RESET_TEST", 1);\n')

        of.write('      reset();\n')
        of.write('    endfunction : build\n\n')
        of.write('  endclass : %s\n\n' % rname)
        of.write('/*!@}*/\n')

    def write_memory(self, reg, dbase, of):

        rname = "mem_%s_%s" % (dbase.set_name, reg.token.lower())

        of.write("/*! \\class %s\n" % rname)
        of.write(" *  \\brief %s\n" % reg.description)
        of.write(" *\n * \\addtogroup registers\n")
        of.write(" * * @{\n")
        of.write(" */\n")
        of.write("  class %s extends uvm_mem;\n\n" % rname)
        of.write("    `uvm_object_utils(%s);\n\n" % rname)
        of.write('    function new(string name = "%s");\n' %
                 reg.token.lower())
        num_bytes = reg.width / 8
        of.write('       super.new(name, %d, %d, "RW", UVM_NO_COVERAGE);\n'
                 % (reg.ram_size / num_bytes, reg.width))
        of.write('    endfunction : new\n\n')

        of.write('  endclass : %s\n\n' % rname)
        of.write('/*!@}*/\n')

    def generate_coverage(self, of, dbase):

        base = dbase.set_name
        of.write("\n\n")
        of.write("class %s_reg_access_wrapper extends uvm_object;\n" % base)
        of.write("\n   `uvm_object_utils(%s_reg_access_wrapper)\n" % base)
        of.write("\n   static int s_num = 0;\n\n")
        of.write("   covergroup ra_cov(string name) with function "
                 "sample(uvm_reg_addr_t addr, bit is_read);\n\n")
        of.write("   option.per_instance = 1;\n")
        of.write("   option.name = name;\n\n")
        of.write("   ADDR: coverpoint addr {\n")
        for reg in dbase.get_all_registers():
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
    flds = reg.get_bit_fields()

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
