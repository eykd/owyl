# -*- coding: utf-8 -*-
"""movement -- basic movement behaviors.

http://aigamedev.com/hierarchical-logic

$Author$
$Rev$
$Date$
"""

__author__ = "$Author$"
__revision__ = "$Rev$"
__date__ = "$Date$"


from math import cos, sin, atan2, radians, degres

def getVectorComponents(rot):
    """Return the x, y vector components of the given rotation.
    """
    x = cos(radians(rot))
    y = sin(radians(rot))
    return x, y

def getRotationDelta(origin, rotation, target_pos):
    """Return the change in rotation necessary to face the target position.
    """
    t_x, t_y = target_pos
    my_x, my_y = origin
    dx = my_x - t_x
    dy = my_y - t_y
    facing = getFacing(t_x, t_y)
    rot_delta = radians(rot) - atan2(dy, dx) + pi
    while rot_delta < -pi:
        rot_delta += pi_2
    while rot_delta > pi:
        rot_delta -= pi_2

    return rot_delta

def getFacing(x, y):
    """Return the rotation in degrees that faces the given coordinates.
    """
    return degrees(atan2(y, x))-90.0

def face(self, x, y):
    self.rot = self.getFacing(x, y)



class TurnToFace(MemoryHandler):
    """Turn to face the position recalled from memory.
    """
    def step(self, dt):
        mp = self.getMemoryPoint()
        target = self.target
        if mp is None:
            result = RESULT.FAIL
        else:
            rot_delta = getRotationDelta(target.xy, target.rot, mp)
                
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

class TurnToFlee(MemoryHandler):
    """Turn to flee from the position recalled from memory.
    """
    def step(self, dt):
        mp = self.getMemoryPoint()
        target = self.target
        if mp is None:
            result = RESULT.FAIL
        else:
            rot_delta = getRotationDelta(target.xy, target.rot, mp)
                
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


class StopRotation(BTNode):
    """Stop all target rotation.
    """
    def step(self, dt):
        target = self.target
        target.turning_right = False
        target.turning_left = False
        return RESULT.SUCCEED


class AmFacing(MemoryHandler):
    """Check if we are facing the memory point.
    """
    def step(self, dt):
        mp = self.getMemoryPoint()
        target = self.target
        if mp is None:
            result = RESULT.FAIL
        else:
            rot_delta = getRotationDelta(target.xy, target.rot, mp)

            if rot_delta > -0.1 and rot_delta < 0.1:
                result = RESULT.SUCCEED
            else:
                result = RESULT.FAIL
        return result


class AmFleeing(MemoryHandler):
    """Check if we are fleeing the memory point.
    """
    def step(self, dt):
        mp = self.getMemoryPoint()
        target = self.target
        if mp is None:
            result = RESULT.FAIL
        else:
            rot_delta = abs(getRotationDelta(mp))

            if rot_delta > (pi-0.1) and rot_delta < (pi+0.1):
                result = RESULT.SUCCEED
            else:
                result = RESULT.FAIL
        return result


class MoveForward(BTNode):
    """Move the target forward.
    """
    def __init__(self, **kwargs):
        super(MoveForward, self).__init__(**kwargs)

    def step(self, dt):
        target = self.target
        target.accelerating = True
        target.backing = False
        return RESULT.SUCCEED

class Stop(BTNode):
    """Stop all rotation and movement.
    """
    def __init__(self, **kwargs):
        super(Stop, self).__init__(**kwargs)

    def step(self, dt):
        target = self.target
        target.accelerating = False
        target.backing = False
        target.turning_left = False
        target.turning_right = False
        return RESULT.SUCCEED


class CheckCollision(BTNode):
    """Check for a value other than none on target.last_collision
    """
    def step(self, dt):
        target = self.target
        try:
            collide = self.target.last_collision
        except AttributeError:
            collide = self.target.last_collision = None
        if collide is not None:
            self.target.last_collision = None
            self.memory['last_collision'] = collide
            result = RESULT.SUCCEED
        else:
            result = RESULT.FAIL
        return result

class LookAheadForCollision(BTNode):
    """Look ahead of the target for collisions with categories of objects.

    Uses blackboard object registrations.
    """
    def __init__(self, look_ahead, categories=(), **kwargs):
        super(LookAheadForCollision, self).__init__(**kwargs)
        self.categories = categories
        self.look_ahead = look_ahead

    def step(self, dt):
        x,y = self.target.convert_offset((0, self.look_ahead))
        collision = False
        for ctg in self.categories:
            c = collisions.collide_single((x, y, 1), self.blackboard[ctg])
            if c: collision = True
            break
        if collision:
            result = RESULT.SUCCEED
        else:
            result = RESULT.FAIL
        return result
        

class CheckSimpleDistance(MemoryHandler):
    """Checks for Manhattan distance.
    """
    def __init__(self, memory_point, 
                 greater_than=0.0, less_than=sys.maxint, **kwargs):
        super(CheckSimpleDistance, self).__init__(memory_point, **kwargs)
        self.greater_than = greater_than
        self.less_than = less_than
    
    def step(self, dt):
        my_x, my_y = self.target.xy
        mp = self.getMemoryPoint()
        if mp is not None:
            c_x, c_y = mp
        
            dx = abs(my_x - c_x)
            dy = abs(my_y - c_y)
            
            in_bounds = False
            gt = self.greater_than
            lt = self.less_than
            if gt < dx < lt or gt < dy < lt:
                in_bounds = True
            if in_bounds:
                result = RESULT.SUCCEED
            else:
                result = RESULT.FAIL
        else:
            result = RESULT.FAIL
        return result


class CheckDistance(MemoryHandler):
    """Checks for real distance matching given bounds.
    """
    def __init__(self, memory_point, 
                 greater_than=0.0, less_than=sys.maxint, **kwargs):
        super(CheckSimpleDistance, self).__init__(memory_point, **kwargs)
        self.greater_than = greater_than
        self.less_than = less_than
    
    def step(self, dt):
        my_x, my_y = self.target.xy
        mp = self.getMemoryPoint()
        if mp is not None:
            c_x, c_y = mp

            d = sqrt((my_x-c_x)**2 + (my_y-c_y)**2)

            in_bounds = False
            gt = self.greater_than
            lt = self.less_than
            if gt < d < lt:
                in_bounds = True

            if in_bounds:
                result = RESULT.SUCCEED
            else:
                result = RESULT.FAIL
        else:
            result = RESULT.FAIL
        return result

