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
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

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
        self.assertEqual(next(t), True)
        self.assertRaises(StopIteration, lambda: next(t))

        t = s()
        self.assertEqual(next(t), True)
        self.assertRaises(StopIteration, lambda: next(t))

    def testFail(self):
        """Can we fail?
        """
        s = owyl.fail()
        t = s()
        self.assertEqual(next(t), False)
        self.assertRaises(StopIteration, lambda: next(t))

        t = s()
        self.assertEqual(next(t), False)
        self.assertRaises(StopIteration, lambda: next(t))

    def testVisitSequenceSuccess(self):
        """Can we visit a successful sequence?
        """
        tree = owyl.sequence(owyl.succeed(),
                             owyl.succeed(),
                             owyl.succeed())

        v = owyl.visit(tree)

        results = [x for x in v if x is not None]
        self.assertEqual(results, [True, True, True, True])

        v = owyl.visit(tree)

        results = [x for x in v if x is not None]
        self.assertEqual(results, [True, True, True, True])

    def testVisitSequenceFailure(self):
        """Can we visit a failing sequence?
        """
        tree = owyl.sequence(owyl.succeed(),
                             owyl.succeed(),
                             owyl.fail(),
                             owyl.succeed())

        v = owyl.visit(tree)

        results = [x for x in v if x is not None]
        self.assertEqual(results, [True, True, False, False])

        v = owyl.visit(tree)

        results = [x for x in v if x is not None]
        self.assertEqual(results, [True, True, False, False])
        
    def testVisitSelectorSuccess(self):
        """Can we visit a successful selector?
        """
        tree = owyl.selector(owyl.fail(),
                             owyl.fail(),
                             owyl.succeed(),
                             owyl.fail())

        v = owyl.visit(tree)

        results = [x for x in v if x is not None]
        self.assertEqual(results, [False, False, True, True])

        v = owyl.visit(tree)

        results = [x for x in v if x is not None]
        self.assertEqual(results, [False, False, True, True])

    def testVisitSelectorFailure(self):
        """Can we visit a failing selector?
        """
        tree = owyl.selector(owyl.fail(),
                             owyl.fail(),
                             owyl.fail())

        v = owyl.visit(tree)

        results = [x for x in v if x is not None]
        self.assertEqual(results, [False, False, False, False])

        v = owyl.visit(tree)

        results = [x for x in v if x is not None]
        self.assertEqual(results, [False, False, False, False])

    def testParallel_AllSucceed_Success(self):
        """Can we visit a succeeding parallel (all succeed)?
        """
        tree = owyl.parallel(owyl.sequence(owyl.succeed(),
                                           owyl.succeed()),
                             owyl.sequence(owyl.succeed(),
                                           owyl.succeed()),
                             policy=owyl.PARALLEL_SUCCESS.REQUIRE_ALL)
        v = owyl.visit(tree)

        results = [x for x in v if x is not None]
        self.assertEqual(results, [True])

        v = owyl.visit(tree)

        results = [x for x in v if x is not None]
        self.assertEqual(results, [True])

    def testParallel_OneSucceeds_Success(self):
        """Can we visit a suceeding parallel (one succeeds)?
        """
        tree = owyl.parallel(owyl.sequence(owyl.succeed(),
                                           owyl.succeed()),
                             owyl.sequence(owyl.succeed(),
                                           owyl.fail()),
                             policy=owyl.PARALLEL_SUCCESS.REQUIRE_ONE)
        v = owyl.visit(tree)

        results = [x for x in v if x is not None]
        self.assertEqual(results, [True])

        v = owyl.visit(tree)

        results = [x for x in v if x is not None]
        self.assertEqual(results, [True])

    def testParallel_AllSucceed_Failure(self):
        """Can we visit a failing parallel (all succeed)?
        """
        tree = owyl.parallel(owyl.sequence(owyl.succeed(),
                                           owyl.fail()),
                             owyl.sequence(owyl.succeed(),
                                           owyl.succeed()),
                             policy=owyl.PARALLEL_SUCCESS.REQUIRE_ALL)
        v = owyl.visit(tree)

        results = [x for x in v if x is not None]
        self.assertEqual(results, [False])

    def testParallel_OneSucceeds_Failure(self):
        """Can we visit a failing parallel (one succeeds)?
        """
        tree = owyl.parallel(owyl.sequence(owyl.fail(),
                                           owyl.fail()),
                             owyl.sequence(owyl.fail(),
                                           owyl.fail()),
                             policy=owyl.PARALLEL_SUCCESS.REQUIRE_ONE)
        v = owyl.visit(tree)

        results = [x for x in v if x is not None]
        self.assertEqual(results, [False])

        v = owyl.visit(tree)

        results = [x for x in v if x is not None]
        self.assertEqual(results, [False])

    def testThrow(self):
        """Can we throw an exception within the tree?
        """
        tree = owyl.sequence(owyl.succeed(),
                             owyl.succeed(),
                             owyl.throw(throws=ValueError,
                                        throws_message="AUGH!!"),
                             )
        v = owyl.visit(tree)
        self.assertEqual(next(v), True)
        self.assertEqual(next(v), True)
        self.assertRaises(ValueError, lambda: next(v))

        v = owyl.visit(tree)
        self.assertEqual(next(v), True)
        self.assertEqual(next(v), True)
        self.assertRaises(ValueError, lambda: next(v))

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
        self.assertEqual(next(v), True)
        self.assertEqual(next(v), True)
        self.assertEqual(next(v), True)

        v = owyl.visit(tree)
        self.assertEqual(next(v), True)
        self.assertEqual(next(v), True)
        self.assertEqual(next(v), True)

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
        self.assertEqual(next(v), True)
        self.assertEqual(next(v), True)
        self.assertRaises(ValueError, lambda: next(v))

        v = owyl.visit(tree)
        self.assertEqual(next(v), True)
        self.assertEqual(next(v), True)
        self.assertRaises(ValueError, lambda: next(v))

    def testIdentity(self):
        """Does identity pass on return values unchanged?
        """
        # Succeed after 5 iterations.
        after = 5
        tree = owyl.identity(owyl.succeedAfter(after=after))

        v = owyl.visit(tree)
        for x in range(after):
            self.assertEqual(next(v), None)
        self.assertEqual(next(v), True)

        v = owyl.visit(tree)
        for x in range(after):
            self.assertEqual(next(v), None)
        self.assertEqual(next(v), True)

        tree = owyl.identity(owyl.failAfter(after=after))

        v = owyl.visit(tree)
        for x in range(after):
            self.assertEqual(next(v), None)
        self.assertEqual(next(v), False)

        v = owyl.visit(tree)
        for x in range(after):
            self.assertEqual(next(v), None)
        self.assertEqual(next(v), False)

    def testCheckBB(self):
        """Can we check a value on a blackboard?
        """
        value = "foo"
        checker = lambda x: x == value

        bb = blackboard.Blackboard('test', value=value)
        tree = blackboard.checkBB(key='value',
                                  check=checker)
        
        # Note that we can pass in the blackboard at run-time.
        v = owyl.visit(tree, blackboard=bb)

        # Check should succeed.
        self.assertEqual(next(v), True)

        v = owyl.visit(tree, blackboard=bb)
        self.assertEqual(next(v), True)

        bb['value'] = 'bar'

        # Check should now fail.
        v = owyl.visit(tree, blackboard=bb)
        self.assertEqual(next(v), False)

        v = owyl.visit(tree, blackboard=bb)
        self.assertEqual(next(v), False)

    def testSetBB(self):
        """Can we set a value on a blackboard?
        """
        value = 'foo'
        checker = lambda x: x == value

        bb = blackboard.Blackboard('test', value='bar')
        tree = owyl.sequence(blackboard.setBB(key="value",
                                              value=value),
                             blackboard.checkBB(key='value',
                                                check=checker)
                             )
        
        # Note that we can pass in the blackboard at run-time.
        v = owyl.visit(tree, blackboard=bb)

        # Sequence will succeed if the check succeeds.
        result = [x for x in v][-1]
        self.assertEqual(result, True)

        v = owyl.visit(tree, blackboard=bb)
        result = [x for x in v][-1]
        self.assertEqual(result, True)

    def testRepeatUntilSucceed(self):
        """Can we repeat a behavior until it succeeds?
        """
        bb = blackboard.Blackboard('test', )  # 'value' defaults to None.
        checker = lambda x: x is not None

        parallel = owyl.parallel
        repeat = owyl.repeatUntilSucceed
        checkBB = blackboard.checkBB
        setBB = blackboard.setBB

        tree = parallel(repeat(checkBB(key='value',
                                       check=checker),
                               final_value=True),

                        # That should fail until this sets the value:
                        owyl.selector(owyl.fail(),
                                      owyl.fail(),
                                      setBB(key='value',
                                            value='foo')),
                        policy=owyl.PARALLEL_SUCCESS.REQUIRE_ALL)

        v = owyl.visit(tree, blackboard=bb)
        results = [x for x in v]
        result = results[-1]
        self.assertEqual(result, True)

        # Need to reset the blackboard to get the same results.
        bb = blackboard.Blackboard('test', )  # 'value' defaults to None.
        v = owyl.visit(tree, blackboard=bb)
        results = [x for x in v]
        result = results[-1]
        self.assertEqual(result, True)

    def testRepeatUntilFail(self):
        """Can we repeat a behavior until it fails?
        """
        bb = blackboard.Blackboard('test', value="foo")
        checker = lambda x: x and True or False  # must eval to True

        parallel = owyl.parallel
        repeat = owyl.repeatUntilFail
        checkBB = blackboard.checkBB
        setBB = blackboard.setBB

        tree = parallel(repeat(checkBB(key='value',
                                            check=checker),
                                    final_value=True),

                        # That should succeed until this sets the value:
                        owyl.selector(owyl.fail(),
                                      owyl.fail(),
                                      setBB(key='value',
                                            value=None)),
                        policy=owyl.PARALLEL_SUCCESS.REQUIRE_ALL)

        v = owyl.visit(tree, blackboard=bb)
        results = [x for x in v]
        result = results[-1]
        self.assertEqual(result, True)

        # Need to reset the blackboard to get the same results.
        bb = blackboard.Blackboard('test', value="foo")
        v = owyl.visit(tree, blackboard=bb)
        results = [x for x in v]
        result = results[-1]
        self.assertEqual(result, True)


if __name__ == "__main__":
    runner = unittest
    try:
        import testoob
        runner = testoob
    except ImportError:
        pass
    runner.main()
