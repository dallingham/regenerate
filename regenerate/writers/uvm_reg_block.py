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
from regenerate.writers.writer_base import WriterBase, ExportInfo
import time
import os
from jinja2 import Environment

#
# Map regenerate types to UVM type strings
#
ACCESS_MAP = {
    BitField.TYPE_READ_ONLY: "RO",
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
    BitField.TYPE_WRITE_1_TO_CLEAR_SET_CLR: "W1C",
    BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S: "W1C",
    BitField.TYPE_WRITE_1_TO_CLEAR_SET_1S_1: "W1C",
    BitField.TYPE_WRITE_1_TO_CLEAR_LOAD: "W1C",
    BitField.TYPE_WRITE_1_TO_CLEAR_LOAD_1S: "W1C",
    BitField.TYPE_WRITE_1_TO_CLEAR_LOAD_1S_1: "W1C",
    BitField.TYPE_WRITE_1_TO_SET: "W1S",
    BitField.TYPE_WRITE_ONLY: "WO",
    BitField.TYPE_READ_WRITE_PROTECT: "RW",
    BitField.TYPE_READ_WRITE_PROTECT_1S:  "RW",
    }


class UVMRegBlockRegisters(WriterBase):
    """
    Generates a SystemVerilog package representing the registers in
    the UVM format.
    """

    # Provide a mapping reserved SystemVerilog keywords to alternatives
    # to prevent syntax errors in the generated code.

    REMAP_NAME = set(["always", "assign", "automatic", "begin", "case", 
                      "casex", "casez", "class", "do", "package", "set",
                      "cell", "config", "deassign", "default", "defparam",
                      "design", "disable","edge", "else", "end", "endcase",
                      "endconfig", "endfunction", "endgenerate", "endmodule",
                      "endprimitive", "endspecify", "endtable", "endtask",
                      "event", "for", "force", "forever", "fork", "function",
                      "generate", "genvar", "if", "ifnone", "incdir", 
                      "initial", "inout", "input", "instance", "join",
                      "liblist", "library", "localparam", "macromodule",
                      "module", "negedge", "output", "parameter", "posedge",
                      "primitive", "reg", "release", "repeat", "scalared",
                      "signed", "specify", "specparam", "strength", "table",
                      "task", "tri", "tri0", "tri1", "triand", "wand", 
                      "trior", "wor", "trireg", "unsigned", "use", "vectored",
                      "wait", "while", "wire", "bit"]) 
    
    def __init__(self, project, dblist):
        """
        Initialize the object. At the current time, only little endian is
        supported by the package
        """
        WriterBase.__init__(self, project, None)
        self.dblist = dblist

    def fix_name(self, field):
        """
        Creates a name from the field. If there are any spaces (which the
        UI should prevent), the are converted to underscores. We then replace
        name names that are reserved SystemVerilog words with alternatives.
        """
        name = "_".join(field.field_name.lower().split())

        if name in self.REMAP_NAME:
            return "%s_field" % name
        else:
            return name

    def fix_reg_name(self, reg):
        """
        Creates a name from the register. If there are any spaces (which the
        UI should prevent), the are converted to underscores. We then replace
        name names that are reserved SystemVerilog words with alternatives.
        """
        name = "_".join(reg.token.lower().split())

        if name in self.REMAP_NAME:
            return "%s_reg" % name
        else:
            return name

    def uvm_address_maps(self):
        return [d for d in self._project.get_address_maps() if not d.uvm]

    def build_map_name_to_groups(self):
        map2grp = {}
        all_groups = [grp.name for grp in self._project.get_grouping_list()]

        for data in self.uvm_address_maps():
            name = data.name
            map2grp[name] = self._project.get_address_map_groups(name)
            if not map2grp[name]:
                map2grp[name] = all_groups
        return map2grp

    def _build_group_maps(self):
        group_maps = {}
        for group in self._project.get_grouping_list():
            in_maps = set()
            for addr_map in self.uvm_address_maps():
                map_list = self._project.get_address_map_groups(addr_map.name)
                if not map_list or group.name in map_list:
                    in_maps.add(addr_map.name)
            if in_maps:
                group_maps[group] = in_maps
        return group_maps

    def _used_maps(self):
        return set([addr_map.name for addr_map in self.uvm_address_maps()])

    def write(self, filename):
        """
        Write the data to the file as a SystemVerilog package. This includes
        a block of register definitions for each register and the associated
        container blocks.
        """
        
        group_maps = self._build_group_maps()
        name = self._project.short_name
        dirpath = os.path.dirname(__file__)

        env = Environment(trim_blocks=True, lstrip_blocks=True)

        env.filters['remove_no_uvm'] = remove_no_uvm

        template_file = os.path.join(dirpath, "templates", 
                                     "uvm_reg_block.template")
        template = env.from_string(file(template_file).read())

        used_dbs = self.get_used_databases()
        

        with open(filename, "w") as of:
            of.write(template.render(project=self._project, dblist=used_dbs,
                                     individual_access=individual_access,
                                     ACCESS_MAP=ACCESS_MAP, 
                                     db_grp_maps=self.get_db_groups(),
                                     group_maps = self._build_group_maps(),
                                     fix_name=self.fix_name,
                                     fix_reg=self.fix_reg_name,
                                     use_new=False,
                                     used_maps = self._used_maps(),
                                     map2grp = self.build_map_name_to_groups(),
                                     current_date=time.strftime("%B %d, %Y")
                                     ))

    def get_db_groups(self):
        data_set = []
        group_maps = self._build_group_maps()
        for dbase in self.get_used_databases():
            for group in self._project.get_grouping_list():
                used = set()
                for grp in group.register_sets:
                    if grp.set == dbase.set_name and grp.set not in used:
                        used.add(grp.set)
                        if group in group_maps:
                            data_set.append((dbase, group, group_maps[group]))
        return data_set

    def get_used_databases(self):

        grp_set = set()
        maps = self._build_group_maps()
        for key in maps:
            if maps[key]:
                grp_set.add(key.name)

        used_sets = set([])
        for group in self._project.get_grouping_list():
            if group.name in grp_set: 
                for reg_sets in group.register_sets:
                    used_sets.add(reg_sets.set)

        return set([db for db in self.dblist if db.set_name in used_sets])

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
            return 0
    return 1

def remove_no_uvm(s):
    return [r for r in s if r.do_not_use_uvm is False]


EXPORTERS = [
    (WriterBase.TYPE_PROJECT, ExportInfo(UVMRegBlockRegisters, ("Test", "UVM Registers"),
                                         "SystemVerilog files", ".sv", 'proj-uvm'))
]
