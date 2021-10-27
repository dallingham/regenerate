try:
    from setuputils import setup
except ImportError:
    from distutils.core import setup

import subprocess

label = str(subprocess.check_output(["git", "describe", "--always"]).strip())

label = label.split("'")[1]

print(type(label), label)
VERSION = f"1.9.9 ({label})"

try:
    out = open("regenerate/settings/version.py", "w")
    out.write(f'PROGRAM_NAME = "regenerate"\n')
    out.write(f'PROGRAM_VERSION = "{VERSION}"\n')
    out.close()
except:
    pass

setup(
    name="regenerate",
    version=VERSION,
    license="License.txt",
    author="Donald N. Allingham",
    author_email="dallingham@gmail.com",
    description="Register editor for ASIC/FPGA designs",
    long_description="Allows users to manange registers for "
    "ASIC and FPGA designs. Capable of generating Verilog/SystemVerilog "
    "RTL, UVM register code, test code, C and assembler header files, "
    "and documentation.",
    packages=[
        "regenerate",
        "regenerate.db",
        "regenerate.importers",
        "regenerate.extras",
        "regenerate.settings",
        "regenerate.ui",
        "regenerate.writers",
    ],
    package_data={
        "regenerate": [
            "data/ui/*.ui",
            "data/media/*.svg",
            "data/help/*.rst",
            "data/help/*.html",
            "data/media/*.png",
            "data/extra/*.odt",
            "data/*.*",
            "writers/templates/*",
        ]
    },
    url="https://github.com/dallingham/regenerate",
    scripts=[
        "bin/regenerate",
        "bin/regbuild",
        "bin/regupdate",
        "bin/regxref",
        "bin/regdiff",
        "bin/ipxact2reg",
    ],
    classifiers=[
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
    ],
)
