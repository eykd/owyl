# -*- coding: utf-8 -*-
"""testowyl -- some tests for owyl.



Copyright 2008 David Eyk. All rights reserved.

$Author$\n
$Rev: 0 $\n
$Date: 0 $
"""

__author__ = "$Author$"[9:-2]
__revision__ = "$Rev: 0 $"[6:-2]
__date__ = "$Date: Today $"[7:-2]

import unittest

import owyl

class OwylTest(unittest.TestCase):
    def testSucceed(self):
        """Can we succeed?
        """
        s = owyl.succeed()
        t = s()
        self.assertEqual(t.next(), True)
        self.assertRaises(StopIteration, t.next)

        t = s()
        self.assertEqual(t.next(), True)
        self.assertRaises(StopIteration, t.next)

    def testFail(self):
        """Can we fail?
        """
        s = owyl.fail()
        t = s()
        self.assertEqual(t.next(), False)
        self.assertRaises(StopIteration, t.next)

        t = s()
        self.assertEqual(t.next(), False)
        self.assertRaises(StopIteration, t.next)


    def testVisitSequenceSuccess(self):
        """Can we visit a successful sequence?
        """
        tree = owyl.sequence(owyl.succeed(),
                             owyl.succeed(),
                             owyl.succeed())

        v = owyl.visit(tree)

        results =  [x for x in v if x is not None]
        self.assertEqual(results, [True, True, True, True])

        v = owyl.visit(tree)

        results =  [x for x in v if x is not None]
        self.assertEqual(results, [True, True, True, True])

    def testVisitSequenceFailure(self):
        """Can we visit a failing sequence?
        """
        tree = owyl.sequence(owyl.succeed(),
                             owyl.succeed(),
                             owyl.fail(),
                             owyl.succeed())

        v = owyl.visit(tree)

        results =  [x for x in v if x is not None]
        self.assertEqual(results, [True, True, False, False])

        v = owyl.visit(tree)

        results =  [x for x in v if x is not None]
        self.assertEqual(results, [True, True, False, False])
        
    def testVisitSelectorSuccess(self):
        """Can we visit a successful selector?
        """
        tree = owyl.selector(owyl.fail(),
                             owyl.fail(),
                             owyl.succeed(),
                             owyl.fail())

        v = owyl.visit(tree)

        results =  [x for x in v if x is not None]
        self.assertEqual(results, [False, False, True, True])

        v = owyl.visit(tree)

        results =  [x for x in v if x is not None]
        self.assertEqual(results, [False, False, True, True])

    def testVisitSelectorFailure(self):
        """Can we visit a failing selector?
        """
        tree = owyl.selector(owyl.fail(),
                             owyl.fail(),
                             owyl.fail())

        v = owyl.visit(tree)

        results =  [x for x in v if x is not None]
        self.assertEqual(results, [False, False, False, False])

        v = owyl.visit(tree)

        results =  [x for x in v if x is not None]
        self.assertEqual(results, [False, False, False, False])

    def testParallel_AllSucceed_Success(self):
        """Can we visit a suceeding parallel (all succeed)?
        """
        tree = owyl.parallel(owyl.sequence(owyl.succeed(),
                                           owyl.succeed()),
                             owyl.sequence(owyl.succeed(),
                                           owyl.succeed()),
                             policy=owyl.PARALLEL_SUCCESS.REQUIRE_ALL)
        v = owyl.visit(tree)

        results =  [x for x in v if x is not None]
        self.assertEqual(results, [True,])

        v = owyl.visit(tree)

        results =  [x for x in v if x is not None]
        self.assertEqual(results, [True,])

    def testParallel_OneSucceeds_Success(self):
        """Can we visit a suceeding parallel (one succeeds)?
        """
        tree = owyl.parallel(owyl.sequence(owyl.succeed(),
                                           owyl.succeed()),
                             owyl.sequence(owyl.succeed(),
                                           owyl.fail()),
                             policy=owyl.PARALLEL_SUCCESS.REQUIRE_ONE)
        v = owyl.visit(tree)

        results =  [x for x in v if x is not None]
        self.assertEqual(results, [True,])

        v = owyl.visit(tree)

        results =  [x for x in v if x is not None]
        self.assertEqual(results, [True,])

    def testParallel_AllSucceed_Failure(self):
        """Can we visit a failing parallel (all succeed)?
        """
        tree = owyl.parallel(owyl.sequence(owyl.succeed(),
                                           owyl.fail()),
                             owyl.sequence(owyl.succeed(),
                                           owyl.succeed()),
                             policy=owyl.PARALLEL_SUCCESS.REQUIRE_ALL)
        v = owyl.visit(tree)

        results =  [x for x in v if x is not None]
        self.assertEqual(results, [False,])

    def testParallel_OneSucceeds_Failure(self):
        """Can we visit a failing parallel (one succeeds)?
        """
        tree = owyl.parallel(owyl.sequence(owyl.fail(),
                                           owyl.fail()),
                             owyl.sequence(owyl.fail(),
                                           owyl.fail()),
                             policy=owyl.PARALLEL_SUCCESS.REQUIRE_ONE)
        v = owyl.visit(tree)

        results =  [x for x in v if x is not None]
        self.assertEqual(results, [False,])

        v = owyl.visit(tree)

        results =  [x for x in v if x is not None]
        self.assertEqual(results, [False,])



if __name__ == "__main__":
    import testoob
    testoob.main()
