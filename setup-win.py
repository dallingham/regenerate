
from setuptools import setup
import py2exe

import os
import glob
    
__import__('gtk')
__import__('jinja2')
__import__('docutils')


setup_dict = dict(
    name='regenerate',
    version='1.0.0',
    license='License.txt',
    author='Donald N. Allingham',
    author_email='dallingham@gmail.com',
    description='Register editor for ASIC/FPGA designs',
    long_description='Allows users to manange registers for '
    'ASIC and FPGA designs. Capable of generating Verilog '
    'RTL, test code, C and assembler header files, and documentation.',
    packages=[
        "regenerate",
        "regenerate.db",
        "regenerate.importers",
        "regenerate.extras",
        "regenerate.settings",
        "regenerate.ui",
        "regenerate.writers"
        ],
    package_dir={
        "regenerate" : "regenerate",
    },
    package_data={
        'regenerate' : [
            "data/ui/*.ui",
            "data/media/*",
            "data/help/*.rst",
            "data/extra/*",
            "data/*.*",
            "writers/templates/*"
        ]
    },
    include_package_data=True,
    url="https://github.com/dallingham/regenerate",
    scripts=[
        "bin/regenerate",
        "bin/regbuild",
        "bin/regupdate",
        "bin/regxref",
        "bin/regdiff"
    ],
    classifiers=[
        'Operating System :: POSIX', 'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)'
    ], 
    windows=[
        {
            "script" : "bin/regenerate",
            "icon_resources" : [(1, "regenerate/data/media/flop.ico")]
        }
    ],
    options={
        'py2exe': { 
            'includes' : 'cairo, pango, pangocairo, atk, gobject, gio, gtk.keysyms, jinja2',
            'skip_archive' : True,
            'dll_excludes': [
                             'MSVCP90.dll',
                             'api-ms-win-core-string-l1-1-0.dll',
                             'api-ms-win-core-registry-l1-1-0.dll',
                             'api-ms-win-core-errorhandling-l1-1-1.dll',
                             'api-ms-win-core-string-l2-1-0.dll',
                             'api-ms-win-core-profile-l1-1-0.dll',
                             'api-ms-win-core-processthreads-l1-1-2.dll',
                             'api-ms-win-core-libraryloader-l1-2-1.dll',
                             'api-ms-win-core-file-l1-2-1.dll',
                             'api-ms-win-security-base-l1-2-0.dll',
                             'api-ms-win-eventing-provider-l1-1-0.dll',
                             'api-ms-win-core-heap-l2-1-0.dll',
                             'api-ms-win-core-libraryloader-l1-2-0.dll',
                             'api-ms-win-core-localization-l1-2-1.dll',
                             'api-ms-win-core-sysinfo-l1-2-1.dll',
                             'api-ms-win-core-synch-l1-2-0.dll',
                             'api-ms-win-core-heap-l1-2-0.dll']
            }
        
        },
    )

setup(**setup_dict)
