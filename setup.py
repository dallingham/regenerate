from distutils.core import setup

setup(
    name='regenerate',
    version='0.8',
    license='License.txt',
    author='Donald N. Allingham',
    author_email='dallingham@gmail.com',
    description='Register editor for ASIC/FPGA designs',
    long_description='Here a longer description',
    packages=["regenerate",
              "regenerate.db",
              "regenerate.importers",
              "regenerate.settings",
              "regenerate.ui",
              "regenerate.writers"],
    package_data={'regenerate': ['data/ui/*.ui',
                                 'data/media/*.svg',
                                 'data/media/*.png',
                                 'data/extra/*.odt',
                                 'data/*.*']},
    url="http://code.google.com/p/vlsi-utils/",
    scripts=['bin/regenerate'],
    classifiers=[
        'Operating System :: POSIX',
        'Programming Language :: Python',
        ],
    )

