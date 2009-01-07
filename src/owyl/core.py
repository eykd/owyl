# -*- coding: utf-8 -*-
"""core -- core behaviors for Owyl.

Copyright 2008 David Eyk. All rights reserved.

$Author$\n
$Rev$\n
$Date$
"""

__author__ = "$Author$"[9:-2]
__revision__ = "$Rev$"[6:-2]
__date__ = "$Date$"[7:-2]

import sys

try:
    from mx.Stack import Stack, EmptyError
except ImportError:
    from stack import Stack, EmptyError

RETURN_VALUES = (True, False, None)

__all__ = ['task', 'visit', 'succeed', 'fail', 'succeedAfter', 'failAfter',
           'sequence', 'selector', 'parallel', 'PARALLEL_SUCCESS',
           'throw', 'catch']

def task(func):
    """Task decorator.

    Decorate a generator function to produce a re-usable generator
    factory for the given task.
    """
    def initTask(**initkwargs):
        def makeIterator(**runkwargs):
            runkwargs.update(initkwargs)
            iterator = func(**runkwargs)
            return iterator
        makeIterator.__name__ = func.__name__
        makeIterator.__doc__ = func.__doc__
        return makeIterator
    initTask.__doc__ = func.__doc__
    initTask.__name__ = func.__name__
    return initTask

def parent_task(func):
    """Parent task decorator.

    A parent task is a task that accepts children.

    Decorate a generator function to produce a re-usable generator
    factory for the given task.
    """
    def initTask(*children, **initkwargs):
        def makeIterator(**runkwargs):
            runkwargs.update(initkwargs)
            iterator = func(*children, **runkwargs)
            return iterator
        makeIterator.__name__ = func.__name__
        makeIterator.__doc__ = func.__doc__
        return makeIterator
    initTask.__doc__ = func.__doc__
    initTask.__name__ = func.__name__
    return initTask

def visit(tree, **kwargs):
    """Iterate over a tree of nested iterators.

    Apply the U{Visitor
    Pattern<http://en.wikipedia.org/wiki/Visitor_pattern>} to a tree
    of nested iterators. Iterators should yield True, False, None, or
    a child iterator. Values of True or False are passed back to the
    parent iterator. A value of None is silently ignored, and the
    current iterator will be queried again on the next pass.

    The visitor will yield None until the tree raises StopIteration,
    upon which the visitor will yield the last value yielded by the
    tree, and terminate itself with StopIteration.

    The visitor is essentially a micro-scheduler for a Behavior Tree
    implemented as a tree of nested iterators. For more information,
    see the discussion at
    U{http://aigamedev.com/programming-tips/scheduler}.
    """
    s = Stack()
    return_values = RETURN_VALUES

    current, cur_name = (tree(**kwargs), tree.__name__)
    #print "Iterating over %s" % (cur_name, )
    send_value = None
    send_ok = False
    while True:
        try:
            if send_ok:
                #print "Passing %s to %s" % (send_value, cur_name)
                child = current.send(send_value)
                send_value = None
                send_ok = False
            else:
                child = current.next()

            if child in return_values:
                send_value = child
                #print "%s returned %s" % (cur_name, child)
                yield send_value
            else:
                # Descend into child node
                s.push((current, cur_name))
                current, cur_name = (child(**kwargs), child.__name__)
                #print "Descending into %s" % (cur_name,)
                
        except StopIteration:
            try:
                current, cur_name = s.pop()
                #print "Ascending back to %s" % (cur_name,)
                send_ok = True
            except EmptyError:
                raise StopIteration
        except Exception, e:
            exc = e.__class__
            try:
                # Give the parent task a chance to handle the exception.
                current, cur_name = s.pop()
                current.throw(exc, e.message, sys.exc_info()[2])()
            except EmptyError, e:
                # Give up if the exception has propagated all the way
                # up the tree:
                raise e
        
@task
def succeed(**kwargs):
    """Always succeed.
    """
    yield True

@task
def fail(**kwargs):
    """Always fail.
    """
    yield False

@task
def succeedAfter(**kwargs):
    """Succeed after a given number of iterations.

    Yields 'None' 'after' times.

    @keyword after: How many iterations to succeed after.
    @type after: int
    """
    after = kwargs.pop('after', 1)
    for x in xrange(after):
        yield None
    yield True

