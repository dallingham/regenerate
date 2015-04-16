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
"""

EXPORTERS = []
PRJ_EXPORTERS = []

(EXP_CLASS, EXP_TYPE, EXP_DESCRIPTION, EXP_EXT, EXP_ID) = range(5)

from regenerate.db import LOGGER

#-----------------------------------------------------------------------------
#
#  Load the register writers. Currently Verilog-95, Verilog-2001, and
#  SystemVerilog.
#
#-----------------------------------------------------------------------------
try:
    from regenerate.site_local.verilog import Verilog, Verilog2001, SystemVerilog
    LOGGER.info("Found site_local verilog")
except ImportError:
    from verilog import Verilog, Verilog2001, SystemVerilog
EXPORTERS.append((SystemVerilog, ("RTL", "SystemVerilog"),
                  "SystemVerilog files", ".sv", 'rtl-system-verilog'))
EXPORTERS.append((Verilog2001, ("RTL", "Verilog 2001"), "Verilog files", ".v",
                  'rtl-verilog-2001'))
EXPORTERS.append((Verilog, ("RTL", "Verilog 95"), "Verilog files", ".v",
                  'rtl-verilog-95'))

#-----------------------------------------------------------------------------
#
#  UVM Register Exporting
#
#-----------------------------------------------------------------------------
#from uvm import UVM_Registers
#EXPORTERS.append((UVM_Registers, ("Test", "UVM Registers"),
#                  "SystemVerilog files", ".sv", 'uvm-system-verilog'))

#-----------------------------------------------------------------------------
#
#  C code register test case exporting
#
#-----------------------------------------------------------------------------
try:
    from regenerate.site_local.c_test import CTest
    LOGGER.info("Found site_local C test")
except ImportError:
    from c_test import CTest
EXPORTERS.append((CTest, ("Test", "C program"), "C files", ".c", 'test-c'))

#-----------------------------------------------------------------------------
#
#  ASM definition exporting
#
#-----------------------------------------------------------------------------
try:
    from regenerate.site_local.asm_equ import AsmEqu
    LOGGER.info("Found site_local asm_eq")
except ImportError:
    from asm_equ import AsmEqu
EXPORTERS.append((AsmEqu, ("Header files", "Assembler Source"),
                  "Assembler files", ".s", 'headers-asm'))

#-----------------------------------------------------------------------------
#
#  C definition exporting
#
#-----------------------------------------------------------------------------
try:
    from regenerate.site_local.c_defines import CDefines
    LOGGER.info("Found site_local c_defines")
except ImportError:
    from c_defines import CDefines
EXPORTERS.append((CDefines, ("Header files", "C Source"), "C header files",
                  ".h", 'headers-c'))

#-----------------------------------------------------------------------------
#
#  Verilog register headers
#
#-----------------------------------------------------------------------------
try:
    from regenerate.site_local.reg_pkg import VerilogConstRegPackage
    LOGGER.info("Found site_local reg_pkg")
    from regenerate.site_local.reg_pkg_wrap import VerilogRegPackage
    LOGGER.info("Found site_local reg_pkg_wrap")
    PRJ_EXPORTERS.append((VerilogRegPackage, (
        "Headers", "SystemVerilog Symbolic Register Mappings"
    ), "SystemVerilog files", ".sv", 'headers-system-verilog-wrap'))
#-----------------------------------------------------------------------------
#
#  Verilog constant headers
#
#-----------------------------------------------------------------------------
except:
    from reg_pkg import VerilogConstRegPackage

PRJ_EXPORTERS.append((VerilogConstRegPackage,
                      ("Headers", "SystemVerilog Register Constants"),
                      "SystemVerilog files", ".sv", 'headers-system-verilog'))

try:
    from regenerate.site_local.cfg_params import CfgValues
    EXPORTERS.append((CfgValues, ("Test", "Test Configuration Table"),
                      "C files", ".c", 'test-config-table'))
except:
    pass

#-----------------------------------------------------------------------------
#
#  Open Document generator
#
#-----------------------------------------------------------------------------
try:
    from regenerate.site_local.odt_doc import OdtDoc
    LOGGER.info("Found site_local odt_doc")
except ImportError:
    from odt_doc import OdtDoc
EXPORTERS.append((OdtDoc, ("Documentation", "OpenDocument"),
                  "OpenDocument files", ".odt", 'doc-odt'))

try:
    from regenerate.site_local.verilog_defs import VerilogDefines
    LOGGER.info("Found site_local verilog_defs")
except ImportError:
    from verilog_defs import VerilogDefines
EXPORTERS.append((VerilogDefines, ("RTL", "Verilog defines"),
                  "Verilog header files", ".vh", 'rtl-verilog-defines'))

try:
    from regenerate.site_local.verilog_param import VerilogParameters
    LOGGER.info("Found site_local verilog_param")
except ImportError:
    from verilog_param import VerilogParameters
EXPORTERS.append((VerilogParameters, ("RTL", "Verilog parameters"),
                  "Verilog header files", ".vh", 'rtl-verilog-parmaeters'))

try:
    from regenerate.site_local.rst_doc import RstDoc
    LOGGER.info("Found site_local rst_doc")
except ImportError:
    from rst_doc import RstDoc

PRJ_EXPORTERS.append((RstDoc, ("Specification", "RestructuredText"),
                      "RestructuredText files", ".rest", 'spec-rst'))

from uvm_block import UVMBlockRegisters

PRJ_EXPORTERS.append((UVMBlockRegisters, ("Test", "UVM Registers"),
                      "SystemVerilog files", ".sv", 'proj-uvm'))

#-----------------------------------------------------------------------------
#
#  Synthesis constraints
#
#-----------------------------------------------------------------------------
try:
    from regenerate.site_local.sdc import Sdc
    LOGGER.info("Found site_local sdc")
except ImportError:
    from sdc import Sdc
PRJ_EXPORTERS.append((Sdc, ("Synthesis", "SDC Constraints"), "SDC files",
                      ".sdc", 'syn-constraints'))

#-----------------------------------------------------------------------------
#
#  Synthesis constraints
#
#-----------------------------------------------------------------------------
try:
    from regenerate.site_local.spyglass import Spyglass
    LOGGER.info("Found site_local spyglass")
except ImportError:
    from spyglass import Spyglass
PRJ_EXPORTERS.append((Spyglass, ("Spyglass CDC Checking", "SGDC Constraints"),
                      "SGDC files", ".sgdc", 'spy-constraints'))
