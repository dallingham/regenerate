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
Imports the exporters. Makes an attempt to load the site_local versions
first. This allows the end user to override the standard version without
fears that it will get overwritten on the next install.

Instead of directly importing the files with the import statement, we
loop through a list of items in the MODULES array, looking at the module
name, and the listed import times from that module. It makes it simpler
to maintain.
"""

from .writer_base import ProjectType, BaseWriter
from .export_info import ExportInfo


EXPORTERS = []
GRP_EXPORTERS = []
PRJ_EXPORTERS = []

IMPORT_PATHS = ["regenerate.writers"]

MODULES = [
    ("verilog", ["Verilog", "Verilog2001", "SystemVerilog"]),
    (
        "address",
        [
            "VerilogDefinesWriter",
            "CDefinesWriter",
            "VerilogParametersWriter",
            "VerilogConstRegPackage",
        ],
    ),
    ("interface", ["InterfaceGen"]),
    ("reg_decode", ["RegDecode"]),
    ("ipxact", ["IpXactWriter"]),
    ("c_test", ["CTest"]),
    ("asm_equ", ["AsmEqu"]),
    ("uvm_reg_block", ["UVMRegBlockRegisters"]),
    ("static_timing", ["Sdc", "Xdc"]),
]


for module in MODULES:
    for mpath in IMPORT_PATHS:
        try:
            fullpath = mpath + "." + module[0]
            a = __import__(fullpath, globals(), locals(), module[1])
            for t, info in a.EXPORTERS:
                if t == ProjectType.REGSET:
                    EXPORTERS.append(info)
                elif t == ProjectType.BLOCK:
                    GRP_EXPORTERS.append(info)
                else:
                    PRJ_EXPORTERS.append(info)
            break
        except ModuleNotFoundError:
            continue
        except ImportError:
            continue
        except AttributeError:
            continue
        except SyntaxError as msg:
            print(f"Could not import {fullpath} ({str(msg)})")
            continue
    else:
        print(f'Could not import the "{module[0]}" module')
