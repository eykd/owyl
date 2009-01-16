# -*- coding: utf-8 -*-
"""
"""

import unittest

from math import radians, pi
pi_2 = pi/2.0

from cocos.director import director

from owyl import blackboard

import boids

class BoidsTest(unittest.TestCase):
    def setUp(self):
        director.init()
        self.bb = blackboard.Blackboard()
        

    def testFacing(self):
        """Can we find the rotation to a set of coordinates?
        """
        b = boids.Boid(self.bb)
        b.position = (0, 0)
        b.rotation = 0

        pos = (0, 5)
        expect = radians(0)
        rr = b.getFacing(*pos)
        self.assertEqual(rr, expect, 
                         "%s: got %s, expected %s" % (pos, rr, expect))

        pos = (5, 0)
        expect = radians(90)
        rr = b.getFacing(*pos)
        self.assertEqual(rr, expect, 
                         "%s: got %s, expected %s" % (pos, rr, expect))

        pos = (-5, 0)
        expect = radians(-90)
        rr = b.getFacing(*pos)
        self.assertEqual(rr, expect, 
                         "%s: got %s, expected %s" % (pos, rr, expect))

        pos = (0, -5)
        expect = radians(180)
        rr = b.getFacing(*pos)
        self.assertEqual(rr, expect, 
                         "%s: got %s, expected %s" % (pos, rr, expect))
        
    def testFindRotationDelta(self):
        """Can we find the change of rotation to match a facing?
        """
        b = boids.Boid(self.bb)

        current_match_delta = ((0, 90, 90),
                               (0, -90, -90),
                               (0, 180, 180),
                               (0, 270, -90),
                               (90, 180, 90),
                               (90, 0, -90),
                               (270, 180, -90),
                               (270, 0, 90),
                               (90, 720, -90),
                               )

        for current, match, delta in current_match_delta:
            current = radians(current)
            match = radians(match)
            delta = radians(delta)
            dr = b.findRotationDelta(current, match)
            self.assertEqual(dr, delta, 
                             "c: %s; m: %s; e: %s; got: %s" % (current,
                                                               match,
                                                               delta,
                                                               dr))
        

if __name__ == "__main__":
    try:
        import testoob
        testoob.main()
    except ImportError:
        unittest.main()
        
