# -*- coding: utf-8 -*-
"""decorators -- decorators for owyl behavior trees.



Copyright 2008 David Eyk. All rights reserved.

$Author$\n
$Rev$\n
$Date$
"""

__author__ = "$Author$"[9:-2]
__revision__ = "$Rev$"[6:-2]
__date__ = "$Date$"[7:-2]

import core

__all__ = ['identity', 'repeatUntilFail', 'repeatUntilSucceed']

@core.parent_task
def identity(child, **kwargs):
    """Transparent decorator. Pass yielded values from child unchanged.
    """
    result = None
    while result is None:
        result = (yield child)
    yield result

@core.parent_task
def flip(child, **kwargs):
    """NOT decorator. Pass yielded values from child with the boolean flipped.

    Yielded values of "None" are passed unchanged.
    """
    result = None
    while result is None:
        result = (yield child)
    yield not result


@core.parent_task
def repeatUntilFail(child, **kwargs):
    """Repeatedly iterate over the child until it fails.

    @keyword final_value: Value to return on failure.
    @type final_value: C{True} or C{False}
    """
    final_value = kwargs.pop('final_value', False)
    result = None
    while result is None:
        try:
            result = (yield child)
            if result is False:
                break
            else:
                yield None # Yield to other tasks.
                result = None
        except StopIteration:
            result = None
    yield final_value

@core.parent_task
def repeatUntilSucceed(child, **kwargs):
    """Repeatedly iterate over the child until it succeeds.

    @keyword final_value: Value to return on failure.
    @type final_value: C{True} or C{False}
    """
    final_value = kwargs.pop('final_value', True)
    result = None
    while result is None:
        try:
            result = (yield child)
            if result is True:
                break
            else:
                yield None # Yield to other tasks.
                result = None
        except StopIteration:
            result = None
    yield final_value
