# Specify defaults for testing
PREFIX=/dls_sw/prod/tools/RHEL5
PYTHON=$(PREFIX)/bin/python2.6
INSTALL_DIR=/dls_sw/work/common/python/test/packages
SCRIPT_DIR=/dls_sw/work/common/python/test/scripts
MODULEVER=0.0

# Override with any release info
-include Makefile.private

# This is run when we type make
dist: setup.py $(wildcard */*.py) dls_edm/helper.pkl
	MODULEVER=$(MODULEVER) $(PYTHON) setup.py bdist_egg
	touch dist
	$(MAKE) -C documentation

# Need to make a pickle object of all the available edm objects on the system
# Check this in as libreadline is not installed on the build server...
dls_edm/helper.pkl: dls_edm/edmObject.py
	$(PYTHON) $<

# Clean the module
clean:
	$(PYTHON) setup.py clean
	-rm -rf build dist *egg-info installed.files dls_edm/helper.pkl
	-find -name '*.pyc' -exec rm {} \;
	$(MAKE) -C documentation clean	

# Install the built egg
install: dist
	$(PYTHON) setup.py easy_install -m \
		--record=installed.files \
		--install-dir=$(INSTALL_DIR) \
		--script-dir=$(SCRIPT_DIR) dist/*.egg
		
