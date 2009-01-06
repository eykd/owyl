# -*- coding: utf-8 -*-
"""setup -- setuptools setup file for dyce.

$Author$\n
$Rev$\n
$Date$
"""

__author__ = "$Author$"[9:-2]
__revision__ = "$Rev$"
__date__ = "$Date$"[7:-2]

__version__ = "0.3"
__release__ = '.r'.join((__version__, __revision__))

__description__ = "Randomizer toolkit, with custom dice expression parser."
__long_description__ = """Dyce is a toolkit for rolling dice. It's a friendly wrapper around python's random module.

Dyce also has a mini-language for expressing random number patterns, including common dice notation (i.e. "3d6+5" for rolling thre six-sided dice and adding 5 to the result), making it ideal for easily storing random number patterns in config files.
"""
__classifiers__ = ["Development Status :: 3 - Alpha",
                   "Environment :: Console",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: MIT License",
                   "Natural Language :: English",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python",
                   "Topic :: Games/Entertainment",
                   "Topic :: Games/Entertainment :: Role-Playing",
                   "Topic :: Software Development :: Libraries",]

import sys

try:
    import setuptools
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()

from setuptools import setup, find_packages

INSTALL_REQUIRES=['ConfigObj>=4.5.3', 'yapps']
ZIP_SAFE = True

setup(
    name = "dyce",
    version = __version__,
    author = "David Eyk",
    author_email = "eykd@eykd.net",
    url = "http://code.google.com/p/dyce/",
    description = __description__,
    long_description = __long_description__,
    download_url = "http://code.google.com/p/dyce/downloads/list",
    classifiers = __classifiers__,

    package_dir = {'': 'src',},
    packages = find_packages('src'),

    include_package_data = True,
    exclude_package_data = {'src':['*.c', '*.h',  '*.pyx', '*.pxd', '*.g']},
    #data_files=['src/data',],

    install_requires=INSTALL_REQUIRES,
    zip_safe = ZIP_SAFE,

    test_suite = "nose.collector",
    )

