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
        WriterBase.__init__(self, None)
        self.project = project
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

        cfile = open(filename, "w")

        cfile.write(' /* \\defgroup registers Registers */\n')

        cfile.write("package %s_reg_pkg;\n\n" % self.project.short_name)
        cfile.write("  import uvm_pkg::*;\n\n")
        cfile.write('  `include "uvm_macros.svh"\n\n')

        for dbase in self.dblist:

            self.generate_coverage(cfile, dbase)

            for key in dbase.get_keys():
                reg = dbase.get_register(key)
                self.write_register(reg, dbase, cfile)

            self.write_dbase_block(dbase, cfile)

        for group in self.project.get_grouping_list():
            self.write_group_block(group, cfile)

        self.write_toplevel_block(cfile)

        cfile.write('endpackage : %s_reg_pkg\n' % self.project.short_name)
        cfile.close()

    def write_toplevel_block(self, cfile):

        sname = self.project.short_name

        cfile.write("class %s_reg_block extends uvm_reg_block;\n" % sname)
        cfile.write("\n")
        cfile.write("   `uvm_object_utils(%s_reg_block)\n" % sname)
        cfile.write("\n")

        for group_name in self.project.get_grouping_list():
            cfile.write("   %s_group_reg_block %s;\n" %
                        (group_name[0], group_name[0]))

        for addr_key in self.project.get_address_maps():
            name = "%s_map" % addr_key
            cfile.write('   uvm_reg_map %s;\n' % name)

        cfile.write("\n")
        cfile.write('   function new(string name = "%s_reg_block");\n' % sname)
        cfile.write("      super.new(name, "
                    "build_coverage(UVM_CVR_ADDR_MAP));\n")
        cfile.write("   endfunction : new\n")
        cfile.write("\n")
        cfile.write("   function void build();\n")
        cfile.write("      if(has_coverage(UVM_CVR_ADDR_MAP)) begin\n")
        cfile.write("         void'(set_coverage(UVM_CVR_ADDR_MAP));\n")
        cfile.write("      end\n")
        cfile.write("\n")

        endian = "UVM_LITTLE_ENDIAN"

        for addr_key in self.project.get_address_maps():
            name = "%s_map" % addr_key
            base = self.project.get_address_base(addr_key)
            width = self.project.get_address_width(addr_key)
            cfile.write('      %s = create_map("%s", \'h%x, %d, %s);\n' %
                        (name, addr_key, base, width, endian))
        cfile.write("\n")

        for group in self.project.get_grouping_list():
            name = group[0]
            cfile.write('      %s = %s_group_reg_block::type_id::create("%s");\n' %
                        (name, name, name))
            cfile.write('      %s.configure(this, "%s");\n' % (name, name))
            cfile.write("      %s.build();\n" % name)
            for addr_key in self.project.get_address_maps():
                cfile.write("      %s_map.add_submap(%s.%s_map, 0);\n" %
                            (addr_key, name, addr_key))
            cfile.write("\n")

        cfile.write("   endfunction: build\n")
        cfile.write("\n")
        cfile.write("endclass: %s_reg_block\n\n" % sname)

    def write_group_block(self, group, cfile):

        sname = group[0]
        cfile.write("class %s_group_reg_block extends uvm_reg_block;\n" %
                    sname)
        cfile.write("\n")
        cfile.write("   `uvm_object_utils(%s_group_reg_block)\n" % sname)
        cfile.write("\n")

        for group_entry in self.project.get_group_map(group[0]):
            if group_entry.repeat > 1:
                cfile.write("   %s_reg_block %s[%d];\n" %
                            (group_entry.set, group_entry.set,
                             group_entry.repeat))
            else:
                cfile.write("   %s_reg_block %s;\n" %
                            (group_entry.set, group_entry.set))

        for addr_key in self.project.get_address_maps():
            name = "%s_map" % addr_key
            cfile.write('   uvm_reg_map %s;\n' % name)

        cfile.write("\n")
        cfile.write('   function new(string name = "%s_group_reg_block");\n' %
                    sname)
        cfile.write("      super.new(name, build_coverage(UVM_CVR_ADDR_MAP));\n")
        cfile.write("   endfunction : new\n")
        cfile.write("\n")
        cfile.write("   function void build();\n")
        cfile.write("      if(has_coverage(UVM_CVR_ADDR_MAP)) begin\n")
        cfile.write("         void'(set_coverage(UVM_CVR_ADDR_MAP));\n")
        cfile.write("      end\n")
        cfile.write("\n")

        endian = "UVM_LITTLE_ENDIAN"
        for addr_key in self.project.get_address_maps():
            name = "%s_map" % addr_key
            width = self.project.get_address_width(addr_key)
            cfile.write('      %s_map = create_map("%s", 0, %d, %s);\n' %
                        (name, addr_key, width, endian))
        cfile.write("\n")

        for group_entry in self.project.get_group_map(group[0]):
            if group_entry.repeat > 1:
                name = group_entry.set
                cfile.write('      for(int i = 0; i < %d; i++) begin\n' %
                            group_entry.repeat)
                cfile.write('         %s[i] = %s_reg_block::type_id::create("%s[i]");\n' %
                            (name, name, name))
                cfile.write('         %s[i].configure(this, $sformatf("%s[%%0d]", i));\n' %
                            (name, name))
                cfile.write("         %s[i].build();\n" % name)
                for addr_key in self.project.get_address_maps():
                    cfile.write("         %s_map.add_submap(%s[i].%s_map, 'h%x + (i * 'h%x));\n" %
                                (addr_key, name, addr_key, group_entry.offset, group_entry.repeat))
                cfile.write('      end\n')
            else:
                name = group_entry.set
                cfile.write('      %s = %s_reg_block::type_id::create("%s");\n' %
                            (name, name, name))
                cfile.write('      %s.configure(this, "%s");\n' % (name, name))
                cfile.write("      %s.build();\n" % name)
                for addr_key in self.project.get_address_maps():
                    cfile.write("      %s_map.add_submap(%s.%s_map, 'h%x);\n" %
                                (addr_key, name, addr_key, group_entry.offset))
            cfile.write("\n")

        cfile.write("   endfunction: build\n")
        cfile.write("\n")
        cfile.write("endclass: %s_group_reg_block\n\n" % sname)

    def write_dbase_block(self, dbase, cfile):
        cfile.write('  class %s_reg_block extends uvm_reg_block;\n\n'
                    % dbase.module_name)
        cfile.write('    `uvm_object_utils(%s_reg_block)\n\n'
                    % dbase.module_name)

        for addr_key in self.project.get_address_maps():
            name = "%s_map" % addr_key
            cfile.write('    uvm_reg_map %s;\n' % name)

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
                        cfile.write("    bit %s;\n" % name)
                    else:
                        cfile.write("    bit [%d:0] %s;\n"
                                    % (field.width - 1, name))

        for key in dbase.get_keys():
            reg = dbase.get_register(key)
            rname = "reg_%s_%s" % (dbase.module_name, reg.token.lower())
            cfile.write("    %s %s;\n" % (rname, reg.token.lower()))

        mod = dbase.module_name
        cfile.write('    %s_reg_access_wrapper %s_access_cg;\n\n' % (mod, mod))
        cfile.write('\n')
        cfile.write('    function new(string name = "%s_access_cg");\n' % mod)
        cfile.write('      super.new(name,build_coverage(UVM_CVR_ALL));\n')
        cfile.write('    endfunction\n\n')

        cfile.write('    virtual function void build();\n')

        cfile.write('       if(has_coverage(UVM_CVR_ALL)) begin\n')
        cfile.write('          %s_access_cg = %s_reg_access_wrapper::type_id::create("%s_access_cg");\n'
                    % (mod, mod, mod))
        cfile.write("          void'(set_coverage(UVM_CVR_ALL));\n")
        cfile.write('       end\n')

        for key in dbase.get_keys():
            reg = dbase.get_register(key)
            rname = "reg_%s_%s" % (dbase.module_name, reg.token.lower())

            cfile.write('      %s = %s::type_id::create("%s", , get_full_name());\n' %
                        (reg.token.lower(), rname, reg.token.lower()))
            for field_key in reg.get_bit_field_keys():
                field = reg.get_bit_field(field_key)
                if field.reset_type == BitField.RESET_PARAMETER:
                    if field.reset_parameter:
                        name = field.reset_parameter
                    else:
                        name = "p%s" % field.field_name.upper()
                    cfile.write('      %s.%s = %s;\n' % (reg.token.lower(),
                                                         name, name))

            cfile.write('      %s.configure(this);\n' % reg.token.lower())
            cfile.write('      %s.build();\n' % reg.token.lower())
            if reg.do_not_generate_code:
                cfile.write('      //%s.add_hdl_path_slice("path to register", 0, <width> );\n\n'
                            % reg.token.lower())
            else:
                for key in reg.get_bit_field_keys():
                    field = reg.get_bit_field(key)
                    cfile.write('      %s.add_hdl_path_slice("r%02x_%s", %d, %d );\n'
                                % (
                                    reg.token.lower(), reg.address,
                                    self._fix_name(field),
                                    field.start_position, field.width))
                    cfile.write("\n")

        cfile.write("\n")

        for addr_key in self.project.get_address_maps():
            name = "%s_map" % addr_key

            cfile.write('      %s = create_map("%s", \'h0, %d, UVM_LITTLE_ENDIAN, 1);\n\n' %
                        (name, name, self.project.get_address_width(addr_key)))
            for key in dbase.get_keys():
                reg = dbase.get_register(key)
                cfile.write('      %s.add_reg(%s, \'h%04x, "RW");\n' %
                            (name, reg.token.lower(), reg.address))
            cfile.write('\n')

        cfile.write('      lock_model();\n')
        cfile.write('    endfunction : build\n')

        cfile.write('    function void sample(uvm_reg_addr_t offset, '
                    'bit is_read, uvm_reg_map  map);\n')
        cfile.write('       if(get_coverage(UVM_CVR_ALL)) begin\n')
        cfile.write('          if(map.get_name() == "default_map") begin\n')
        cfile.write('             %s_access_cg.sample(offset, is_read);\n' %
                    dbase.module_name)
        cfile.write('          end\n')
        cfile.write('       end\n')
        cfile.write('    endfunction: sample\n\n')

        cfile.write('  endclass : %s_reg_block\n\n' % dbase.module_name)

    def write_register(self, reg, dbase, cfile):

        rname = "reg_%s_%s" % (dbase.module_name, reg.token.lower())

        cfile.write("/*! \\class %s\n" % rname)
        cfile.write(" *  \\brief %s\n" % reg.description)
        cfile.write(" *\n * \\addtogroup registers\n")
        cfile.write(" * * @{\n")
        cfile.write(" */\n")
        cfile.write("  class %s extends uvm_reg;\n\n" % rname)
        cfile.write("    `uvm_object_utils(%s);\n\n" % rname)
        field_keys = reg.get_bit_field_keys()
        field_list = []
        for key in field_keys:
            field = reg.get_bit_field(key)
            cfile.write("    uvm_reg_field %s;\n" % self._fix_name(field))
            if field.reset_type == BitField.RESET_PARAMETER:
                field_list.append(field)

        for field in field_list:
            if field.reset_parameter:
                name = field.reset_parameter
            else:
                name = "p%s" % field.field_name.upper()

            if field.width == 1:
                cfile.write("    bit %s = 1'b0;\n" % name)
            else:
                cfile.write("    bit [%d:0] %s = '0;\n" % (field.width - 1,
                                                           name))

        grps = set()

        for key in field_keys:
            field = reg.get_bit_field(key)
            if field.values:
                n = self._fix_name(field)
                grps.add("cov_%s" % n)
                cfile.write("\n      covergroup cov_%s;\n" % n)
                cfile.write("         option.per_instance = 1;\n")
                cfile.write("         %s: coverpoint %s.value {\n" %
                            (n.upper(), n.lower()))
                for value in field.values:
                    cfile.write("            bins bin_%s = {'h%x};\n" %
                                self.mk_coverpt(value))
                cfile.write("      }\n")
                cfile.write("      endgroup : cov_%s\n" % n)

        cfile.write('\n    function new(string name = "%s");\n' %
                    reg.token.lower())
        if grps:
            cfile.write('       super.new(name, %d, ' % reg.width)
            cfile.write('build_coverage(UVM_CVR_FIELD_VALS));\n')
            for item in grps:
                cfile.write('       %s = new;\n' % item)
        else:
            cfile.write('      super.new(name, %d' % reg.width)
            cfile.write(', UVM_NO_COVERAGE);\n')

        cfile.write('    endfunction : new\n\n')

        if grps:
            cfile.write('\n')
            cfile.write('    function void sample(uvm_reg_data_t data,\n')
            cfile.write('                         uvm_reg_data_t byte_en,\n')
            cfile.write('                         bit            is_read,\n')
            cfile.write('                         uvm_reg_map    map);\n')
            for item in grps:
                cfile.write('     %s.sample();\n' % item)
            cfile.write('    endfunction: sample\n\n')

        cfile.write('    virtual function void build();\n')

        field_keys = reg.get_bit_field_keys()

        for key in field_keys:
            field = reg.get_bit_field(key)
            cfile.write('      %s = uvm_reg_field::type_id::create("%s"' %
                        (self._fix_name(field), self._fix_name(field)))
            cfile.write(', , get_full_name());\n')
        cfile.write("\n")

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
            access = access_map[field.field_type]

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

            cfile.write('      %s.configure(this, %d, %d, "%s", %d, %s, %d, %d, %d);\n' %
                        (self._fix_name(field), size, lsb, access, volatile,
                         reset, has_reset, is_rand, ind_access))

        if reg.do_not_test:
            cfile.write('      uvm_resource_db #(bit)::set({"REG::", '
                        'get_full_name()}, "NO_REG_HW_RESET_TEST", 1);\n')
        if reg.do_not_test:
            cfile.write('      uvm_resource_db #(bit)::set({"REG::", '
                        'get_full_name()}, "NO_REG_BIT_BASH_TEST", 1);\n')

        cfile.write('\n      reset();\n')
        cfile.write('\n    endfunction : build\n\n')
        cfile.write('  endclass : %s\n\n' % rname)
        cfile.write('/*!@}*/\n')

    def generate_coverage(self, cfile, dbase):

        base = dbase.module_name
        cfile.write("\n\n")
        cfile.write("class %s_reg_access_wrapper extends uvm_object;\n" % base)
        cfile.write("\n   `uvm_object_utils(%s_reg_access_wrapper)\n\n" % base)
        cfile.write("\n   static int s_inst_num = 0;\n\n")
        cfile.write("   covergroup ra_cov(string name) with function sample(uvm_reg_addr_t addr, bit is_read);\n\n")
        cfile.write("   option.per_instance = 1;\n")
        cfile.write("   option.name = name;\n\n")
        cfile.write("   ADDR: coverpoint addr {\n")
        for key in dbase.get_keys():
            reg = dbase.get_register(key)
            cfile.write("     bins r_%s = {'h%x};\n" % (reg.token.lower(),
                                                        reg.address))
        cfile.write("   }\n\n")
        cfile.write("   RW: coverpoint is_read {\n")
        cfile.write("      bins RD = {1};\n")
        cfile.write("      bins WR = {0};\n")
        cfile.write("   }\n\n")
        cfile.write("   ACCESS: cross ADDR, RW;\n\n")
        cfile.write("   endgroup : ra_cov\n\n")
        cfile.write('   function new(string name = "%s_reg_access_wrapper");\n' %
                    base)
        cfile.write('      ra_cov = new($sformatf("%s_%0d", name, s_inst_num++));\n')
        cfile.write('   endfunction : new\n\n')
        cfile.write('   function void sample(uvm_reg_addr_t offset, bit is_read);\n')
        cfile.write('      ra_cov.sample(offset, is_read);\n')
        cfile.write('   endfunction: sample\n')
        cfile.write('endclass : %s_reg_access_wrapper\n\n' % base)


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
