# -*- coding: utf-8 -*-
"""example1 -- Example 1 of Owyl behavior trees.



Copyright 2008 David Eyk. All rights reserved.

$Author$\n
$Rev: 0 $\n
$Date: 0 $
"""

__author__ = "$Author$"[9:-2]
__revision__ = "$Rev: 0 $"[6:-2]
__date__ = "$Date: Today $"[7:-2]

import os

import random
from math import radians, sin, cos

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


@task
def move(**kwargs):
    """Move the actor forward perpetually.

    @keyword dt: delta time
    @keyword actor: actor to move
    """
    bb = kwargs['blackboard']
    a = kwargs['actor']
    while True:
        dt = bb['dt']
        r = radians(a.rotation)
        s = dt * a.speed
        a.x += sin(r) * s
        a.y += cos(r) * s
        yield None


class Boid(Sprite):
    _img = pyglet.resource.image('triangle.png')
    _img.anchor_x = _img.width / 2
    _img.anchor_y = _img.height / 2

    boids = []
    others = property(lambda self: [b for b in self.boids if b is not self])

    def __init__(self, blackboard):
        super(Boid, self).__init__(self._img)
        self.scale = 0.1
        self.schedule(self.update)
        self.bb = blackboard
        self.boids.append(self)
        self.opacity = 0
        self.do(FadeIn(2))
        self.speed = 20

        self.tree = self.buildTree()

    def buildTree(self):
        """Build the behavior tree.
        """
        tree = parallel(move(actor=self),
                        )
        return visit(tree, blackboard=self.bb)

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
            boid.position = (random.randint(50, 750),
                             random.randint(50, 550))
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
