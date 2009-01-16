# -*- coding: utf-8 -*-
"""steering -- common steering helpers.


Copyright 2008 David Eyk. All rights reserved.

$Author$\n
$Rev: 41 $\n
$Date: 2009-01-15 22:37:46 -0600 (Thu, 15 Jan 2009) $
"""

__author__ = "$Author$"[9:-2]
__revision__ = "$Rev: 41 $"[6:-2]
__date__ = "$Date: 2009-01-15 22:37:46 -0600 (Thu, 15 Jan 2009) $"[7:-2]

from cocos.sprite import Sprite

from math import atan2, pi
pi_2 = pi*2.0
pi_1_2 = pi/2.0
pi_1_4 = pi/4.0
pi_3_4 = (pi*3)/4


class Steerable(Sprite):
    """A steerable sprite, with helpers for figuring rotations and vectors.
    """
    def __init__(self, image):
        super(Steerable, self).__init__(self._img)
        self.speed = 0

        self.bounding_radius = 1
        self.bounding_radius_squared = 1
        
        self.personal_radius = 1

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


