from distutils.core import setup

setup(
    name='regenerate',
    version='0.9.6',
    license='License.txt',
    author='Donald N. Allingham',
    author_email='dallingham@gmail.com',
    description='Register editor for ASIC/FPGA designs',
    long_description='Allows users to manange registers for ASIC and FPGA designs. Capable of generating Verilog RTL, test code, C and assembler header files, and documentation.',
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
    scripts=['bin/regenerate'],
    classifiers=[
        'Operating System :: POSIX',
        'Programming Language :: Python',
        ],
    )

