# -*- coding: utf-8 -*-
"""base -- base behaviors for Owyl.

Copyright 2008 David Eyk. All rights reserved.

$Author$\n
$Rev$\n
$Date$
"""

__author__ = "$Author$"[9:-2]
__revision__ = "$Rev$"[6:-2]
__date__ = "$Date$"[7:-2]

try:
    from mx.Stack import Stack, EmptyError
except ImportError:
    from .stack import Stack, EmptyError

RETURN_VALUES = (True, False, None)

def task(func):
    """Task decorator.

    Decorate a generator function to produce a re-usable generator
    factory for the given task.
    """
    def initTask(*args, **initkwargs):
        def makeIterator(**runkwargs):
            runkwargs.update(initkwargs)
            iterator = func(*args, **runkwargs)
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
                yield None
        except StopIteration:
            try:
                current, cur_name = s.pop()
                #print "Ascending back to %s" % (cur_name,)
                send_ok = True
            except EmptyError:
                raise StopIteration
        except Exception, e:
            exc = e.__class__(*e.args)
            try:
                # Give the parent task a chance to handle the exception.
                current, cur_name = s.pop()
                current.throw(exc)
            except EmptyError:
                # Give up if the exception has propagated all the way
                # up the tree:
                raise exc

        
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
def sequence(*args, **kwargs):
    """Run tasks in sequence until one fails.

    The sequence will run each task in sequence until one fails,
    returning a failure. If all fail, returns a success.

    For more information, see the discussion at
    U{http://aigamedev.com/hierarchical-logic/sequence}.
    """
    final_value = True
    for child in args:
        result = (yield child)
        if not result:
            final_value = False
            break
        yield None
    yield final_value

@task
def selector(*args, **kwargs):
    """Run tasks in sequence until one succeeds.

    The selector will run each task in sequence until one succeeds,
    returning a success. If all fail, returns a failure.

    For more information, see the discussion at
    U{http://aigamedev.com/hierarchical-logic/selector}.

    @param *args: tasks to run in sequence as children.
    """
    final_value = False
    for child in args:
        result = (yield child)
        if result:
            final_value = True
            break
        yield None
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

@task
def parallel(*args, **kwargs):
    """Run tasks in parallel until the success policy is fulfilled or broken.

    If the success policy is met, return a success. If the policy is
    broken, return a failure.

    For more information, see the discussion at
    U{aigamedev.com/hierarchical-logic/parallel}.

    @param *args: tasks to run in parallel as children.

    @param policy: The success policy. All must succeed, 
                   or only one must succeed.
    @type policy: C{PARALLEL_SUCCESS.REQUIRE_ALL} or 
                  C{PARALLEL_SUCCESS.REQUIRE_ONE}.
    """
    return_values = (True, False)
    policy = kwargs.pop('policy', PARALLEL_SUCCESS.REQUIRE_ONE)
    all_must_succeed = (policy == PARALLEL_SUCCESS.REQUIRE_ALL)
    visits = [visit(arg, **kwargs) for arg in args]
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
                yield None
        except StopIteration:
            break
    yield final_value

@task
def throw(**kwargs):
    """Throw (raise) an exception.

    @param throws: An Exception to throw.
    @type throws: C{Exception}

    @param throws_message: Text to instantiate C{throws} with.
    @param throws_message: C{str}
    """
    throws = kwargs.pop('throws', Exception)
    throws_message = kwargs.pop('throws_message', '')
    class gen(object):
        def __iter__(self):
            return self
        def next(self):
            raise throws(throws_message)
    return gen
