#
# To install, two paths need to be set below. 
#
# INSTALL_DIR - path to where the python code and support files will be
#               installed.
#
# BIN_DIR     - path where the executable script will be installedd. This
#               path needs to be in your search path ($PATH)
#
TOP=/home/tools/
BIN_DIR=$(TOP)/tools/bin
PYTHON=/apps/global/python/3.11.5/bin/python3

all:
	@echo "Type 'make install' to install"

install:
	@echo "Must use beta, alpha, or release"

release:
	sh install_release.sh /home/tools/release

beta:
	sh install_release.sh /home/tools/beta

alpha:
	sh install_release.sh /home/tools/alpha

clean:
	rm -f *.pyc *.v *.bak *~ *.log

tags:
	etags *.py */*.py
