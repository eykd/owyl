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

try:
    from mx.Stack import Stack, EmptyError
except ImportError:
    from stack import Stack, EmptyError

RETURN_VALUES = set((True, False, None))

__all__ = ['wrap', 'task', 'taskmethod', 'parent_task', 'parent_taskmethod', 'visit', 
           'succeed', 'fail', 'succeedAfter', 'failAfter', 
           'sequence', 'selector', 'parallel', 'PARALLEL_SUCCESS',
           'queue', 'parallel_queue',
           'throw', 'catch']


def wrap(func, *args, **kwargs):
    """Wrap a callable as a task. Yield the boolean of its result.
    """
    def initTask(**initkwargs):
        def makeIterator(**runkwargs):
            result = func(*args, **kwargs)
            yield bool(result)
        try: makeIterator.__name__ = func.__name__
        except AttributeError: pass
        try: makeIterator.__doc__ = func.__doc__
        except AttributeError: pass
        return makeIterator
    try: initTask.__doc__ = func.__doc__
    except AttributeError: pass
    try: initTask.__name__ = func.__name__
    except AttributeError: pass
    return initTask


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
        try: makeIterator.__name__ = func.__name__
        except AttributeError: pass
        try: makeIterator.__doc__ = func.__doc__
        except AttributeError: pass
        return makeIterator
    try: initTask.__doc__ = func.__doc__
    except AttributeError: pass
    try: initTask.__name__ = func.__name__
    except AttributeError: pass
    return initTask


def taskmethod(func):
    """Task decorator.

    Decorate a generator function to produce a re-usable generator
    factory for the given task.
    """
    def initTask(self, **initkwargs):
        def makeIterator(**runkwargs):
            runkwargs.update(initkwargs)
            iterator = func(self, **runkwargs)
            return iterator
        try: makeIterator.__name__ = func.__name__
        except AttributeError: pass
        try: makeIterator.__doc__ = func.__doc__
        except AttributeError: pass
        return makeIterator
    try: initTask.__doc__ = func.__doc__
    except AttributeError: pass
    try: initTask.__name__ = func.__name__
    except AttributeError: pass
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
        try: makeIterator.__name__ = func.__name__
        except AttributeError: pass
        try: makeIterator.__doc__ = func.__doc__
        except AttributeError: pass
        return makeIterator
    try: initTask.__doc__ = func.__doc__
    except AttributeError: pass
    try: initTask.__name__ = func.__name__
    except AttributeError: pass
    return initTask


def parent_taskmethod(func):
    """Parent task decorator.

    A parent task is a task that accepts children.

    Decorate a generator function to produce a re-usable generator
    factory for the given task.
    """
    def initTask(self, *children, **initkwargs):
        def makeIterator(**runkwargs):
            runkwargs.update(initkwargs)
            iterator = func(self, *children, **runkwargs)
            return iterator
        try: makeIterator.__name__ = func.__name__
        except AttributeError: pass
        try: makeIterator.__doc__ = func.__doc__
        except AttributeError: pass
        return makeIterator
    try: initTask.__doc__ = func.__doc__
    except AttributeError: pass
    try: initTask.__name__ = func.__name__
    except AttributeError: pass
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

    current = tree(**kwargs)
    send_value = None
    send_ok = False
    while True:
        try:
            if send_ok:
                child = current.send(send_value)
                send_value = None
                send_ok = False
            else:
                child = current.next()

            if child in return_values:
                send_value = child
                yield send_value
            else:
                # Descend into child node
                s.push(current)
                current = child
                
        except StopIteration:
            try:
                current = s.pop()
                send_ok = True
            except EmptyError:
                raise StopIteration


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
def stall(**kwargs):
    """Wrap a callable as a task. Yield the boolean of its result after 'after' iterations.

    Yields 'None' 'after' times.

    @keyword func: The callable to run.
    @type func: callable

    @keyword after: Run the callable after this many iterations.
    @type after: int
    """
    func = kwargs.pop('func')
    after = kwargs.pop('after', 1)
    for x in xrange(after):
        yield None
    yield bool(func())


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
        result = yield child(**kwargs)
        if not result and result is not None:
            final_value = False
            break
        
    yield final_value


@parent_task
def queue(queue, **kwargs):
    """Run tasks in the queue in sequence.

    The queue will run each task in the queue in sequence. If the
    queue is empty, it will stall until the queue receives new items.

    Note: the queue task *never* returns a success or failure code.

    The queue should be an object implementing pop(). If the queue has
    items in it, it should evaluate to True, otherwise False. The
    queue task will pop the next task in the queue and evaluate it in
    the normal fashion.

    @param queue: task queue.
    @type queue: A sequence object implementing pop()
    """
    while True:
        if queue:
            child = queue.pop()
            yield child(**kwargs)
        else:
            yield None


@parent_task
def parallel_queue(queue, **kwargs):
    """Run tasks in the queue in parallel.

    The queue will run each task in the queue in parallel. If the
    queue is empty, it will stall until the queue receives new items.

    Note: the queue task *never* returns a success or failure code.

    The queue should be an object implementing pop(). If the queue has
    items in it, it should evaluate to True, otherwise False. The
    queue task will pop the next task in the queue and evaluate it in
    the normal fashion.

    @param queue: task queue.
    """
    visits = []  # Canonical list of visited children
    visiting = []  # Working list of visited children
    while True:
        if queue:
            child = queue.pop()
            visits.append(visit(child, **kwargs))
        visiting[:] = visits  # Se we can remove from visits
        for child in visiting:
            try:
                child.next()
            except StopIteration:
                visits.remove(child)
        yield None


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
        result = (yield child(**kwargs))
        if result:
            final_value = True
            break
        
    yield final_value


class Enum(object):
    """Enum/namespace class. Cannot be implemented. 

    Subclass and add class variables.
    """
    def __init__(self): 
        raise NotImplementedError("_Enum class object. Do not instantiate.")


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
    return_values = set((True, False))
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
            yield None
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
    tree = visit(child, **kwargs)
    try:
        while result is None:
            result = tree.next()
            yield None
    except caught:
        while result is None:
            result = (yield branch(**kwargs))
    yield result
