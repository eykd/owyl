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

import time

import core

__all__ = ['identity', 'repeatUntilFail', 'repeatUntilSucceed',
           'flip', 'repeatAlways', 'limit']

@core.parent_task
def identity(child, **kwargs):
    """Transparent decorator. Pass yielded values from child unchanged.
    """
    result = None
    child = child(**kwargs)
    while result is None:
        result = (yield child)
    yield result

@core.parent_task
def flip(child, **kwargs):
    """NOT decorator. Pass yielded values from child with the boolean flipped.

    Yielded values of "None" are passed unchanged.
    """
    result = None
    child = child(**kwargs)
    while result is None:
        result = (yield child)
    yield not result

@core.parent_task
def repeatAlways(child, **kwargs):
    """Perpetually iterate over the child, regardless of return value.
    """
    result = None
    while True:
        try:
            visitor = core.visit(child, **kwargs)
        except StopIteration:
            continue
        while result is None:
            try:
                result = (yield visitor.next())
            except StopIteration:
                yield None
                break
        

@core.parent_task
def repeatUntilFail(child, **kwargs):
    """Repeatedly iterate over the child until it fails.

    @keyword final_value: Value to return on failure.
    @type final_value: C{True} or C{False}
    """
    final_value = kwargs.pop('final_value', False)
    result = None
    child = child(**kwargs)
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
    child = child(**kwargs)
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

@core.parent_task
def limit(child, **kwargs):
    """Limit the child to only iterate once every period.

    Otherwise, act as an identity decorator.

    @keyword limit_period: how often to run the child, in seconds.
    """
    nowtime = time.time
    last_run = nowtime()
    period = kwargs.get('limit_period', 1.0)
    result = None
    visitor = core.visit(child, **kwargs)
    while True:
        now = nowtime()
        since_last = now - last_run
        if (since_last) <= period:
            yield None
            continue
        last_run = nowtime()
        result = visitor.next()
        yield result
