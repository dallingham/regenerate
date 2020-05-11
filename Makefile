#
# To install, two paths need to be set below. 
#
# INSTALL_DIR - path to where the python code and support files will be
#               installed.
#
# BIN_DIR     - path where the executable script will be installedd. This
#               path needs to be in your search path ($PATH)
#
INSTALL_DIR = /home/tools/vlsi-utils/regenerate
BIN_DIR = /home/tools/bin


all:
	@echo "Type 'make install' to install"

install:
	python3 setup.py install --home=/home/tools --force

clean:
	rm -f *.pyc *.v *.bak *~ *.log

tags:
	etags *.py */*.py
