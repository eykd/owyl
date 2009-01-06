# -*- coding: utf-8 -*-
"""stack -- stack implementation for owyl



Copyright 2008 David Eyk. All rights reserved.

$Author$\n
$Rev: 0 $\n
$Date: 0 $
"""

__author__ = "$Author$"[9:-2]
__revision__ = "$Rev: 0 $"[6:-2]
__date__ = "$Date: Today $"[7:-2]

class EmptyError(Exception): pass

class Stack(list):
    """A list with a push method.
    """
    push = list.append
