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
Produces RestructuredText documentation from the definition of the register.
Docutils is used to convert the output to the desired format. Currently, only
HTML is supported now.
"""

import re
import sys
from functools import reduce
from typing import Set, Optional

from regenerate.db import (
    TYPE_TO_SIMPLE_TYPE,
    Register,
    RegProject,
    RegisterSet,
)
from regenerate.extras.token import full_token, in_groups, uvm_name

from docx.shared import Inches, RGBColor
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml

BIT_TABLE = (
    ("Bits", Inches(0.25)),
    ("Type", Inches(0.25)),
    ("Label", Inches(1.25)),
    ("Description", Inches(3.5)),
    ("Default", Inches(0.25)),
    ("Platforms", Inches(0.5)),
)


def reg_addr(register: Register, offset: int) -> str:
    """Returns the register address range"""

    base = register.address + offset
    if register.ram_size > 32:
        return "%04x - %04x" % (base, base + register.ram_size)
    return "%04x" % base


def norm_name(text: str) -> str:
    """Converts the name tolower case, and removes bad characters"""

    if text is not None:
        return text.lower().replace(" ", "-").replace("_", "-")
    return ""


class RegisterDocx:
    "Produces documentation from a register definition"

    def __init__(
            self,
            doc, 
            register: Register,
            project: RegProject = None,
            header=None,
            inst=None,
            highlight=None,
            show_defines: bool = True,
            show_uvm: bool = False,
            decode=None,
            group=None,
            maxlines: int = 9999999,
            dbase: Optional[RegisterSet] = None,
            max_values: int = 24,
            bootstrap: bool = False,
            header_level = 2
    ):
        self.doc = doc
        self.header = header
        self._max_values = max_values
        self._reg = register
        self._highlight = highlight
        self._prj = project
        self._show_defines = show_defines
        self._show_uvm = show_uvm
        self._group = group
        self._inst = inst
        self._maxlines = maxlines
        self._bootstrap = bootstrap
        self._header_level = header_level

        if dbase is None:
            self.reglist = set()
        else:
            self.reglist = set(list(dbase.get_all_registers()))
            self._regset_id = dbase.uuid
            self._regset_name = dbase.name

        if decode:
            try:
                if not isinstance(decode, int):
                    decode = int(decode, 16)
            except ValueError:
                decode = None
        self._decode = decode
        self._db = dbase

    def build(self, text: str = "", use_regs=True) -> str:
        "Returns the definition of the register in RestructuredText format"

        self.str_title()
        self.str_overview()

        if self._reg.ram_size < 32:  # Temporary hack
            self._write_bit_fields()

        if self._show_defines:
            self._write_defines(True, False)

    def tbl_hdr(self, cell, text):

        shading_elm_1 = parse_xml(r'<w:shd {} w:fill="8EAADB"/>'.format(nsdecls('w')))
        cell._tc.get_or_add_tcPr().append(shading_elm_1)

        run = cell.paragraphs[0].add_run()
        run.font.bold = True
        run.text = text

    def refname(self, reg_name: str) -> str:
        """Create a cross reference name from the register"""
        if self._group:
            gname = self._group
        else:
            gname = ""

        if self._inst:
            iname = self._inst
        else:
            iname = ""

        return "%s-%s-%s" % (
            norm_name(iname),
            norm_name(gname),
            norm_name(reg_name),
        )

    def field_ref(self, name: str) -> str:
        """Create a cross reference name from the field"""
        if self._group:
            gname = self._group.name
        else:
            gname = ""

        if self._inst:
            iname = self._inst.name
        else:
            iname = ""

        return "%s-%s-%s-%s" % (
            norm_name(iname),
            norm_name(gname),
            norm_name(self._reg.name),
            norm_name(name),
        )

    def str_title(self) -> None:
        """Create the title in RST format"""
        para = self.doc.add_heading("", self._header_level)
        run = para.add_run(f"REG {reg_addr(self._reg, 0)}h ({self._reg.token})")
        run.bold = True
        run.font.color.rgb = RGBColor(0, 0, 0)


    def str_overview(self, ofile=None) -> None:
        """Return the text overview in RST"""

        data = self._reg.description.encode("utf-8", "replace").decode()

        for t in data.split("\n"):
            self.doc.add_paragraph(t)

    def str_bit_fields(self, ofile=None):
        """Create the bitfield table in RST"""

        records = []
        
        last_index = self._reg.width - 1
        extra_text = []

        footnote = False

        for field in reversed(self._reg.get_bit_fields()):
            data = []
            
            msb = field.msb.resolve()

            if msb != last_index:
                records.append(display_reserved(last_index, msb + 1))

            if field.width == 1:
                data.append(f"{field.lsb}")
            else:
                data.append(f"{msb}:{field.lsb}")

            data.append(TYPE_TO_SIMPLE_TYPE[field.field_type])
            data.append(field.name)
            descr = field.description.strip()
            lines = descr.split("\n")
            platforms = ""
            text = []
            if "Platforms:" in descr:
                for line in lines:
                    if line.startswith("Platforms:"):
                        l = line.replace(","," ").split(":")[1].split()
                        platforms = ", ".join([i.strip() for i in l])
                    else:
                        text.append(line)
                descr = "\n".join(text)

            encoded_descr = descr.encode("utf-8", "replace").rstrip().decode()
            lines = encoded_descr.split("\n")
            data.append(encoded_descr)

            if self._decode:
                val = (self._decode & mask(msb, field.lsb)) >> field.lsb
                if val != field.reset_value:
                    data.append("0x%x" % val)
                else:
                    data.append("0x%x" % val)
            else:
                data.append("0x%x" % field.reset_value)
            data.append(platforms)
                

            last_index = field.lsb - 1
            records.append(data)
        if last_index >= 0:
            records.append(display_reserved(last_index, 0))

        table = self.add_table(1, 6, "Table Grid", BIT_TABLE)
        for d in records:
            row_cells = table.add_row().cells
            for i,d in enumerate(d):
                row_cells[i].text = d

        for ref, name, descr in extra_text:
            sys.stderr.write(".. _%s:\n\n" % ref)
            title = "Description for %s\n" % name
            sys.stderr.write(title)
            sys.stderr.write("+" * len(title))
            sys.stderr.write("\n\n")
            sys.stderr.write(descr)
            sys.stderr.write("\n\n")

#        if footnote:
#            ofile.write(":sup:`*` This field uses the secondary reset.\n\n")


    def add_table(self, rows, cols, style, header_info):

        table = self.doc.add_table(1, 6)
        table.style = style
        hdr_cells = table.rows[0].cells
        for index, info in enumerate(header_info):
            self.tbl_hdr(hdr_cells[index], info[0])
            table.columns[index].width = info[1]
        return table
    
    def _write_bit_fields(self):
        """Write the bitfield section"""

        self.str_bit_fields()

    def _write_defines(self, ofile, use_uvm=True, use_id=True):
        """Write the addresses as defines"""

        para = self.doc.add_heading("", 3)
        run = para.add_run("Addresses")
        run.bold = True
        run.font.color.rgb = RGBColor(0, 0, 0)
        self.str_defines(use_uvm, use_id)

    def str_defines(self, use_uvm=True, use_id=True):
        """Dump out the actual define values"""

        regset_blocks = self._prj.blocks_containing_regset(self._regset_id)

        block_inst_list = []
        for blk in regset_blocks:
            block_inst_list += self._prj.instances_of_block(blk)

        addr_maps_regset_is_in = {}
        
        for addr_map in self._prj.get_address_maps():
            for blk_inst in block_inst_list:
                if blk_inst.uuid in addr_map.block_insts:
                    addr_maps_regset_is_in[addr_map.uuid] = addr_map

        registers = self.find_registers(block_inst_list)
        names = self.expand_register_list(registers)
        
        if not addr_maps_regset_is_in:
            self.doc.add_paragraph(
                "This register has not been mapped into any address space."
            )

        else:
            table = self.doc.add_table(rows=len(names), cols=len(addr_maps_regset_is_in) + 1)
            table.style = "Light Grid"
            self.tbl_hdr(table.rows[0].cells[0], "Register Name")
            for i,amap in enumerate(addr_maps_regset_is_in.values()):
                self.tbl_hdr(table.rows[0].cells[i+1], amap.name)

            records  = []
            for name, addr in names:
                records.append(
                    self._addr_entry(
                        name,
                        addr,
                        addr_maps_regset_is_in,
                    )
                )
            for d in records:
                row_cells = table.add_row().cells
                for i,d in enumerate(d):
                    row_cells[i].text = d


    def _addr_entry(self, regpath, address, addr_maps):
        """Write and address entry"""
        data = []
        data.append(regpath)

        for map_name in addr_maps:
            map_base = self._prj.get_address_base(map_name)
            offset = address + map_base
            data.append(f"0x{offset:x}")
        return data

    def _display_uvm_entry(self, inst, index, ofile):
        """Display the UVM name"""

        name = full_token(
            inst.group, self._reg.token, self._regset_name, index, inst.format
        )
        ofile.write(f"   * - {name}\n")
        name = uvm_name(inst.group, self._reg.token, inst.inst, index)
        ofile.write(f"     - {name}\n")

    def reg_addr(self, blk_inst, brpt, regset_inst, rrpt):
        blk = self._prj.blocks[blk_inst.blkid]
        regset = self._prj.regsets[regset_inst.regset_id]
        rset_width = 1 << regset.ports.address_bus_width

        val = (
            blk_inst.address_base
            + (brpt * blk.address_size)
            + regset_inst.offset
            + (rrpt * rset_width)
            + self._reg.address
        )

        return val

    def find_registers(self, block_inst_list):
        registers = []
        for blk_inst in block_inst_list:
            block = self._prj.blocks[blk_inst.blkid]
            regset_list = [
                rs
                for rs in block.get_regset_insts()
                if rs.regset_id == self._regset_id
            ]
            registers.append((blk_inst, regset_list))
        return registers


    def _token(self, reg):
        regdim = reg.dimension.int_value
        
        if regdim > 1:
            rtoken = f"{reg.token.lower()}[{regdim}]"
        else:
            rtoken = reg.token.lower()
        return rtoken
    
    
    def expand_register_list(self, registers):
        rtoken  = self._token(self._reg)
            
        names = []
        for (blk_inst, regset_list) in registers:
            bname = blk_inst.name
            if blk_inst.repeat > 1:
                for idx in range(0, blk_inst.repeat):
                    for regset in regset_list:
                        rname = regset.name
                        if regset.repeat.resolve() > 1:
                            for ridx in range(0, regset.repeat.resolve()):
                                names.append(
                                    (
                                        f"{bname}[{idx}].{rname}[{ridx}].{rtoken}",
                                        self.reg_addr(
                                            blk_inst, idx, regset, ridx
                                        ),
                                    )
                                )
                        else:
                            names.append(
                                (
                                    f"{bname}[{idx}].{rname}.{rtoken}",
                                    self.reg_addr(blk_inst, idx, regset, 0),
                                )
                            )
            else:
                for regset in regset_list:
                    rname = regset.name
                    if regset.repeat.resolve() > 1:
                        for ridx in range(0, regset.repeat.resolve()):
                            names.append(
                                (
                                    f"{bname}.{rname}[{ridx}].{rtoken}",
                                    self.reg_addr(blk_inst, 0, regset, ridx),
                                )
                            )
                    else:
                        names.append(
                            (
                                f"{bname}.{rname}.{rtoken}",
                                self.reg_addr(blk_inst, 0, regset, 0),
                            )
                        )
        return names


def display_reserved(stop: int, start: int) -> list[str]:
    """
    Return a list of strings, one for each field in the table for
    the reserved field. Only the bit fields change.
    """
    
    if stop == start:
        return [f"{stop}", "RO", "", "reserved", "0x0"]
    
    return [f"{stop}:{start}", "RO", "", "reserved", "0x0"]


def mask(stop: int, start: int) -> int:
    """
    Generate a bit mask with a 1 set in all the positions between
    stop and start
    """
    return reduce(lambda a, b: a | (1 <<b), range(start, stop+1))
