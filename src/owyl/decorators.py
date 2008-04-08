"""decorators -- decorator nodes for Behavior Trees.

http://aigamedev.com/hierarchical-logic

$Author$
$Rev$
$Date$
"""

__author__ = "$Author$"
__revision__ = "$Rev$"
__date__ = "$Date$"

from base import BaseBTNode, BTParentNode

class BTDecorator(BaseBTNode, BTParentNode):
    """Special purpose Behavior Tree node that can have only one child.

    Defaults to identity behavior.
    """
    def __init__(self, child, **kwargs):
        super(_BTDecorator, self).__init__(**kwargs)
        self.child = None

        self.setChild(child)

    def setChild(self, child):
        """Set the decorator's child.
        """
        self.child = child
        self.child.parent = self

    def isLeaf(self):
        """Decorators can't be leaves.
        """
        return False

    def step(self, dt):
        c = self.child
        c_result = c.step(dt)
        return self.RESULT_TABLE[c_result](c)


class Identity(BTDecorator):
    """Transparent decorator.  Runs its child and passes on the result.
    """
    pass


class RepeatUntilFail(BTDecorator):
    """Repeat the decorated behavior unti it fails.
    """
    def ifChildSucceeds(self, child):
        return RESULT.CONTINUE

    def ifChildFails(self, child):
        return RESULT.FAIL


class RepeatUntilSucceed(BTDecorator):
    """Repeat the decorated behavior unti it succeeds.
    """
    def ifChildSucceeds(self, child):
        return RESULT.SUCCEED

    def ifChildFails(self, child):
        return RESULT.CONTINUE

    def step(self, dt):
        c = self.child
        c_result = c.step(dt)
        return self.RESULT_TABLE[c_result](c)


def logStdout(*stuff):
    print stuff

class Log(_BTDecorator):
    """Logging decorator.  Accepts a function w/ two arguments.

    Sends (self.child, result) to logFunc.
    """
    def __init__(self, child, logFunc=logStdout, **kwargs):
        super(Log, self).__init__(child, **kwargs)
        self.logFunc = logFunc

    def step(self, dt):
        result = self.child.step(dt)
        self.logFunc(self.child, result)


class Limit(BTDecorator):
    def __init__(self, child, delay, **kwargs):
        super(Limit, self).__init__(child, **kwargs)
        self.delay = delay
        self.counter = 0.0 #delay*random.random()

    def step(self, dt):
        self.counter += dt
        delay = self.delay
        if self.counter >= delay:
            dt = self.counter
            self.counter -= delay
            result = self.child.step(dt)
        else:
            result = RESULT.CONTINUE
        return result


class Flip(BTDecorator):
    """Flip the return value of the child.
    """
    def ifChildSucceeds(self, child):
        return RESULT.FAIL

    def ifChildFails(self, child):
        return RESULT.SUCCEED


