# -*- coding: utf-8 -*-
"""setup -- setuptools setup file for pyweek6 entry.

$Author$
$Rev$
$Date$
"""

__author__ = "$Author$"
__revision__ = "$Rev$"
__version__ = "0.1"
__release__ = '.r'.join((__version__, __revision__[6:-2]))
__date__ = "$Date$"

import sys

try:
    import setuptools
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()

from setuptools import setup, find_packages
from setuptools.extension import Extension

setup(
    name = "owyl",
    version = __version__,
    description='Behavior trees for Artificial Intelligence.',
    author='David Eyk',
    author_email='owyl@eykd.net',
    url='http://code.google.com/p/owyl/',

    package_dir = {'': 'src',},
    packages = find_packages('src'),

    install_requires=['Rabbyt==0.8.1',
                      'Cellulose==0.2',
                      'enum',],
    tests_require=['nose',
                   'mocker',
                   'figleaf',
                   'testoob',
                   ],
    test_suite = "nose.collector",

    include_package_data = True,
    )
