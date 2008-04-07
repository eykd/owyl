# -*- coding: utf-8 -*-
#    I, for one, welcome our new robot overloards
#    Copyright (C) 2008 David Eyk, David Thulson, Collin Sanford, David Howery
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""ai -- artificial intelligence for actors, using Behavior Trees.

http://aigamedev.com/hierarchical-logic

$Author$
$Rev: 871 $
$Date: 2008-04-02 19:38:18 -0500 (Wed, 02 Apr 2008) $
"""

__author__ = "$Author$"
__revision__ = "$Rev: 871 $"
__date__ = "$Date: 2008-04-02 19:38:18 -0500 (Wed, 02 Apr 2008) $"

import traceback
import weakref
import operator
import random
choice = random.choice

from math import atan2, radians, degrees, pi
pi_2 = pi*2
pi_1_2 = pi/2.0

import rabbyt
import enum

import world
from entity import EntityCategories

from cellulose import InputCellDescriptor, ComputedCellDescriptor

RESULT = enum.Enum('FAIL', 'SUCCEED', 'CONTINUE')

class _BaseBTNode(object):
    """Base Behavior Tree Node.
    """
    def __init__(self, **kwargs):
        super(_BaseBTNode, self).__init__()
        self.parent = None

        self.priority = kwargs.get('priority', 1)
        self.probability = kwargs.get('probability', 1)

        self.RESULT_TABLE = {RESULT.SUCCEED: self.ifChildSucceeds,
                             RESULT.FAIL: self.ifChildFails,
                             RESULT.CONTINUE: self.ifChildContinues,}

    @ComputedCellDescriptor
    def target(self):
        return self.parent.target

    @ComputedCellDescriptor
    def memory(self):
        return self.parent.memory

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

    def ifChildSucceeds(self, child):
        return RESULT.SUCCEED

    def ifChildFails(self, child):
        return RESULT.FAIL

    def ifChildContinues(self, child):
        return RESULT.CONTINUE

    def step(self, dt):
        return RESULT.SUCCEED


class _BTNode(_BaseBTNode):
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

class _BTLeaf(_BTNode):
    def __init__(self, **kwargs):
        super(_BTLeaf, self).__init__(**kwargs)


class _BTDecorator(_BaseBTNode):
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

class Identity(_BTDecorator):
    """Transparent decorator.  Runs its child and passes on the result.
    """
    pass


class Root(_BTDecorator):
    """Root behavior tree node.  

    Repeat child forever.  Pretend everything's okay, even if it's
    not. Report exceptions.
    """
    target = InputCellDescriptor()
    memory = InputCellDescriptor()

    def __init__(self, target, child):
        self.target = target
        self.memory = {}
        super(Root, self).__init__(child)

    def step(self, dt):
        """Step through children.
        """
        try:
            self.child.step(dt)
        except Exception, e:
            traceback.print_exc()
        return RESULT.CONTINUE

class Sequence(_BTNode):
    """Sequence behavior.
    """
    def __init__(self, *children, **kwargs):
        super(Sequence, self).__init__(*children, **kwargs)
        self.cursor = 0

    def reset(self):
        self.cursor = 0

    def ifChildSucceeds(self, child):
        self.cursor += 1
        if self.cursor >= len(self.children):
            self.reset()
            result = RESULT.SUCCEED
        else:
            result = RESULT.CONTINUE
        return result

    def ifChildFails(self, child):
        self.reset()
        return RESULT.FAIL

    def step(self, dt):
        """Step through children in sequence.
        """
        try:
            c = self.children[self.cursor]
            c_result = c.step(dt)
        except Exception, e:
            self.reset()
            raise e
            
        return self.RESULT_TABLE[c_result](c)


_getProbability = operator.attrgetter('probability')
def pickByProbability(candidates):
    picklist = []
    for c in candidates:
        for x in xrange(_getProbability(c)):
            picklist.append(c)
    return choice(picklist)

_getPriority = operator.attrgetter('priority')
def pickByPriority(candidates):
    return sorted(candidates, key=_getPriority)[-1]

class Selector(_BTNode):
    """Selector behavior.

    Pick a child using the given picking strategy and run it.

    
    """
    def __init__(self, *children, **kwargs):
        super(Selector, self).__init__(*children, **kwargs)
        self.picker = kwargs.get('picker', pickByProbability)
        self.continue_child = False
        self.last_pick = None
    
    def ifChildContinues(self, child):
        self.continue_child = True
        return RESULT.CONTINUE

    def step(self, dt):
        if self.continue_child:
            self.continue_child = False
        else:
            self.last_pick = self.picker(self.children)
        
        c = self.last_pick
        c_result = c.step(dt)

        return self.RESULT_TABLE[c_result](c)


class RepeatUntilFail(_BTDecorator):
    """Repeat the decorated behavior unti it fails.
    """
    def ifChildSucceeds(self, child):
        return RESULT.CONTINUE

    def ifChildFails(self, child):
        return RESULT.FAIL


class RepeatUntilSucceed(_BTDecorator):
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


FAILURE_POLICY = enum.Enum('ALL', 'ONE')
COMPLETION_POLICY = enum.Enum('ALL', 'ONE')

class Parallel(_BTNode):
    """Parallel behaviors.

    Run all children in parallel (arbitrary sequential order).
    """
    def __init__(self, *children, **kwargs):
        super(Parallel, self).__init__(*children, **kwargs)

        self.failure_policy = kwargs.get('failure_policy',
                                         FAILURE_POLICY.ONE)
        self.completion_policy = kwargs.get('completion_policy',
                                         COMPLETION_POLICY.ALL)

        self.failed = 0
        self.completed = 0

        self.completed_children = []

        self.POLICY = {FAILURE_POLICY.ONE: self._policyOneFails,
                       FAILURE_POLICY.ALL: self._policyAllFail,
                       COMPLETION_POLICY.ONE: self._policyOneCompletes,
                       COMPLETION_POLICY.ALL: self._policyAllComplete}

    def reset(self):
        self.children.extend(self.completed_children)
        self.completed_children = []
        self.failed = 0
        self.completed = 0

    def _policyOneFails(self, child):
        self.reset()
        return RESULT.FAIL

    def _policyAllFail(self, child):
        if self.failed >= len(self.children)+len(self.completed_children):
            self.reset()
            result = RESULT.FAIL
        else:
            result = RESULT.CONTINUE
        return result

    def _policyOneCompletes(self, child):
        self.reset()
        return RESULT.SUCCEED

    def _policyAllComplete(self, child):
        if self.completed >= len(self.children)+len(self.completed_children):
            self.reset()
            result = RESULT.SUCCEED
        else: 
            result = RESULT.CONTINUE
        return result

    def ifChildFails(self, child):
        self.failed += 1
        self.completed += 1
        self.children.remove(child)
        self.completed_children.append(child)
        return min(self.POLICY[self.failure_policy](child),
                   self.POLICY[self.completion_policy](child))

    def ifChildSucceeds(self, child):
        self.completed += 1
        self.children.remove(child)
        self.completed_children.append(child)
        return self.POLICY[self.completion_policy](child)

    def step(self, dt):
        results = []
        for c in tuple(self.children):
            c_result = c.step(dt)
            result = self.RESULT_TABLE[c_result](c)
            results.append(result)
        results.sort(reverse=True)
        return results[-1]


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

class _AfterNode(_BTNode):
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

class Succeed(_AfterNode):
    """Always succeed, or, succeed after a given number of steps.
    """
    def getFinalResult(self):
        return RESULT.SUCCEED

class Fail(_AfterNode):
    """Always fail, or, fail after a given number of steps.
    """
    def getFinalResult(self):
        return RESULT.FAIL


class Error(_AfterNode):
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

class Limit(_BTDecorator):
    def __init__(self, child, delay, **kwargs):
        super(Limit, self).__init__(child, **kwargs)
        self.delay = delay
        self.counter = delay*random.random()

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


class FindPlayer(_BTNode):
    def __init__(self, **kwargs):
        super(FindPlayer, self).__init__(**kwargs)
        self.look_radius = 400
    
    def step(self, dt):
        target = self.target
        x, y = target.xy
        players = target.world.queryEntitiesNear(x, y, self.look_radius,
                                                 (EntityCategories.player,))
        if players:
            self.memory['player_pos'] = players[0].xy
            #print "Found player at", players[0].xy
            result = RESULT.SUCCEED
        else:
            self.memory['player_pos'] = None
            result = RESULT.FAIL
        return result

class _MemoryHandler(_BTNode):
    def __init__(self, memory_point, **kwargs):
        super(_MemoryHandler, self).__init__(**kwargs)
        self.memory_point = memory_point

    def getMemory(self):
        return self.memory.setdefault(self.memory_point, None)

class CheckMemory(_MemoryHandler):
    """Check our memory to see if we know about the given memory point.
    """
    def step(self, dt):
        mp = self.getMemory()
        if mp is None:
            result = RESULT.FAIL
        else:
            result = RESULT.SUCCEED
        return result

class TurnToFace(_MemoryHandler):
    """Turn to face the position recalled from memory.
    """
    def step(self, dt):
        mp = self.getMemory()
        target = self.target
        if mp is None:
            result = RESULT.FAIL
        else:
            rot_delta = target.getRotationDelta(*mp)
                
            if rot_delta < -0.1:
                target.turning_right = False
                target.turning_left = True
            elif rot_delta > 0.1:
                target.turning_right = True
                target.turning_left = False
            else:
                target.turning_right = False
                target.turning_left = False

            result = RESULT.SUCCEED
        return result

class TurnToFlee(_MemoryHandler):
    """Turn to flee from the position recalled from memory.
    """
    def step(self, dt):
        mp = self.getMemory()
        target = self.target
        if mp is None:
            result = RESULT.FAIL
        else:
            rot_delta = target.getRotationDelta(*mp)
                
            if rot_delta < -0.1:
                target.turning_right = True
                target.turning_left = False
            elif rot_delta > 0.1:
                target.turning_right = False
                target.turning_left = True
            else:
                target.turning_right = False
                target.turning_left = False

            result = RESULT.SUCCEED
        return result


class MoveForward(_BTNode):
    def __init__(self, **kwargs):
        super(MoveForward, self).__init__(**kwargs)

    def step(self, dt):
        target = self.target
        target.accelerating = True
        target.backing = False
        return RESULT.SUCCEED

class Stop(_BTNode):
    def __init__(self, **kwargs):
        super(Stop, self).__init__(**kwargs)

    def step(self, dt):
        target = self.target
        target.accelerating = False
        target.backing = False
        target.turning_left = False
        target.turning_right = False
        #self.report("Stopped.")
        return RESULT.SUCCEED


class Flip(_BTDecorator):
    """Flip the return value of the child.
    """
    def ifChildSucceeds(self, child):
        return RESULT.FAIL

    def ifChildFails(self, child):
        return RESULT.SUCCEED

class CheckCollision(_BTNode):
    def step(self, dt):
        target = self.target
        collide = self.target.last_collision
        if collide is not None:
            self.target.last_collision = None
            self.memory['last_collision'] = collide
            #self.report("last collided at %s" % (collide,))
            result = RESULT.SUCCEED
        else:
            #self.report("found no previous collisions.")
            result = RESULT.FAIL
        return result

class ClearMemory(_MemoryHandler):
    def step(self, dt):
        self.memory[self.memory_point] = None
        #self.report("cleared memory at %s" % (self.memory_point,))
        #self.report("remembers %s as %s" % (self.memory_point, 
        #                                    self.memory[self.memory_point]))
        return RESULT.SUCCEED


class factory(object):
    def __init__(self):
        msg = "Do not instantiate.  Use class members and methods."
        raise NotImplementedError, msg

    @classmethod
    def buildDudeAI(cls, dude):
        r = Root(dude, 
                 Limit(
                 Parallel(Limit(FindPlayer(), 0.3),
                          Sequence(CheckMemory('player_pos'),
                                   Limit(TurnToFlee('player_pos'), 0.1),
                                   MoveForward(),
                                   ),
                          Sequence(Flip(CheckMemory('player_pos')),
                                   Stop(),
                                   ),
                          Sequence(CheckCollision(),
                                   Stop(),
                                   Limit(TurnToFlee('last_collision'), 0.1),
                                   ClearMemory('last_collision'),
                                   MoveForward(),
                                   )
                          ),
                 0.1),
                 )
        # When we have found a player:
        # 
        return r
                 
