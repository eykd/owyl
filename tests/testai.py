# -*- coding: utf-8 -*-
"""testai -- tests for Behavior Tree AI.

$Author$
$Rev: 871 $
$Date: 2008-04-02 19:38:18 -0500 (Wed, 02 Apr 2008) $
"""

__author__ = "$Author$"
__revision__ = "$Rev: 871 $"
__date__ = "$Date: 2008-04-02 19:38:18 -0500 (Wed, 02 Apr 2008) $"

import unittest
import operator

from owyl import ai
from owyl.ai import Log
from owyl.ai import RESULT
from owyl.ai import Root, Sequence, Parallel
from owyl.ai import Selector, pickByPriority, pickByProbability
from owyl.ai import RepeatUntilFail, RepeatUntilSucceed
from owyl.ai import Succeed, Fail, Error

class LoggingCase(unittest.TestCase):
    def log(self, child, result):
        self.results.append(result)


class RootTest(LoggingCase):
    """Tests for root node of behavior tree.
    """
    def setUp(self):
        self.results = []

    def testRoot(self):
        """Does the root behavior work?
        """
        r = Root(self,
                    Log(Succeed(),
                           logFunc=self.log))

        n = 1000
        for x in xrange(n):
            r.step(1)
        
        self.assertEqual(len(self.results), n)

        self.assertEqual(r.step(1), RESULT.CONTINUE)

class SequenceTest(LoggingCase):
    """Tests for sequences.
    """
    def setUp(self):
        self.results = []
        self.root = Root(self,
                            Log(Sequence(Succeed(),
                                               Succeed(), 
                                               Succeed(), 
                                               Fail(), 
                                               Error(),
                                               Succeed()),
                                   self.log))

    def testSequenceFailure(self):
        n = 4
        self.root.stepTimes(n, n)

        self.assertEqual(self.results[-1], RESULT.FAIL)
        self.assertEqual(self.root.child.child.cursor, 0)

    def testSequenceContinue(self):
        r = self.root.step(1)
        self.assertEqual(r, RESULT.CONTINUE)

    def testSequenceError(self):
        self.root.child.child.children.pop(-2)
        n = 4
        self.root.stepTimes(n, n)

        # Exception should not get past the self.root, but seq. should reset.
        self.assertEqual(self.root.child.child.cursor, 0)

    def testSequenceSuccess(self):
        self.root.child.child.children.pop(-2)
        self.root.child.child.children.pop(-2)
        n = 20
        self.root.stepTimes(n, n)

        self.assert_(RESULT.SUCCEED in self.results)
        self.assert_(RESULT.CONTINUE in self.results)
        self.assert_(RESULT.FAIL not in self.results)

class SelectorTest(LoggingCase):
    """Tests for selectors.
    """
    def setUp(self):
        self.results = []

        self.selections = {'succeed':Succeed(),
                           'fail': Fail()}

        self.root = Root(self,
                            Log(Selector(*self.selections.values()),
                                   self.log))

    def testSelectPriority(self):
        """Can we select behaviors by priority?
        """
        self.root.child.child.picker = pickByPriority

        self.selections['succeed'].priority = 10

        self.root.step(1)
        self.assertEqual(self.results[-1], RESULT.SUCCEED)

        self.selections['succeed'].priority = 1
        self.selections['fail'].priority = 10

        self.root.step(1)
        self.assertEqual(self.results[-1], RESULT.FAIL)

    def testSelectProbability(self):
        """Can we select behavior by probability?
        """
        self.selections['succeed'].probability = 2
        self.selections['fail'].probability = 2
        n = 10000
        self.root.stepTimes(n, n)
        failures = self.results.count(RESULT.FAIL)
        successes = self.results.count(RESULT.SUCCEED)

        n = abs(failures/float(successes)-1)

        self.assertAlmostEqual(n, 0.0, 1)

        self.selections['succeed'].probability = 4
        self.selections['fail'].probability = 2
        n = 10000
        self.root.stepTimes(n, n)
        failures = self.results.count(RESULT.FAIL)
        successes = self.results.count(RESULT.SUCCEED)

        n = abs(failures/float(successes)-1)

        self.assertAlmostEqual(n, 0.25, 1)


