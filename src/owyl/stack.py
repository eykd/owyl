# -*- coding: utf-8 -*-
"""stack -- stack implementation for owyl



Copyright 2008 David Eyk. All rights reserved.

$Author$\n
$Rev$\n
$Date$
"""

__author__ = "$Author$"[9:-2]
__revision__ = "$Rev$"[6:-2]
__date__ = "$Date$"[7:-2]

__all__ = "EmptyError Stack".split()

EmptyError = IndexError

class Stack(list):
    """A list with a push method.
    """
    push = list.append
