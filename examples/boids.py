# -*- coding: utf-8 -*-
"""boids -- Boids implementation using Owyl behavior trees.

Note: this demo requires Pyglet, Rabbyt, and cocos2d.

Copyright 2008 David Eyk. All rights reserved.

$Author$\n
$Rev$\n
$Date$
"""

__author__ = "$Author$"[9:-2]
__revision__ = "$Rev$"[6:-2]
__date__ = "$Date$"[7:-2]

import os

import random
from math import radians, degrees, sin, cos, pi, atan2
pi_2 = pi*2.0
pi_1_2 = pi/2.0
pi_1_4 = pi/4.0
pi_3_4 = (pi*3)/4

from operator import attrgetter, itemgetter
getX = attrgetter('x')
getY = attrgetter('y')
getR = attrgetter('rotation')

import memojito

import pyglet
pyglet.resource.path = [os.path.dirname(os.path.abspath(__file__)),]
pyglet.resource.reindex()

from cocos.director import director
from cocos.scene import Scene
from cocos.sprite import Sprite
from cocos.actions import FadeIn
from cocos.tiles import ScrollableLayer, ScrollingManager

from owyl import blackboard
from owyl import taskmethod, visit, succeed, fail
from owyl import sequence, selector, parallel, PARALLEL_SUCCESS
from owyl.decorators import repeatUntilFail, limit, repeatAlways

from rabbyt.collisions import collide_single