class ParallelTest(LoggingCase):
    def setUp(self):
        self.results = []

    def doPrint(self, p):
        pc = [(c.__class__.__name__, c.count, c.after) for c in p.children]
        f = "Failed: %s" % p.failed
        c = "Completed: %s" % p.completed
        print pc
        print f
        print c
        print "Last result: %s" % self.results[-1]
        print

    def testFailOne(self):
        p = Parallel(Succeed(after=1),
                     Succeed(after=2),
                     Fail(after=3),
                     Succeed(after=4),
                     completion_policy=ai.COMPLETION_POLICY.ALL,
                     failure_policy=ai.FAILURE_POLICY.ONE)

        root = Root(self,
                    Log(p, self.log)
                    )
        
        root.step(1)
        self.assertEqual(p.failed, 0)
        self.assertEqual(p.completed, 0)

        root.step(1)
        self.assertEqual(p.failed, 0)
        self.assertEqual(p.completed, 1)

        root.step(1)
        self.assertEqual(p.failed, 0)
        self.assertEqual(p.completed, 2)

        # This next step fails
        root.step(1)
        # But the parallel resets.
        self.assertEqual(p.failed, 0)
        self.assertEqual(p.completed, 0)

        self.assertEqual(self.results[-1], RESULT.FAIL)

    def testCompleteAll(self):
        p = Parallel(Succeed(after=1),
                     Succeed(after=2),
                     Succeed(after=3),
                     completion_policy=ai.COMPLETION_POLICY.ALL,
                     failure_policy=ai.FAILURE_POLICY.ONE)

        root = Root(self,
                    Log(p, self.log)
                    )
        
        root.step(1)
        self.assertEqual(p.failed, 0)
        self.assertEqual(p.completed, 0)

        root.step(1)
        self.assertEqual(p.failed, 0)
        self.assertEqual(p.completed, 1)

        root.step(1)
        self.assertEqual(p.failed, 0)
        self.assertEqual(p.completed, 2)

        # This next step succeeds
        root.step(1)
        # And the parallel resets.
        self.assertEqual(p.failed, 0)
        self.assertEqual(p.completed, 0)

        self.assertEqual(self.results[-1], RESULT.SUCCEED)

    def testFailAll(self):
        p = Parallel(Fail(after=1),
                     Fail(after=2),
                     Fail(after=3),
                     completion_policy=ai.COMPLETION_POLICY.ALL,
                     failure_policy=ai.FAILURE_POLICY.ALL)

        root = Root(self,
                    Log(p, self.log)
                    )
        
        root.step(1)
        self.assertEqual(p.failed, 0)
        self.assertEqual(p.completed, 0)

        root.step(1)
        self.assertEqual(p.failed, 1)
        self.assertEqual(p.completed, 1)

        root.step(1)
        self.assertEqual(p.failed, 2)
        self.assertEqual(p.completed, 2)

        root.step(1)
        # And the parallel resets.
        self.assertEqual(p.failed, 0)
        self.assertEqual(p.completed, 0)

        self.assertEqual(self.results[-1], RESULT.FAIL)

    def testCompleteOne(self):
        p = Parallel(Succeed(after=1),
                     Succeed(after=2),
                     Fail(after=3),
                     Succeed(after=4),
                     completion_policy=ai.COMPLETION_POLICY.ONE,
                     failure_policy=ai.FAILURE_POLICY.ALL)

        root = Root(self,
                    Log(p, self.log)
                    )
        
        root.step(1)
        self.assertEqual(p.failed, 0)
        self.assertEqual(p.completed, 0)

        # One completes, and the par gets reset.
        root.step(1)
        self.assertEqual(p.failed, 0)
        self.assertEqual(p.completed, 0)

        self.assertEqual(self.results[-1], RESULT.SUCCEED)


if __name__ == "__main__":
    import testoob
    testoob.main()
