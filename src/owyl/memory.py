"""memory -- behaviors for working with memory

http://aigamedev.com/hierarchical-logic

$Author$
$Rev$
$Date$
"""

__author__ = "$Author$"
__revision__ = "$Rev$"
__date__ = "$Date$"

from base import BTNode
from base import RESULT


class MemoryHandler(BTNode):
    def __init__(self, memory_point, from_blackboard=False, **kwargs):
        super(_MemoryHandler, self).__init__(**kwargs)
        self.memory_point = memory_point

        if from_blackboard:
            self.getMemoryPoint = self._getBlackboardPoint
            self.setMemoryPoint = self._setBlackboardPoint

    def getMemoryPoint(self):
        return self.memory.setdefault(self.memory_point, None)

    def _getBlackboardPoint(self):
        return self.blackboard.setdefault(self.memory_point, None)

    def setMemoryPoint(self, v):
        self.memory[self.memory_point] = v

    def _setBlackboardPoint(self, v):
        self.blackboard[self.memory_point] = v



class CheckMemory(MemoryHandler):
    """Check our memory to see if we know about the given memory point.

    Empty memory points will be set to None.
    """
    def step(self, dt):
        mp = self.getMemoryPoint()
        if mp is None:
            result = RESULT.FAIL
        else:
            result = RESULT.SUCCEED
        return result


class ClearMemory(MemoryHandler):
    """Clear the given memory point (by setting it to None).
    """
    def step(self, dt):
        self.setMemoryPoint(None)
        return RESULT.SUCCEED


class FindNearest(MemoryHandler):
    """Find the nearest member of the given categories, within a radius.

    This makes use of the registered obects on the root blackboard.
    """
    def __init__(self, memory_point, categories=(), look_radius=400, **kwargs):
        super(FindNearest, self).__init__(memory_point, 
                                          use_blackboard=True,
                                          **kwargs)
        self.look_radius = look_radius
        self.categories = categories
    
    def step(self, dt):
        target = self.target
        x, y = target.xy

        found = []
        for c in self.categories:
            found.extend(self.blackboard[c])
        if found:
            nearby = collisions.collide_single((x, y, self.look_radius), found)
            if nearby:
                nearby.sort(key=lambda r: (abs(r.x - x)+abs(r.y -y)) / 2.0)
                self.setMemory(nearby[0].xy)
                #self.memory[self.memory_point] = nearby[0].xy
                result = RESULT.SUCCEED
            else:
                self.setMemory(None)
                self.memory[self.memory_point] = None
                result = RESULT.FAIL
        else:
            result = RESULT.FAIL
        return result

