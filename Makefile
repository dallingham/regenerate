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
	-mkdir -p $(INSTALL_DIR)
	-mkdir -p $(BIN_DIR)
	install bin/regenerate $(BIN_DIR)
#	sed s@\"\\.\"@$(INSTALL_DIR)@ <bin/regenerate > $(BIN_DIR)/regenerate
	chmod +x $(BIN_DIR)/regenerate
	-mkdir -p $(INSTALL_DIR)
	install *.py $(INSTALL_DIR)
	-mkdir $(INSTALL_DIR)/db
	install regenerate/db/*.py $(INSTALL_DIR)/db
	-mkdir $(INSTALL_DIR)/ui
	install regenerate/ui/*.py regenerate/data/ui/*.ui $(INSTALL_DIR)/ui
	-mkdir $(INSTALL_DIR)/writers
	install regenerate/writers/*.py $(INSTALL_DIR)/writers
	-mkdir $(INSTALL_DIR)/importers
	install regenerate/importers/*.py $(INSTALL_DIR)/importers
	-mkdir $(INSTALL_DIR)/settings
	install regenerate/settings/*.py $(INSTALL_DIR)/settings
	-mkdir $(INSTALL_DIR)/data
	install regenerate/data/* $(INSTALL_DIR)/data
	-mkdir $(INSTALL_DIR)/site_local
	install regenerate/site_local/__init__.py $(INSTALL_DIR)/site_local

clean:
	rm -f *.pyc *.v *.bak *~ *.log

tags:
	etags *.py */*.py
