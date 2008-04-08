# -*- coding: utf-8 -*-
"""setup -- setuptools setup file for pyweek6 entry.

$Author$
$Rev: 1016 $
$Date: 2008-04-05 16:22:08 -0500 (Sat, 05 Apr 2008) $
"""

__author__ = "$Author$"
__revision__ = "$Rev: 1016 $"
__version__ = "0.1"
__release__ = '.r'.join((__version__, __revision__[6:-2]))
__date__ = "$Date: 2008-04-05 16:22:08 -0500 (Sat, 05 Apr 2008) $"

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
