# -*- coding: utf-8 -*-
"""boids -- Boids implementation using Owyl behavior trees.

This module provides example code using the L{owyl} library to
implement the Boids flocking algorithm.

Requirements
============

 Note: this demo requires Pyglet, Rabbyt, cocos2d

  - B{Pyglet}: U{http://pypi.python.org/pypi/pyglet}
  - B{Rabbyt}: U{http://pypi.python.org/pypi/Rabbyt}
  - B{cocos}: U{http://cocos2d.org/}


Intent
======

 This example demonstrates the basic usage of Owyl, including:

  - building and running a Behavior Tree, and
  - developing custom behaviors.


Definitions
===========

  - B{behavior}: Any unit of a Behavior Tree, as represented by a task
    node, branch, or group of parallel behaviors.
  - B{task node}: Any atomic Behavior Tree node.
  - B{parent node}/B{parent task}: Any task node that has child nodes.
  - B{branch}: A parent node and all its children.
  - B{node decorator}: A parent node with only one child. Used to add
    functionality to a child.
  - B{leaf node}/B{leaf task}/B{leaf}: A task node that has no children.


Algorithm
=========

 The basic Boids flocking algorithm was developed by Craig
 Reynolds. For more information, see his page at
 U{http://www.red3d.com/cwr/boids/}.

 It's a very simple algorithm, with three basic behaviors:

  - "B{Separation}: steer to avoid crowding local flockmates"
  - "B{Alignment}: steer towards the average heading of local flockmates"
  - "B{Cohesion}: steer to move toward the average position of local
    flockmates"

 I{(Definitions from C. Reynolds, linked above)}

 This is actually so simple, we wouldn't really need a behavior tree
 to model it, but it's a good place to start.

 Just to spice things up, we've added some extra behavior: boids will
 accelerate as they steer away from too-close flock mates, and they
 will seek to match a global speed. This gives the flock more the
 appearance of a school of fish, rather than a flight of sparrows, but
 it will let us break out some slightly more advanced behaviors.

 The boids will also seek after a fixed point (conveniently, the center
 of the screen), so that we can observe their movement better.


Building the Tree
=================

 See L{Boid.buildTree} below.


Core Behaviors
==============

 The core behaviors are documented below in each task nodes'
 docstring. They are:

  - L{Boid.hasCloseNeighbors}: conditional to detect crowding
  - L{Boid.accelerate}: accelerate at a given rate
  - L{Boid.matchSpeed}: accelerate to match a given speed
  - L{Boid.move}: move straight ahead at current speed
  - L{Boid.seek}: seek a fixed goal position
  - L{Boid.steerToMatchHeading}: match neighbors' average heading
  - L{Boid.steerForSeparation}: steer away from close flockmates
  - L{Boid.steerForCohesion}: steer toward average position of neighbors.


Helpers
=======

 A number of other helper methods clutter up the namespace. Boid also
 inherits from L{steering.Steerable<examples.steering.Steerable>},
 which contains common steering helper methads will be useful in
 future examples.


Other Stuff
===========

 Copyright 2008 David Eyk. All rights reserved.

 $Author$\n
 $Rev$\n
 $Date$

@newfield blackboard: Blackboard data
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
from cocos.actions import FadeIn
from cocos.tiles import ScrollableLayer, ScrollingManager

from owyl import blackboard
from owyl import taskmethod, visit, succeed, fail
from owyl import sequence, selector, parallel, PARALLEL_SUCCESS
from owyl.decorators import repeatUntilFail, limit, repeatAlways

from rabbyt.collisions import collide_single

from steering import Steerable


class Boid(Steerable):
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

        Building the Behavior Tree
        ==========================

         We'll use a L{parallel<owyl.core.parallel>} parent node as
         the root of our tree. Parallel is essentially a round-robin
         scheduler. That is, it will run one step on each its children
         sequentially, so that the children execute parallel to each
         other. Parallel is useful as a root behavior when we want
         multiple behaviors to run at teh same time, as with Boids.

         The first call to a task node constructor returns another
         function. Calling I{that} function will return an iterable
         generator. (This behavior is provided by the "@task..."
         family of python decorators found in L{owyl.core}.)
         Generally, you won't have to worry about this unless you're
         writing new parent nodes, but keep it in mind.

         Also note that keyword arguments can be provided at
         construction time (call to task constructor) or at run-time
         (call to visit). The C{blackboard} keyword argument to
         C{visit} will be available to the entire tree. (This is also
         why all nodes should accept C{**kwargs}-style keyword
         arguments, and access 

         Skipping down to the end of the tree definition, we see the
         first use of
         L{visit<owyl.core.visit>}. L{visit<owyl.core.visit>} provides
         the external iterator interface to the tree. Technically,
         it's an implementation of the Visitor pattern. It visits each
         "node" of the behavior tree and iterates over it, descending
         into children as determined by the logic of the parent
         nodes. (In AI terminology, this is a depth-first search, but
         with the search logic embedded in the tree.)
         L{visit<owyl.core.visit>} is also used internally by several
         parent behaviors, including L{parallel<owyl.core.parallel>},
         L{limit<owyl.decorators.limit>}, and
         L{repeatAlways<owyl.decorators.repeatAlways>} in order to
         gain more control over its children.

        L{limit<owyl.decorators.limit>}
        ===============================

         The next parent node we see is
         L{limit<owyl.decorators.limit>}. L{limit<owyl.decorators.limit>}
         is a decorator node designed to limit how often its child is
         run (given by the keyword argument C{limit_period} in
         seconds). This is useful for limiting the execution of
         expensive tasks.

         In the example below, we're using
         L{limit<owyl.decorators.limit>} to clear memoes once every
         second. This implementation of Boids uses
         L{memojito<examples.memojito>} to cache (or "memoize")
         neighbor data for each Boid. Neighbor data is used by each of
         the core behaviors, and is fairly expensive to
         calculate. However, it's constantly changing, so adjusting
         the limit_period will affect the behavior of the flock (and
         the frame rate).

        L{repeatAlways<owyl.decorators.repeatAlways>}
        =============================================
        
         We next see the L{repeatAlways<owyl.decorators.repeatAlways>}
         decorator node. This does exactly as you might expect: it
         takes a behavior that might only run once, and repeats it
         perpetually, ignoring return values and always yielding None
         (the special code for "I'm not done yet, give me another
         chance to run").

        Core Behaviors
        ==============

         The core behaviors are documented below in each method's
         docstring. They are:

          - L{Boid.hasCloseNeighbors}: conditional to detect crowding
          - L{Boid.accelerate}: accelerate at a given rate
          - L{Boid.matchSpeed}: accelerate to match a given speed
          - L{Boid.move}: move straight ahead at current speed
          - L{Boid.seek}: seek a fixed goal position
          - L{Boid.steerToMatchHeading}: match neighbors' average
            heading
          - L{Boid.steerForSeparation}: steer away from close
            flockmates
          - L{Boid.steerForCohesion}: steer toward average position of
            neighbors.

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
    def move(self, **kwargs):
        """Move the actor forward perpetually.

        @keyword blackboard: shared blackboard

        @blackboard: B{dt}: time elapsed since last update.
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

        @blackboard: B{dt}: time elapsed since last update.
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

        @blackboard: B{dt}: time elapsed since last update.
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
    def steerForSeparation(self, **kwargs):
        """Steer to maintain distance between self and neighbors.

        @keyword blackboard: shared blackboard
        @keyword rate: steering rate

        @blackboard: B{dt}: time elapsed since last update.
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

        @keyword blackboard: shared blackboard
        @keyword rate: steering rate

        @blackboard: B{dt}: time elapsed since last update.
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

                                     

    def canSee(self, other):
        """Return True if I can see the other boid.

        @param other: Another Boid or Sprite.
        @type other: L{Boid} or C{Sprite}.
        """
        dx = self.x - other.x
        dy = self.y - other.y
        return abs(self.getFacing(dx, dy)) < pi_1_2

    @memojito.memoizedproperty
    def others(self):
        """Find other boids that I can see.

        @rtype: C{list} of L{Boid}s.
        """
        return [b for b in self.boids if b is not self and self.canSee(b)]

    @property
    def neighbors(self):
        """Find the other boids in my neighborhood.

        @rtype: C{list} of L{Boid}s.
        """
        hood = (self.x, self.y, self.neighborhood_radius) # neighborhood
        n = collide_single(hood, self.others)
        return n

    @property
    def closest_neighbors(self):
        """Find the average position of the closest neighbors.

        @rtype: C{tuple} of C{(x, y)}.
        """
        hood = (self.x, self.y, self.personal_radius)
        n = collide_single(hood, self.others)
        return n
    
    def findAveragePosition(self, *boids):
        """Return the average position of the given boids.

        @rtype: C{tuple} of C{(x, y)}.
        """
        if not boids:
            return (0, 0)
        num_n = float(len(boids)) or 1
        avg_x = sum((getX(n) for n in boids))/num_n
        avg_y = sum((getY(n) for n in boids))/num_n
        return avg_x, avg_y

    def findAverageHeading(self, *boids):
        """Return the average heading of the given boids.

        @rtype: C{float} rotation in degrees.
        """
        if not boids:
            return 0.0
        return sum((getR(b) for b in boids))/len(boids)

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

        This gets scheduled in L{Boid.__init__}.

        @param dt: Change in time since last update.
        @type dt: C{float} seconds.
        """
        self.bb['dt'] = dt
        self.tree.next()


class SpriteLayer(ScrollableLayer):
    is_event_handler = True
    
    def __init__(self, how_many):
        super(SpriteLayer, self).__init__()
        self.how_many = how_many
        self.manager = ScrollingManager()
        self.manager.add(self)
        self.active = None
        self.blackboard = blackboard.Blackboard()
        self.boids = None

    def makeBoids(self):
        boids = []
        for x in xrange(int(self.how_many)):
            boid = Boid(self.blackboard)
            boid.position = (random.randint(0, 200),
                             random.randint(0, 200))
            boid.rotation = random.randint(1, 360)
            self.add(boid)
            boids.append(boid)

        return boids

    def on_enter(self):
        """Code to run when the Layer enters the scene.
        """
        super(SpriteLayer, self).on_enter()
        self.boids = self.makeBoids()

        self.manager.set_focus(0, 0)


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        how_many = int(sys.argv[1])
    else:
        how_many = 50
        
    director.init(resizable=True, caption="Owyl Behavior Tree Demo: Boids",
                  width=1024, height=768)
    s = Scene(SpriteLayer(how_many))
    director.run(s)
