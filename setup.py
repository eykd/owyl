# -*- coding: utf-8 -*-
"""setup -- setuptools setup file for Owyl.

$Author$\n
$Rev$\n
$Date$
"""

__author__ = "$Author$"[9:-2]
__revision__ = "$Rev$"
__date__ = "$Date$"[7:-2]

__version__ = "0.2.2"
__release__ = '.r'.join((__version__, __revision__))

__description__ = "The goal of Owyl: provide a fast and flexible Behavior Tree library implemented in python."
__long_description__ = """You have Pyglet. You've got Rabbyt. But who do your sprites go to for advice? Owyl, of course.

The goal of Owyl: provide a fast and flexible Behavior Tree library implemented in python. For more information on Behavior Trees, see the articles at http://aigamedev.com/hierarchical-logic

"""
__classifiers__ = ["Development Status :: 3 - Alpha",
                   "Environment :: Console",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: BSD License",
                   "Natural Language :: English",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python",
                   "Topic :: Games/Entertainment",
                   "Topic :: Scientific/Engineering :: Artificial Intelligence",
                   "Topic :: Software Development :: Libraries",]

import sys

try:
    import setuptools
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()

from setuptools import setup, find_packages

INSTALL_REQUIRES=[]
ZIP_SAFE = True

setup(
    name = "owyl",
    version = __version__,
    author = "David Eyk",
    author_email = "eykd@eykd.net",
    url = "http://code.google.com/p/owyl/",
    description = __description__,
    long_description = __long_description__,
    download_url = "http://code.google.com/p/owyl/downloads/list",
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

