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
pi_2 = pi/2.0

from operator import attrgetter, itemgetter
getX = attrgetter('x')
getY = attrgetter('y')
getR = attrgetter('rotation')

import pyglet
pyglet.resource.path = [os.path.dirname(os.path.abspath(__file__)),]
pyglet.resource.reindex()
print pyglet.resource.path

from cocos.director import director
from cocos.actions import MoveTo, MoveBy, FadeIn
from cocos.layer import Layer
from cocos.scene import Scene
from cocos.sprite import Sprite
from cocos.tiles import ScrollableLayer, ScrollingManager

from owyl import blackboard
from owyl import task, visit
from owyl import parallel, sequence, selector

from rabbyt.collisions import collide_single

@task
def move(**kwargs):
    """Move the actor forward perpetually.

    @keyword actor: actor to move
    """
    bb = kwargs['blackboard']
    a = kwargs['actor']
    while True:
        dt = bb['dt']
        r = radians(getR(a)) # rotation
        s = dt * a.speed
        a.x += sin(r) * s
        a.y += cos(r) * s
        yield None

@task
def steerToMatchHeading(**kwargs):
    """Perpetually steer to match actor's heading to neighbors.

    @keyword dt: delta time
    @keyword actor: actor to move
    @keyword rate: steering rate
    """
    bb = kwargs['blackboard']
    a = kwargs['actor']
    rate = kwargs['rate']
    while True:
        dt = bb['dt']
        n_heading = radians(a.neighbors_avg_heading)
        my_heading = radians(a.rotation)

        # Find the rotation delta
        r = (n_heading - my_heading) % pi - pi_2
        rsize = degrees(abs(r)) 

        # Factor in our turning rate and elapsed time.
        rchange = rsize * rate * dt

        a.rotation += rchange
        yield None

@task
def steerForSeparation(**kwargs):
    """Steer to maintain distance between self and neighbors.
    """
    bb = kwargs['blackboard']
    a = kwargs['actor']
    rate = kwargs['rate']
    while True:
        cn = a.closest_neighbor
        dt = bb['dt']

        abs_heading_to_neighbor = atan2(a.y-cn.y, a.x-cn.x)
        flee_heading = abs_heading_to_neighbor - pi
        my_heading = radians(a.rotation)

        # Find the rotation delta
        r = (flee_heading - my_heading) % pi - pi_2
        rsize = degrees(abs(r)) 

        # Factor in our turning rate and elapsed time.
        rchange = rsize * rate * dt

        a.rotation += rchange
        yield None

@task
def steerForCohesion(**kwargs):
    """Steer toward the average position of neighbors.
    """
    bb = kwargs['blackboard']
    a = kwargs['actor']
    rate = kwargs['rate']
    while True:
        np_x, np_y = a.neighbors_avg_pos
        dt = bb['dt']

        seek_heading = atan2(a.y-np_y, a.x-np_x)
        my_heading = radians(a.rotation)

        # Find the rotation delta
        r = (seek_heading - my_heading) % pi - pi_2
        rsize = degrees(abs(r)) 

        # Factor in our turning rate and elapsed time.
        rchange = rsize * rate * dt

        a.rotation += rchange
        yield None

class Boid(Sprite):
    _img = pyglet.resource.image('triangle.png')
    _img.anchor_x = _img.width / 2
    _img.anchor_y = _img.height / 2

    boids = []

    def __init__(self, blackboard):
        super(Boid, self).__init__(self._img)
        self.scale = 0.1
        self.schedule(self.update)
        self.bb = blackboard
        self.boids.append(self)
        self.opacity = 0
        self.do(FadeIn(2))
        self.speed = 40
        self.bounding_radius = 10
        self.bounding_radius_squared = 100

        self.tree = self.buildTree()

    def buildTree(self):
        """Build the behavior tree.
        """
        tree = parallel(move(actor=self),
                        steerToMatchHeading(actor=self, rate=1.5),
                        steerForSeparation(actor=self, rate=5),
                        steerForCohesion(actor=self, rate=1),
                        )
        return visit(tree, blackboard=self.bb)

    @property
    def neighbors(self):
        """Find the other boids in my neighborhood.
        """
        others = self.boids # [b for b in self.boids if b is not self]
        hood = (self.x, self.y, 1000) # neighborhood
        n = collide_single(hood, others)
        return n

    @property
    def neighbors_avg_pos(self):
        """Find the average position of my neighbors.
        """
        neighbors = self.neighbors
        num_n = float(len(neighbors))
        avg_x = sum((getX(n) for n in neighbors))/num_n
        avg_y = sum((getY(n) for n in neighbors))/num_n
        return avg_x, avg_y

    @property
    def closest_neighbor(self):
        """Find the closest neighbor.
        """
        neighbors = self.neighbors
        mx = self.x
        my = self.y
        dn = ((abs(mx-n.x)+abs(my-n.y), n) for n in neighbors)
        return sorted(dn)[0][1] # closest neighbor
        

    @property
    def neighbors_avg_heading(self):
        """Find the average heading of my neighbors.
        """
        neighbors = self.neighbors
        num_n = float(len(neighbors))
        avg_r = sum((getR(n) for n in neighbors))/num_n
        return avg_r

    def update(self, dt):
        self.bb['dt'] = dt
        self.tree.next()

class SpriteLayer(ScrollableLayer):
    is_event_handler = True
    
    def __init__(self):
        super(SpriteLayer, self).__init__()
        self.manager = ScrollingManager()
        self.manager.add(self)
        self.active = None
        self.schedule(self.update)
        self.blackboard = blackboard.Blackboard()


    def makeBoids(self, how_many):
        boids = []
        for x in xrange(how_many):
            boid = Boid(self.blackboard)
            boid.position = (random.randint(0, 1000),
                             random.randint(0, 1000))
            boid.rotation = random.randint(1, 360)
            self.add(boid)
            boids.append(boid)

        return boids

    def on_enter(self):
        super(SpriteLayer, self).on_enter()
        boid = self.makeBoids(10)[0]

        self.active = boid

        boid.position = 320, 200


    def update(self, dt):
        x, y = self.active.position
        self.manager.set_focus(x, y)

if __name__ == "__main__":
    director.init(resizable=True, caption="Owyl Behavior Tree Demo: Boids")
    s = Scene(SpriteLayer())
    director.run(s)
