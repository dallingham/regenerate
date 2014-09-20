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
ACCESS_MAP = {BitField.TYPE_READ_ONLY: "RO",
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


class UVMBlockRegisters(WriterBase):
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
        'set': 'set_',
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
        name = self._project.short_name

        with open(filename, "w") as of:
            of.write(' /* \\defgroup registers Registers */\n')
            of.write("package {0}_reg_pkg;\n\n".format(name))
            of.write("  import uvm_pkg::*;\n\n")
            of.write('  `include "uvm_macros.svh"\n')

            # Write register blocks
            for dbase in self.dblist:
                self.write_db_coverage(of, dbase)
                self.write_db_registers(of, dbase)
                self.write_db_groups(of, dbase, group_maps)

            # Write group/subsystem blocks
            for group in group_maps:
                self.write_group_block(group, of, group_maps[group])

            # Write top level wrapper block
            self.write_toplevel_block(of)

            of.write('endpackage : {0}_reg_pkg\n'.format(name))

    def write_db_registers(self, of, dbase):
        """
        Loop through all registers, writing either the memory block
        or a register
        """
        for reg in dbase.get_all_registers():
            if reg.ram_size:
                self.write_memory(reg, dbase, of)
            else:
                self.write_register(reg, dbase, of)

    def write_db_groups(self, of, dbase, group_maps):
        for group in self._project.get_grouping_list():
            used = set()
            for grp in group.register_sets:
                if grp.set == dbase.set_name and grp.set not in used:
                    used.add(grp.set)
                    self.write_dbase_block(dbase, of, group, group_maps[group])

    def write_toplevel_block_new(self, of):
        func_def = (
            "",
            '   function new(string name = "{0}_reg_block");',
            '      super.new(name, build_coverage(UVM_CVR_ADDR_MAP));',
            '   endfunction : new',
            ''
            )

        for line in func_def:
            of.write(line.format(self._project.short_name))
            of.write("\n")

    def write_toplevel_block_build(self, of):
        func_def = (
            '   function void build();',
            '',
            '      if (has_coverage(UVM_CVR_ADDR_MAP)) begin',
            "         void'(set_coverage(UVM_CVR_ADDR_MAP));",
            "      end",
            "",
            )

        for line in func_def:
            of.write(line.format(self._project.short_name))
            of.write("\n")

        map2grp = self.build_map_name_to_groups()
        map2base = self.build_map_name_to_base_address()

        for key in map2grp:
            map_name = "{0}_map".format(key)
            of.write('      if (!disable_{0}) begin\n'.format(map_name))
            of.write('         {0} = create_map("{0}", \'h{1:x}, {2:d}, {3});\n'.format(
                     map_name, map2base[key], self._project.get_address_width(key),
                     self.endian))
            of.write('      end\n')
        of.write("\n")

        for group in self._project.get_grouping_list():
            if group.repeat <= 1:
                self.build_and_configure_group(of, group, map2grp)
            else:
                self.build_and_configure_group_array(of, group, map2grp)

        for data in self._project.get_address_maps():
            map_list = self._project.get_address_map_groups(data.name)
            if not map_list:
                map_list = [group.name
                            for group in self._project.get_grouping_list()]
            for name in map_list:
                grp_data = [grp for grp in self._project.get_grouping_list()
                            if grp.name == name]
                self.connect_submaps(of, grp_data[0], data.name, name)

        of.write('      lock_model();\n')
        of.write("\n")
        of.write("   endfunction: build\n")

    def connect_submaps(self, of, grp_data, data_name, name):
        disable = "disable_{0}_map".format(data_name)
        mapname = "{0}_map".format(data_name)

        if grp_data.repeat <= 1:
            of.write('      if (!{0}) begin\n'.format(disable))
            of.write("         {0}.add_submap({1}.{0}, 'h{2:x});\n".format(
                     mapname, name, grp_data.base))
            of.write('      end\n')
        else:
            of.write('      foreach ({0}[i]) begin\n'.format(name))
            of.write('         if (!{0}) begin\n'.format(disable))
            of.write("            {0}.add_submap({1}[i].{0}, 'h{2:x} + (i * 'h{3:x}));\n".format(
                     mapname, name, grp_data.base, grp_data.repeat_offset))
            of.write("         end\n")
            of.write("      end\n")

    def build_and_configure_group(self, of, group, map2grp):
        name = group.name
        cls = "{0}_grp_reg_blk".format(name)
        of.write('      {0} = {1}::type_id::create("{0}");\n'.format(name, cls))
        of.write('      {0}.configure(this, "{1}");\n'.format(name, group.hdl))
        for mname in map2grp:
            if name in map2grp[mname]:
                disable = "disable_{0}_map".format(mname)
                of.write("      {0}.{1} = {1};\n".format(name, disable))
        of.write("      {0}.build();\n".format(name))

    def build_and_configure_group_array(self, of, group, map2grp):
        name = group.name
        cls = "{0}_grp_reg_blk".format(name)

        of.write('      foreach ({0}[i]) begin\n'.format(name))
        of.write('         {0}[i] = {1}::type_id::create($sformatf("{0}[%0d]", i));\n'.format(name, cls))
        if group.hdl:
            of.write('         {0}[i].configure(this, $sformatf("{1}", i));\n'.format(name, group.hdl))
        else:
            of.write('         {0}[i].configure(this, "");\n'.format(name))

        for mname in map2grp:
            if name in map2grp[mname]:
                disable = "disable_{0}_map".format(mname)
                of.write("         {0}[i].{1} = {1};\n".format(name, disable))
        of.write("         {0}[i].build();\n".format(name))
        of.write("      end\n")

    def build_map_name_to_groups(self):
        map2grp = {}
        all_groups = [grp.name for grp in self._project.get_grouping_list()]

        for data in self._project.get_address_maps():
            name = data.name
            map2grp[name] = self._project.get_address_map_groups(name)
            if not map2grp[name]:
                map2grp[name] = all_groups
        return map2grp

    def build_map_name_to_base_address(self):
        map2base = {}

        for data in self._project.get_address_maps():
            map2base[data.name] = data.base
        return map2base

    def write_toplevel_block(self, of):

        header = (
            "/*",
            " * Top level register block",
            " */",
            "",
            "class {0}_reg_block extends uvm_reg_block;",
            "",
            "   `uvm_object_utils({0}_reg_block)",
            "",
            )

        # Write class header
        for line in header:
            of.write(line.format(self._project.short_name))
            of.write("\n")

        # Declare class instances for the sub blocks
        for group in self._project.get_grouping_list():
            gclass = "{0}_grp_reg_blk".format(group.name)
            gname = group.name
            repeat = group.repeat

            if repeat > 1:
                of.write("   {0} {1}[{2}];\n".format(gclass, gname, repeat))
            else:
                of.write("   {0} {1};\n".format(gclass, gname))

        # Declare register maps
        for data in self._project.get_address_maps():
            of.write('   uvm_reg_map {0}_map;\n'.format(data.name))

        # Declare variables to enable/disable register maps
        for data in self._project.get_address_maps():
            of.write('   bit disable_{0}_map = 1\'b0;\n'.format(data.name))

        # Create new and build functions
        self.write_toplevel_block_new(of)
        self.write_toplevel_block_build(of)

        # End the class declaration
        of.write("\n")
        of.write("endclass: {0}_reg_block\n\n".format(self._project.short_name))

    def write_group_block(self, group, of, in_maps):

        class_name = "{0}_grp_reg_blk".format(group.name)

        sname = group.name
        of.write("class {0} extends uvm_reg_block;\n".format(class_name))
        of.write("\n")
        of.write("   `uvm_object_utils({0})\n".format(class_name))
        of.write("\n")

        for group_entry in group.register_sets:
            if group_entry.repeat > 1:
                of.write("   {0}_{1}_reg_blk {2}[{3}];\n".format(
                         sname, group_entry.set, group_entry.inst,
                         group_entry.repeat))
            else:
                of.write("   {0}_{1}_reg_blk {2};\n".format(
                         sname, group_entry.set, group_entry.inst))

        of.write("\n")
        for item in in_maps:
            of.write("   uvm_reg_map {0}_map;\n".format(item))
            of.write("   bit disable_{0}_map = 1'b0;\n".format(item))

        of.write("\n")
        of.write('   function new(string name = "{0}");\n'.format(class_name))
        of.write("      super.new(name, build_coverage(UVM_CVR_ADDR_MAP));\n")
        of.write("   endfunction : new\n")
        of.write("\n")
        of.write("   function void build();\n")
        of.write("      if(has_coverage(UVM_CVR_ADDR_MAP)) begin\n")
        of.write("         void'(set_coverage(UVM_CVR_ADDR_MAP));\n")
        of.write("      end\n")
        of.write("\n")

        for item in in_maps:
            of.write('      if (!disable_{0}_map) begin\n'.format(item))
            of.write('         {0}_map = create_map("{0}_map", 0, {1}, {2});\n'.format(
                     item, self._project.get_address_width(item), self.endian))
            of.write('      end\n')
        of.write("\n")

        for group_entry in group.register_sets:
            name = group_entry.set
            inst = group_entry.inst
            if group_entry.repeat > 1:
                of.write('      for(int i = 0; i < {0}; i++) begin\n'.format(
                         group_entry.repeat))
                of.write('         {0}[i] = {1}_{2}_reg_blk::type_id::create($sformatf("{0}[%0d]", i));\n'.format(
                         inst, sname, name))
                if group_entry.hdl:
                    of.write('         {0}[i].configure(this, $sformatf("{1}", i));\n'.format(
                             inst, group_entry.hdl))
                else:
                    of.write('         {0}[i].configure(this, "");\n'.format(inst))

                for item in in_maps:
                    disable = "disable_{0}_map".format(item)
                    of.write("         {0}[i].{1} = {1};\n".format(inst, disable))

                of.write("         {0}[i].build();\n".format(inst))

                for item in in_maps:
                    disable = "disable_{0}_map".format(item)
                    mname = "{0}_map".format(item)

                    of.write("         if (!{0}) begin\n".format(disable))
                    of.write("            {0}.add_submap({1}[i].{0}, 'h{2:x} + (i * 'h{3:x}));\n".format(
                             mname, inst, group_entry.offset, group_entry.repeat_offset))
                    of.write("         end\n")
                    if group_entry.no_uvm:
                        of.write('        uvm_resource_db#(bit)::set({{"REG::",{0}[i].get_full_name(),".*"}},\n'.format(inst))
                        of.write('                                    "NO_REG_TESTS", 1, this);\n')
                of.write('      end\n')
            else:
                of.write('      {0} = {1}_{2}_reg_blk::type_id::create("{0}");\n'.format(
                         inst, sname, name))
                of.write('      {0}.configure(this, "{1}");\n'.format(
                         inst, group_entry.hdl))
                for item in in_maps:
                    of.write("      {0}.disable_{1}_map = disable_{1}_map;\n".format(inst, item))
                of.write("      {0}.build();\n".format(inst))
                for item in in_maps:
                    of.write("      if (!disable_{0}_map) begin\n".format(item))
                    of.write("         {0}_map.add_submap({1}.{0}_map, 'h{2:x});\n".format(
                             item, inst, group_entry.offset))
                    of.write("      end\n")
                if group_entry.no_uvm:
                    of.write('      uvm_resource_db#(bit)::set({{"REG::",{0}.get_full_name(),".*"}},'.format(inst))
                    of.write(' "NO_REG_TESTS", 1, this);\n')
            of.write("\n")

        of.write("   endfunction: build\n")
        of.write("\n")
        of.write("endclass: {0}\n\n".format(class_name))

    def write_dbase_block(self, dbase, of, group, in_maps):

        sname = dbase.set_name

        gmap_list = group.register_sets
        hdl_match = [grp.hdl for grp in gmap_list if grp.set == sname]

        of.write('  class {0}_{1}_reg_blk extends uvm_reg_block;\n\n'.format(
                 group.name, sname))
        of.write('    `uvm_object_utils({0}_{1}_reg_blk)\n\n'.format(
                 group.name, sname))

        for reg in dbase.get_all_registers():
            for field in reg.get_bit_fields():
                if field.reset_parameter:
                    name = field.reset_parameter
                else:
                    name = "p{0}".format(field.field_name.upper())
                if field.reset_type == BitField.RESET_PARAMETER:
                    if field.width == 1:
                        of.write("    bit {0};\n".format(name))
                    else:
                        of.write("    bit [{0:d}:0] {1};\n".format(
                                 field.width - 1, name))

        for reg in dbase.get_all_registers():
            prefix = "mem" if reg.ram_size else "reg"
            token = reg.token.lower()
            rname = "_".join((prefix, sname, token))
            of.write("    {0} {1};\n".format(rname, token))

        for item in in_maps:
            of.write("    uvm_reg_map {0}_map;\n".format(item))
            of.write("    bit disable_{0}_map = 1'b0;\n".format(item))

        of.write('    {0}_reg_access_wrapper {0}_access_cg;\n\n'.format(sname))
        of.write('\n')
        of.write('    function new(string name = "{0}_{1}_reg_blk");\n'.format(
                 group.name, sname))
        of.write('      super.new(name,build_coverage(UVM_CVR_ALL));\n')
        of.write('    endfunction\n\n')

        of.write('    virtual function void build();\n\n')

        of.write('      if(has_coverage(UVM_CVR_ALL)) begin\n')
        of.write('        {0}_access_cg = {0}_reg_access_wrapper::type_id::create("{0}_access_cg");\n'.format(
                 sname))
        of.write("        void'(set_coverage(UVM_CVR_ALL));\n")
        of.write('      end\n')

        for reg in dbase.get_all_registers():
            token = reg.token.lower()
            prefix = "mem" if reg.ram_size else "reg"
            rname = "_".join((prefix, sname, token))

            of.write('      {0} = {1}::type_id::create("{0}", , get_full_name());\n'.format(
                     token, rname, token))
            for field in reg.get_bit_fields():
                if field.reset_type == BitField.RESET_PARAMETER:
                    if field.reset_parameter:
                        name = field.reset_parameter
                    else:
                        name = "".join(["p", field.field_name.upper()])
                    of.write('      {0}.{1} = {1};\n'.format(token, name))

            of.write('      {0}.configure(this);\n'.format(token))
            if reg.ram_size == 0:
                of.write('      {0}.build();\n'.format(token))
                if not reg.do_not_generate_code:
                    for field in reg.get_bit_fields():
                        of.write('      %s.add_hdl_path_slice("r%02x_%s", %d, %d );\n'
                                 % (token, reg.address, self._fix_name(field),
                                    field.lsb, field.width))
        of.write("\n")

        for item in in_maps:
            mname = "{0}_map".format(item)

            of.write('      if (!disable_{0}_map) begin;\n'.format(item))
            width = min(dbase.data_bus_width / 8,
                        self._project.get_address_width(item))
            of.write('         {0} = create_map("{0}", \'h0, {1:d}, {2}, 1);\n'.format(
                     mname, width, self.endian))
            of.write('      end\n')

        for reg in dbase.get_all_registers():
            for item in in_maps:
                cmd = "add_mem" if reg.ram_size else "add_reg"
                of.write('      if (!disable_{0}_map) begin\n'.format(item))
                of.write('         %s_map.%s(%s, \'h%04x, "RW");\n' %
                         (item, cmd, reg.token.lower(), reg.address))
                of.write('      end\n')

        if not hdl_match[0]:
            self.disable_access_tests(dbase, of)

        of.write('\n')
        of.write('    endfunction : build\n\n')
        of.write('    function void sample(uvm_reg_addr_t offset, '
                 'bit is_read, uvm_reg_map  map);\n')
        of.write('       if (get_coverage(UVM_CVR_ALL)) begin\n')
        of.write('          {0}_access_cg.sample(offset, is_read);\n'.format(sname))
        of.write('       end\n')
        of.write('    endfunction: sample\n\n')
        of.write('  endclass : {0}_{1}_reg_blk\n\n'.format(group.name, dbase.set_name))

    def disable_access_tests(self, dbase, of):
        for reg in dbase.get_all_registers():
            test = "MEM" if reg.ram_size else "REG"
            of.write('      uvm_resource_db #(bit)::set({"REG::", ')
            of.write('get_full_name(), ".{0}"}}, "NO_{1}_ACCESS_TEST", 1);\n'.format(
                     reg.token.lower(), test))

    def write_register(self, reg, dbase, of):

        rname = "reg_{0}_{1}".format(dbase.set_name, reg.token.lower())

        of.write("/*! \\class {0}\n".format(rname))
        of.write(" *  \\brief {0}\n".format(reg.description))
        of.write(" *\n * \\addtogroup registers\n")
        of.write(" * * @{\n")
        of.write(" */\n")
        of.write("  class {0} extends uvm_reg;\n\n".format(rname))
        of.write("    `uvm_object_utils({0});\n\n".format(rname))
        field_list = []
        for field in reg.get_bit_fields():
            of.write("    uvm_reg_field {0};\n".format(self._fix_name(field)))
            if field.reset_type == BitField.RESET_PARAMETER:
                field_list.append(field)

        for field in field_list:
            if field.reset_parameter:
                name = field.reset_parameter
            else:
                name = "".join(["p", field.field_name.upper()])

            if field.width == 1:
                of.write("    bit {0} = 1'b0;\n".format(name))
            else:
                of.write("    bit [{0}:0] {1} = '0;\n".format(field.width - 1,
                                                              name))

        grps = set()

        for field in reg.get_bit_fields():
            if field.values:
                n = self._fix_name(field)
                grps.add("cov_{0}".format(n))
                of.write("\n      covergroup cov_{0};\n".format(n))
                of.write("         option.per_instance = 1;\n")
                of.write("         {0}: coverpoint {1}.value {{\n".format(
                         n.upper(), n.lower()))
                for value in field.values:
                    of.write("            bins bin_%s = {'h%x};\n" %
                             self.mk_coverpt(value))
                of.write("      }\n")
                of.write("      endgroup : cov_{0}\n".format(n))

        of.write('\n    function new(string name = "{0}");\n'.format(
                 reg.token.lower()))
        if grps:
            of.write('       super.new(name, {0}, '.format(reg.width))
            of.write('build_coverage(UVM_CVR_FIELD_VALS));\n')
            for item in grps:
                of.write('       {0} = new;\n'.format(item))
        else:
            of.write('      super.new(name, {0}'.format(reg.width))
            of.write(', UVM_NO_COVERAGE);\n')

        of.write('    endfunction : new\n\n')

        if grps:
            of.write('    function void sample(uvm_reg_data_t data,\n')
            of.write('                         uvm_reg_data_t byte_en,\n')
            of.write('                         bit            is_read,\n')
            of.write('                         uvm_reg_map    map);\n')
            for item in grps:
                of.write('     {0}.sample();\n'.format(item))
            of.write('    endfunction: sample\n\n')

        of.write('    virtual function void build();\n')

        for field in reg.get_bit_fields():
            field_name = self._fix_name(field)
            of.write('      {0} = uvm_reg_field::type_id::create("{0}"'.format(
                     field_name))
            of.write(', , get_full_name());\n')

        dont_test = False
        side_effects = False
        no_reset_test = False

        for field in reg.get_bit_fields():
            size = field.width
            if field.lsb >= reg.width:
                lsb = field.lsb % reg.width
                tok = reg.token
                msg = "{0} has bits that exceed the register width".format(tok)
                LOGGER.warning(msg)
            else:
                lsb = field.lsb

            access = ACCESS_MAP.get(field.field_type, None)
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
                    reset = "".join(["p", field.field_name.upper()])
            else:
                reset = "{0:d}'h{1:x}".format(field.width, field.reset_value)
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
        of.write('  endclass : {0}\n\n'.format(rname))
        of.write('/*!@}*/\n')

    def write_memory(self, reg, dbase, of):

        rname = "mem_{0}_{1}".format(dbase.set_name, reg.token.lower())

        access_types = set()
        for field in reg.get_bit_fields():
            access_types.add(ACCESS_MAP[field.field_type])

        if len(access_types) == 1:
            access = list(access_types)[0]
        else:
            access = "RW"

        of.write("/*! \\class {0}\n".format(rname))
        of.write(" *  \\brief {0}\n".format(reg.description))
        of.write(" *\n * \\addtogroup registers\n")
        of.write(" * * @{\n")
        of.write(" */\n")
        of.write("  class {0} extends uvm_mem;\n\n".format(rname))
        of.write("    `uvm_object_utils({0});\n\n".format(rname))
        of.write('    function new(string name = "{0}");\n'.format(reg.token.lower()))
        num_bytes = reg.width / 8
        of.write('       super.new(name, {0}, {1}, "{2}", UVM_NO_COVERAGE);\n'.format(
                 reg.ram_size / num_bytes, reg.width, access))
        of.write('    endfunction : new\n\n')

        of.write('  endclass : {0}\n\n'.format(rname))
        of.write('/*!@}*/\n')

    def write_db_coverage(self, of, dbase):

        base = dbase.set_name
        of.write("\n\n")
        of.write("class {0}_reg_access_wrapper extends uvm_object;\n".format(base))
        of.write("\n   `uvm_object_utils({0}_reg_access_wrapper)\n".format(base))
        of.write("\n   static int s_num = 0;\n\n")
        of.write("   covergroup ra_cov(string name) with function "
                 "sample(uvm_reg_addr_t addr, bit is_read);\n\n")
        of.write("   option.per_instance = 1;\n")
        of.write("   option.name = name;\n\n")
        of.write("   ADDR: coverpoint addr {\n")
        for reg in dbase.get_all_registers():
            of.write("     bins r_{0} = {{'h{1:x}}};\n".format(reg.token.lower(),
                                                               reg.address))
        of.write("   }\n\n")
        of.write("   RW: coverpoint is_read {\n")
        of.write("      bins RD = {1};\n")
        of.write("      bins WR = {0};\n")
        of.write("   }\n\n")
        of.write("   ACCESS: cross ADDR, RW;\n\n")
        of.write("   endgroup : ra_cov\n\n")
        of.write('   function new(string name = "{0}_reg_access_wrapper");\n'.format(base))
        of.write('      ra_cov = new($sformatf("%s_%0d", name, s_num++));\n')
        of.write('   endfunction : new\n\n')
        of.write('   function void sample(uvm_reg_addr_t offset, bit is_read);\n')
        of.write('      ra_cov.sample(offset, is_read);\n')
        of.write('   endfunction: sample\n\n')
        of.write('endclass : {0}_reg_access_wrapper\n\n'.format(base))


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
        for pos in range(f.lsb, f.msb + 1):
            used_bytes.add(pos / 8)

    # loop through the bytes used by the current field, and make sure they
    # do match any of the bytes used by other fields
    for pos in range(field.lsb, field.msb + 1):
        if (pos / 8) in used_bytes:
            return False
    return True
