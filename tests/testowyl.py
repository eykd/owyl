# -*- coding: utf-8 -*-
"""testowyl -- some tests for owyl.

Copyright 2008 David Eyk. All rights reserved.

$Author$\n
$Rev$\n
$Date$
"""

__author__ = "$Author$"[9:-2]
__revision__ = "$Rev$"[6:-2]
__date__ = "$Date$"[7:-2]

import unittest

import owyl
from owyl import blackboard

class OwylTests(unittest.TestCase):
    """Tests for Owyl.

    Note: tests should run the tree twice to make sure that the
    constructed tree is re-usable.
    """
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


    def testThrow(self):
        """Can we throw an exception within the tree?
        """
        tree = owyl.sequence(owyl.succeed(),
                             owyl.succeed(),
                             owyl.throw(throws=ValueError,
                                        throws_message="AUGH!!"),
                             )
        v = owyl.visit(tree)
        self.assertEqual(v.next(), True)
        self.assertEqual(v.next(), True)
        self.assertRaises(ValueError, v.next)

        v = owyl.visit(tree)
        self.assertEqual(v.next(), True)
        self.assertEqual(v.next(), True)
        self.assertRaises(ValueError, v.next)


    def testCatch(self):
        """Can we catch an exception thrown within the tree?
        """
        tree = owyl.sequence(owyl.succeed(),
                             owyl.succeed(),
                             owyl.catch(owyl.throw(throws=ValueError,
                                                   throws_message="AUGH!!"),
                                        caught=ValueError, 
                                        branch=owyl.succeed())
                             )
        v = owyl.visit(tree)
        self.assertEqual(v.next(), True)
        self.assertEqual(v.next(), True)
        self.assertEqual(v.next(), True)

        v = owyl.visit(tree)
        self.assertEqual(v.next(), True)
        self.assertEqual(v.next(), True)
        self.assertEqual(v.next(), True)


    def testCatchIgnoresOthers(self):
        """Does catch ignore other exceptions thrown within the tree?
        """
        tree = owyl.sequence(owyl.succeed(),
                             owyl.succeed(),
                             owyl.catch(owyl.throw(throws=ValueError,
                                                   throws_message="AUGH!!"),
                                        caught=IndexError, 
                                        branch=owyl.succeed())
                             )
        v = owyl.visit(tree)
        self.assertEqual(v.next(), True)
        self.assertEqual(v.next(), True)
        self.assertRaises(ValueError, v.next)

        v = owyl.visit(tree)
        self.assertEqual(v.next(), True)
        self.assertEqual(v.next(), True)
        self.assertRaises(ValueError, v.next)


    def testIdentity(self):
        """Does identity pass on return values unchanged?
        """
        # Succeed after 5 iterations.
        after = 5
        tree = owyl.identity(owyl.succeedAfter(after=after))

        v = owyl.visit(tree)
        for x in xrange(after):
            self.assertEqual(v.next(), None)
        self.assertEqual(v.next(), True)

        v = owyl.visit(tree)
        for x in xrange(after):
            self.assertEqual(v.next(), None)
        self.assertEqual(v.next(), True)

        tree = owyl.identity(owyl.failAfter(after=after))

        v = owyl.visit(tree)
        for x in xrange(after):
            self.assertEqual(v.next(), None)
        self.assertEqual(v.next(), False)

        v = owyl.visit(tree)
        for x in xrange(after):
            self.assertEqual(v.next(), None)
        self.assertEqual(v.next(), False)


        

if __name__ == "__main__":
    runner = unittest
    try:
        import testoob
        runner = testoob
    except ImportError:
        pass
    runner.main()