@task
def failAfter(**kwargs):
    """Fail after a given number of iterations.

    Yields 'None' 'after' times.

    @keyword after: How many iterations to fail after.
    @type after: int
    """
    after = kwargs.pop('after', 1)
    for x in xrange(after):
        yield None
    yield False


@parent_task
def sequence(*children, **kwargs):
    """Run tasks in sequence until one fails.

    The sequence will run each task in sequence until one fails,
    returning a failure. If all fail, returns a success.

    For more information, see the discussion at
    U{http://aigamedev.com/hierarchical-logic/sequence}.

    @param children: tasks to run in sequence as children.
    """
    final_value = True
    for child in children:
        result = yield child
        if not result and result is not None:
            final_value = False
            break
        
    yield final_value

@parent_task
def selector(*children, **kwargs):
    """Run tasks in sequence until one succeeds.

    The selector will run each task in sequence until one succeeds,
    returning a success. If all fail, returns a failure.

    For more information, see the discussion at
    U{http://aigamedev.com/hierarchical-logic/selector}.

    @param children: child tasks to select from.
    """
    final_value = False
    for child in children:
        result = (yield child)
        if result:
            final_value = True
            break
        
    yield final_value


class Enum(object):
    """Enum/namespace class. Cannot be implemented. 

    Subclass and add class variables.
    """
    def __init__(self): 
        raise NotImplementedError, "_Enum class object. Do not instantiate."
    
class PARALLEL_SUCCESS(Enum):
    """Success policy enumerator for parallel behavior.

    C{REQUIRE_ALL}: All child tasks must succeed.
    C{REQUIRE_ONE}: Only one child task must succeed.
    """
    REQUIRE_ALL = "ALL"
    REQUIRE_ONE = "ONE"

@parent_task
def parallel(*children, **kwargs):
    """Run tasks in parallel until the success policy is fulfilled or broken.

    If the success policy is met, return a success. If the policy is
    broken, return a failure.

    For more information, see the discussion at
    U{aigamedev.com/hierarchical-logic/parallel}.

    @param children: tasks to run in parallel as children.

    @keyword policy: The success policy. All must succeed, 
                   or only one must succeed.
    @type policy: C{PARALLEL_SUCCESS.REQUIRE_ALL} or 
                  C{PARALLEL_SUCCESS.REQUIRE_ONE}.
    """
    return_values = (True, False)
    policy = kwargs.pop('policy', PARALLEL_SUCCESS.REQUIRE_ONE)
    all_must_succeed = (policy == PARALLEL_SUCCESS.REQUIRE_ALL)
    visits = [visit(arg, **kwargs) for arg in children]
    final_value = True
    while True:
        try:
            # Run one step on each child per iteration.
            for child in visits:
                result = child.next()
                if result in return_values:
                    if not result and all_must_succeed:
                        final_value = False
                        break
                    elif result and not all_must_succeed:
                        final_value = True
                        break
                    else:
                        final_value = result
                
        except StopIteration:
            break
        except EmptyError:
            break
    yield final_value

@task
def throw(**kwargs):
    """Throw (raise) an exception.

    @keyword throws: An Exception to throw.
    @type throws: C{Exception}

    @keyword throws_message: Text to instantiate C{throws} with.
    @type throws_message: C{str}
    """
    throws = kwargs.pop('throws', Exception)
    throws_message = kwargs.pop('throws_message', '')
    class gen(object):
        def __iter__(self):
            return self
        def next(self):
            raise throws(throws_message)
    return gen()

@parent_task
def catch(child, **kwargs):
    """Catch a raised exception from child and run an alternate branch.

    Note: this will not catch exceptions raised in the branch.

    @keyword caught: An Exception to catch.
    @type caught: C{Exception}

    @keyword branch: An alternate tree to visit when caught.
    """
    caught = kwargs.pop('caught', Exception)
    branch = kwargs.pop('branch', fail())
    
    result = None
    try:
        while result is None:
            result = (yield child)
    except caught, e:
        while result is None:
            result = (yield branch)
    yield result
