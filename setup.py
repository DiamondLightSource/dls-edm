from setuptools import setup, find_packages, Extension

# these lines allow the version to be specified in Makefile.private
import os
version = os.environ.get("MODULEVER", "0.0")

setup(
    # install_requires allows you to import a specific version of a module in your scripts 
#   install_requires = ['dls.ca2==1.6'],
    # name of the module
    name = "dls_edm",
    # version: over-ridden by the release script
    version = version,
    packages = ["dls_edm"],
    zip_safe = False,
    package_data = { "": ["*.pkl"] },
    # define console_scripts to be 
    entry_points = {'console_scripts': \
                    ['dls-edm-resize.py = dls_edm.resize:cl_resize',
                     'dls-edm-titlebar.py = dls_edm.titlebar:cl_titlebar',
                     'dls-edm-substitute-embed.py = dls_edm.substitute_embed:cl_substitute_embed',
                     'dls-edm-flip-horizontal.py = dls_edm.flip_horizontal:cl_flip_horizontal']},
    )
