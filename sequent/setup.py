import os
import sys

from setuptools import setup
from distutils.sysconfig import get_python_lib
import importlib.util

''' 
is the Python package in your project. It's the top-level folder containing the 
__init__.py module that should be in the same directory as your setup.py file
/-
  |- README.rst
  |- CHANGES.txt
  |- setup.py
  |- dogs 
     |- __init__.py
     |- catcher.py

To create package and upload:

  python setup.py register
  python setup.py sdist
  twine upload -s dist/path/to/gz

'''


def import_setup_utils():
    # load setup utils
    try:
        setup_utils_spec = \
            importlib.util.spec_from_file_location("setup.utils",
                                                   "setup_utils.py")
        setup_utils = importlib.util.module_from_spec(setup_utils_spec)
        setup_utils_spec.loader.exec_module(setup_utils)
    except Exception as err:
        raise RuntimeError("Failed to find setup_utils.py."
                           " Please copy or link.") from err
    return setup_utils


setup_utils = import_setup_utils()
HERE = os.path.abspath(os.path.dirname(__file__))
PACKAGE = "sequent"
NAME = PACKAGE
# METAPATH = os.path.join(HERE, PACKAGE, "__init__.py")
metahost = setup_utils.metahost(PACKAGE)

DESCRIPTION = '''sequent is a programming interface based on eventor providing simple way to write program flows'''
AUTHOR = 'Acrisel Team'
AUTHOR_EMAIL = 'support@acrisel.com'
URL = 'https://github.com/Acrisel/sequent'

metafile = setup_utils.metafile(PACKAGE, 'VERSION')
VERSION = setup_utils.read_version(metahost=metahost, metafile=metafile)

# Warn if we are installing over top of an existing installation. This can
# cause issues where files that were deleted from a more recent Accord are
# still present in site-packages. See #18115.
overlay_warning = False
if "install" in sys.argv:
    lib_paths = [get_python_lib()]
    if lib_paths[0].startswith("/usr/lib/"):
        # We have to try also with an explicit prefix of /usr/local in order to
        # catch Debian's custom user site-packages directory.
        lib_paths.append(get_python_lib(prefix="/usr/local"))
        
    for lib_path in lib_paths:
        existing_path = os.path.abspath(os.path.join(lib_path, PACKAGE))
        if os.path.exists(existing_path):
            # We note the need for the warning here, but present it after the
            # command is run, so it's more likely to be seen.
            overlay_warning = True
            break

setup_info={'name': NAME,
 'version': VERSION,
 'url': URL,
 'author': AUTHOR,
 'author_email': AUTHOR_EMAIL,
 'description': DESCRIPTION,
 'long_description': open("README.rst", "r").read(),
 'license': 'MIT',
 'keywords': 'framework workflow flow program dependency dependencies procedural procedure sequential recovery restart',
 'packages': [PACKAGE],
 'install_requires': [
     'eventor>=5.1.0',
     ],
 'extras_require': {'dev': [], 'test': []},
 'classifiers': ['Development Status :: 5 - Production/Stable',
                 'Environment :: Other Environment',
                 #'Framework :: Project Settings and Operation',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: MIT License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.2',
                 'Programming Language :: Python :: 3.3',
                 'Programming Language :: Python :: 3.4',
                 'Programming Language :: Python :: 3.5',
                 'Programming Language :: Python :: 3.6',
                 'Topic :: Software Development :: Libraries :: Application Frameworks',
                 ]}
setup(**setup_info)


if overlay_warning:
    sys.stderr.write("""

========
WARNING!
========

You have just installed ProjEnv over top of an existing
installation, without removing it first. Because of this,
your install may now include extraneous files from a
previous version that have since been removed from
Accord. This is known to cause a variety of problems. You
should manually remove the

%(existing_path)s

directory and re-install ProjEnv.

""" % {"existing_path": existing_path})