class Boid(Sprite):
    _img = pyglet.resource.image('triangle.png')
    _img.anchor_x = _img.width / 2
    _img.anchor_y = _img.height / 2

    boids = []

    def __init__(self, blackboard):
        super(Boid, self).__init__(self._img)
        self.scale = 0.05
        self.schedule(self.update)
        self.bb = blackboard
        self.boids.append(self)
        self.opacity = 0
        self.do(FadeIn(2))
        self.speed = 200
        self.bounding_radius = 5
        self.bounding_radius_squared = 25
        self.neighborhood_radius = 1000
        self.personal_radius = 20

        self.tree = self.buildTree()

    def buildTree(self):
        """Build the behavior tree.

        Building the behavior tree is as simple as nesting the
        behavior constructor calls.
        """
        tree = parallel(limit(repeatAlways(self.clearMemoes(), debug=True), 
                              limit_period=1),
                        
                        ### Velocity and Acceleration
                        #############################
                        repeatAlways(sequence(self.hasCloseNeighbors(),
                                              self.accelerate(rate=.01),
                                              ),
                                     ),
                        self.move(),
                        self.matchSpeed(match_speed=200, rate=.01),

                        ### Steering
                        ############
                        self.seek(goal=(0, 0), rate=2),
                        self.steerToMatchHeading(rate=1),
                        self.steerForSeparation(rate=3),
                        self.steerForCohesion(rate=1),

                        policy=PARALLEL_SUCCESS.REQUIRE_ALL
                        )
        return visit(tree, blackboard=self.bb)

    def canSee(self, other):
        """Return True if I can see the other boid.
        """
        dx = self.x - other.x
        dy = self.y - other.y
        return abs(self.getFacing(dx, dy)) < pi_1_2

    @memojito.memoizedproperty
    def others(self):
        """Find other boids that I can see.
        """
        return [b for b in self.boids if b is not self and self.canSee(b)]

    @property
    def neighbors(self):
        """Find the other boids in my neighborhood.
        """
        hood = (self.x, self.y, self.neighborhood_radius) # neighborhood
        n = collide_single(hood, self.others)
        return n

    @property
    def closest_neighbors(self):
        """Find the average position of the closest neighbors.
        """
        hood = (self.x, self.y, self.personal_radius)
        n = collide_single(hood, self.others)
        return n
    
    def findAveragePosition(self, *boids):
        """Return the average position of the given boids.
        """
        if not boids:
            return (0, 0)
        num_n = float(len(boids)) or 1
        avg_x = sum((getX(n) for n in boids))/num_n
        avg_y = sum((getY(n) for n in boids))/num_n
        return avg_x, avg_y


    def findAverageHeading(self, *boids):
        """Return the average heading of the given boids.
        """
        if not boids:
            return 0.0
        return sum((getR(b) for b in boids))/len(boids)
    

    def findRotationDelta(self, this_heading, that_heading):
        """Find the change in rotation required to match a given heading.
        
        Headings are given in radians.
        """
        
        dr = (that_heading - this_heading)
        while dr < -pi:
            dr += pi_2
        while dr > pi:
            dr -= pi_2
        return dr

    def getFacing(self, tx, ty):
        """Find the facing rotation to local coordinates tx, ty.
        """
        return -(atan2(ty, tx) - pi_1_2)

    @taskmethod
    def move(self, **kwargs):
        """Move the actor forward perpetually.
        """
        bb = kwargs['blackboard']
        while True:
            dt = bb['dt']
            r = radians(getR(self)) # rotation
            s = dt * self.speed
            self.x += sin(r) * s
            self.y += cos(r) * s
            yield None


    @taskmethod
    def seek(self, **kwargs):
        """Perpetually seek a goal position.

        @keyword rate: steering rate
        @keyword blackboard: shared blackboard
        """
        bb = kwargs['blackboard']
        rate = kwargs['rate']
        gx, gy = kwargs.get('goal', (0, 0))
        while True:
            dt = bb['dt']
            dx = gx-self.x
            dy = gy-self.y
            seek_heading = self.getFacing(dx, dy)
            my_heading = radians(self.rotation)
            
            rsize = degrees(self.findRotationDelta(my_heading, seek_heading))

            rchange = rsize * rate * dt
            self.rotation += rchange
            yield None
            

    @taskmethod
    def steerToMatchHeading(self, **kwargs):
        """Perpetually steer to match actor's heading to neighbors.
        
        @keyword blackboard: shared blackboard
        @keyword rate: steering rate
        """
        bb = kwargs['blackboard']
        rate = kwargs['rate']
        while True:
            dt = bb['dt'] or 0.01
            n_heading = radians(self.findAverageHeading(*self.neighbors))
            if n_heading is None:
                yield None
                continue
            my_heading = radians(self.rotation)
            
            rsize = degrees(self.findRotationDelta(my_heading, n_heading))

            # Factor in our turning rate and elapsed time.
            rchange = rsize * rate * dt
            
            self.rotation += rchange
            yield None

    @taskmethod
    def hasCloseNeighbors(self, **kwargs):
        """Check to see if we have close neighbors.
        """
        yield bool(self.closest_neighbors)

    @taskmethod
    def accelerate(self, **kwargs):
        """accelerate

        @keyword rate: The rate of acceleration (+ or -)
        """
        bb = kwargs['blackboard']
        rate = kwargs['rate']
        dt = bb['dt']
        self.speed = max(self.speed + rate * dt, 0)
        yield True

    @taskmethod
    def matchSpeed(self, **kwargs):
        """Accelerate to match the given speed.

        @keyword blackboard: A shared blackboard.
        @keyword match_speed: The speed to match.
        @keyword rate: The rate of acceleration.
        """
        bb = kwargs['blackboard']
        ms = kwargs['match_speed']
        rate = kwargs['rate']
        while True:
            if self.speed == ms:
                yield None
            dt = bb['dt']
            dv_size = ms - self.speed
            dv = dv_size * rate * dt
            self.speed += dv
            yield None
                                     
    @taskmethod
    def steerForSeparation(self, **kwargs):
        """Steer to maintain distance between self and neighbors.
        """
        bb = kwargs['blackboard']
        rate = kwargs['rate']
        while True:
            cn_x, cn_y = self.findAveragePosition(*self.closest_neighbors)
            
            dt = bb['dt']
            dx = self.x-cn_x
            dy = self.y-cn_y
            
            heading_away_from_neighbors = self.getFacing(dx, dy)
            flee_heading = heading_away_from_neighbors
            my_heading = radians(self.rotation)
            
            rsize = degrees(self.findRotationDelta(my_heading, flee_heading))
            
            # Factor in our turning rate and elapsed time.
            rchange = rsize * rate * dt
            
            self.rotation += rchange
            yield None

    @taskmethod
    def steerForCohesion(self, **kwargs):
        """Steer toward the average position of neighbors.
        """
        bb = kwargs['blackboard']
        rate = kwargs['rate']
        while True:
            neighbors = self.neighbors
            np_x, np_y = self.findAveragePosition(*neighbors)
            dt = bb['dt']
            dx = np_x-self.x
            dy = np_y-self.y
            seek_heading = self.getFacing(dx, dy)
            my_heading = radians(self.rotation)

            # Find the rotation delta
            rsize = degrees(self.findRotationDelta(my_heading, seek_heading))
            
            # Factor in our turning rate and elapsed time.
            rchange = rsize * rate * dt

            self.rotation += rchange
            yield None

    @taskmethod
    def clearMemoes(self, **kwargs):
        """Clear memoizations.
        """
        self.clear()
        yield True

    @memojito.clearbefore
    def clear(self):
        """Clear memoizations.
        """
        pass

    def update(self, dt):
        """Update this Boid's behavior tree.

        This gets scheduled in the __init__.
        """
        self.bb['dt'] = dt
        self.tree.next()


class SpriteLayer(ScrollableLayer):
    is_event_handler = True
    
    def __init__(self):
        super(SpriteLayer, self).__init__()
        self.manager = ScrollingManager()
        self.manager.add(self)
        self.active = None
        self.blackboard = blackboard.Blackboard()


    def makeBoids(self, how_many):
        boids = []
        for x in xrange(how_many):
            boid = Boid(self.blackboard)
            boid.position = (random.randint(0, 200),
                             random.randint(0, 200))
            boid.rotation = random.randint(1, 360)
            self.add(boid)
            boids.append(boid)

        return boids

    def on_enter(self):
        super(SpriteLayer, self).on_enter()
        self.makeBoids(50)[0]

        self.manager.set_focus(0, 0)


if __name__ == "__main__":
    director.init(resizable=True, caption="Owyl Behavior Tree Demo: Boids",
                  width=1024, height=768)
    s = Scene(SpriteLayer())
    director.run(s)
