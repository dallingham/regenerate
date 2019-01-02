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

from collections import namedtuple
from writer_base import WriterBase
from regenerate.db import LOGGER
import platform

ExportInfo = namedtuple("ExportInfo", ["obj_class", "type", "description",
                                       "extension", "id"])


EXPORTERS = []
GRP_EXPORTERS = []
PRJ_EXPORTERS = []

IMPORT_PATHS = ("regenerate.site_local", "regenerate.writers")
MODULES = [ 
    ("verilog", ["Verilog", "Verilog2001", "SystemVerilog"]),
    ("verilog_defs", ["VerilogDefines"]),
    ("verilog_param", ["VerilogParameters"]),
    ("reg_pkg", ["VerilogConstRegPackage"]),
    ("decoder", ["AddressDecode"]),
    ("ipxact", ["IpXactWriter"]),
    ("c_test", ["CTest"]),
    ("c_defines", ["CDefines"]),
    ("c_struct", ["CStruct"]),
    ("asm_equ", ["AsmEqu"]),
    ("odt_doc", ["OdtDoc"]),
    ("rst_doc", ["RstDoc"]),
    ("uvm_reg_block", ["UVMRegBlockRegisters"]),
    ("sdc", ["Sdc"]),
    ("spyglass", ["Spyglass"]),
    ]

#-----------------------------------------------------------------------------
#
#  Dynamically load writes for Linux. To get the packaging tools to work, 
#  we must use the stanard import for windows
#
#-----------------------------------------------------------------------------

if platform.system() == 'windows':

    from verilog import Verilog, Verilog2001, SystemVerilog
    from verilog_defs import VerilogDefines
    from verilog_param import VerilogParameters
    from reg_pkg import VerilogConstRegPackage
    from decoder import AddressDecode
    from ipxact import IpXactWriter
    from c_test import CTest
    from c_defines import CDefines
    from asm_equ import AsmEqu
    from odt_doc import OdtDoc
    from rst_doc import RstDoc
    from uvm_reg_block import UVMRegBlockRegisters
    from sdc import Sdc
    from spyglass import Spyglass

for module in MODULES:
    for mpath in IMPORT_PATHS:
        try:
            fullpath = mpath + "." + module[0]
            a = __import__(fullpath, globals(), locals(), module[1])
            for t, info in a.EXPORTERS:
                if t == WriterBase.TYPE_BLOCK:
                    EXPORTERS.append(info)
                elif t == WriterBase.TYPE_GROUP:
                    GRP_EXPORTERS.append(info)
                else:
                    PRJ_EXPORTERS.append(info)
            break
        except ImportError, msg:
            continue
        except AttributeError, msg:
            continue
        except SyntaxError, msg:
            print str(msg)
            continue
    else:
        LOGGER.warning('Cound not import the "{0}" module'.format(module[0]))



