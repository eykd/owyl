"""base -- base Behavior Trees node objects.

http://aigamedev.com/hierarchical-logic

$Author$
$Rev$
$Date$
"""

__author__ = "$Author$"
__revision__ = "$Rev$"
__date__ = "$Date$"


from cellulose import InputCellDescriptor, ComputedCellDescriptor

import enum

RESULT = enum.Enum('FAIL', 'SUCCEED', 'CONTINUE')

class BaseBTNode(object):
    """Base Behavior Tree Node.
    """
    def __init__(self, **kwargs):
        super(_BaseBTNode, self).__init__()
        self.parent = None

        self.priority = kwargs.get('priority', 1)
        self.probability = kwargs.get('probability', 1)

    @ComputedCellDescriptor
    def target(self):
        return self.parent.target

    @ComputedCellDescriptor
    def memory(self):
        return self.parent.memory

    @ComputedCellDescriptor
    def blackboard(self):
        return self.parent.blackboard

    def report(self, action_msg):
        print self.target.__class__.__name__, action_msg

    def isRoot(self):
        return self.parent is None

    def step(self, dt):
        return RESULT.SUCCEED

    def stepTimes(self, n, dt):
        dt = dt/float(n)
        results = tuple((self.step(dt) for x in xrange(n)))
        return results


class BTParentNode(object):
    """Mixin class for a nodes that can handle child result states.
    """
    def __init__(self, **kwargs):
        super(BTParentNode, self).__init__()
        self.RESULT_TABLE = {RESULT.SUCCEED: self.ifChildSucceeds,
                             RESULT.FAIL: self.ifChildFails,
                             RESULT.CONTINUE: self.ifChildContinues,}

    def ifChildSucceeds(self, child):
        return RESULT.SUCCEED

    def ifChildFails(self, child):
        return RESULT.FAIL

    def ifChildContinues(self, child):
        return RESULT.CONTINUE


class BTNode(BaseBTNode, BTParentNode):
    """Behavior Tree Node.
    """
    def __init__(self, *children, **kwargs):
        super(_BTNode, self).__init__(**kwargs)
        self.children = []

        self.addChildren(*children)

    def addChildren(self, *children):
        [setattr(c, 'parent', self) for c in children]
        self.children.extend(children)

    def isLeaf(self):
        return not bool(self.children)

class BTLeaf(BTNode):
    """Behavior Tree leaf node.
    """
    def __init__(self, **kwargs):
        super(_BTLeaf, self).__init__(**kwargs)

    def isLeaf(self):
        return True


class AfterNode(BTLeaf):
    """Always return something until after so many steps.
    """
    def __init__(self, after=None, until_then=RESULT.CONTINUE, 
                 **kwargs):
        super(_AfterNode, self).__init__(**kwargs)
        self.until_then = until_then
        self.after = after
        self.count = 0

    def getFinalResult(self):
        return RESULT.CONTINUE

    def reset(self):
        count = 0

    def step(self, dt):
        if self.after is None:
            result = self.getFinalResult()
        else:
            if self.count >= self.after:
                self.reset()
                result = self.getFinalResult()
            else:
                result = self.until_then
            self.count += 1
        return result


class Succeed(AfterNode):
    """Always succeed, or, succeed after a given number of steps.
    """
    def getFinalResult(self):
        return RESULT.SUCCEED


class Fail(AfterNode):
    """Always fail, or, fail after a given number of steps.
    """
    def getFinalResult(self):
        return RESULT.FAIL


class Error(AfterNode):
    """Always raise an exception, or, raise after a given number of steps.
    """
    def __init__(self, exc=Exception, msg="Reached Error node.", 
                 after=None, until_then=RESULT.CONTINUE, **kwargs):
        super(Error, self).__init__(after=after, until_then=until_then,
                                    **kwargs)
        self.exc = exc
        self.msg = msg

    def getFinalResult(self):
        raise self.exc(self.msg)


class SetAttribute(BTLeaf):
    """Set the given attribute name on our target to the function result.
    """
    def __init__(self, name, value_func, **kwargs):
        self.set_name = name
        self.getValue = value_func

    def step(self, dt):
        setattr(self.target, self.set_name, self.getValue())
        return RESULT.SUCCEED

