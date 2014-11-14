from distutils.core import setup

setup(
    name='regenerate',
    version='0.9.7',
    license='License.txt',
    author='Donald N. Allingham',
    author_email='dallingham@gmail.com',
    description='Register editor for ASIC/FPGA designs',
    long_description='Allows users to manange registers for '
    'ASIC and FPGA designs. Capable of generating Verilog '
    'RTL, test code, C and assembler header files, and documentation.',
    packages=["regenerate",
              "regenerate.db",
              "regenerate.importers",
              "regenerate.extras",
              "regenerate.settings",
              "regenerate.ui",
              "regenerate.writers"],
    package_data={'regenerate': ['data/ui/*.ui',
                                 'data/media/*.svg',
                                 'data/help/*.rst',
                                 'data/media/*.png',
                                 'data/extra/*.odt',
                                 'data/*.*']},
    url="https://github.com/dallingham/regenerate",
    scripts=["bin/regenerate",
             "bin/regbuild",
             "bin/regupdate",
             "bin/regxref",
             "bin/regdiff"],
    classifiers=[
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)'
        ],
    )
