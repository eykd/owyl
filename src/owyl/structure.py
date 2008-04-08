"""structure -- structural logic nodes for Behavior Trees.

http://aigamedev.com/hierarchical-logic

$Author$
$Rev$
$Date$
"""

__author__ = "$Author$"
__revision__ = "$Rev$"
__date__ = "$Date$"


from cellulose import InputCellDescriptor, ComputedCellDescriptor

import enum


class Root(BTDecorator):
    """Root behavior tree node.  

    Repeat child forever.  Pretend everything's okay, even if it's
    not. Report exceptions.
    """
    target = InputCellDescriptor()
    memory = InputCellDescriptor()
    blackboard = {}

    def __init__(self, target, child, initial_delay = 0.0):
        self.target = target
        self.memory = {}
        self.initial_delay = initial_delay
        self.counter = 0.0
        super(Root, self).__init__(child)

        if initial_delay > 0.0:
            self._step = self.step
            self.step = self._delayStep

    @classmethod
    def registerObject(cls, obj, category):
        """Register an object on the AI blackboard.
        """
        c_list = cls.blackboard.setdefault(category, [])
        c_list.append(obj)
        cls.blackboard.setdefault('all_objects', []).append(obj)

    @classmethod
    def deregisterObject(cls, obj, category):
        """Deregister an object registered on the AI blackboard.
        """
        c_list = cls.blackboard.setdefault(category, [])
        try:
            c_list.remove(obj)
        except ValueError:
            pass
        a_list = cls.blackboard.setdefault('all_objects', [])
        try:
            a_list.remove(obj)
        except ValueError:
            pass

    def _delayStep(self, dt):
        self.counter += dt
        if dt >= self.initial_delay:
            self.step = self._step
            self.step(dt)
        return RESULT.CONTINUE

    def step(self, dt):
        """Step through children.
        """
        try:
            self.child.step(dt)
        except Exception, e:
            print "Exception on", self.target
            traceback.print_exc()
        return RESULT.CONTINUE


class Sequence(BTNode):
    """Sequence behavior.
    """
    def __init__(self, *children, **kwargs):
        super(Sequence, self).__init__(*children, **kwargs)
        self.cursor = 0

    def reset(self):
        self.cursor = 0

    def ifChildSucceeds(self, child):
        self.cursor += 1
        if self.cursor >= len(self.children):
            self.reset()
            result = RESULT.SUCCEED
        else:
            result = RESULT.CONTINUE
        return result

    def ifChildFails(self, child):
        self.reset()
        return RESULT.FAIL

    def step(self, dt):
        """Step through children in sequence.
        """
        try:
            c = self.children[self.cursor]
            c_result = c.step(dt)
        except Exception, e:
            self.reset()
            raise e
            
        return self.RESULT_TABLE[c_result](c)


_getProbability = operator.attrgetter('probability')
def pickByProbability(candidates):
    picklist = []
    for c in candidates:
        for x in xrange(_getProbability(c)):
            picklist.append(c)
    return choice(picklist)

_getPriority = operator.attrgetter('priority')
def pickByPriority(candidates):
    return sorted(candidates, key=_getPriority)[-1]


class Selector(BTNode):
    """Selector behavior.

    Pick a child using the given picking strategy and run it.

    
    """
    def __init__(self, *children, **kwargs):
        super(Selector, self).__init__(*children, **kwargs)
        self.picker = kwargs.get('picker', pickByProbability)
        self.continue_child = False
        self.last_pick = None
    
    def ifChildContinues(self, child):
        self.continue_child = True
        return RESULT.CONTINUE

    def step(self, dt):
        if self.continue_child:
            self.continue_child = False
        else:
            self.last_pick = self.picker(self.children)
        
        c = self.last_pick
        c_result = c.step(dt)

        return self.RESULT_TABLE[c_result](c)


FAILURE_POLICY = enum.Enum('ALL', 'ONE')
COMPLETION_POLICY = enum.Enum('ALL', 'ONE')


class Parallel(_BTNode):
    """Parallel behaviors.

    Run all children in parallel (arbitrary sequential order).
    """
    def __init__(self, *children, **kwargs):
        super(Parallel, self).__init__(*children, **kwargs)

        self.failure_policy = kwargs.get('failure_policy',
                                         FAILURE_POLICY.ONE)
        self.completion_policy = kwargs.get('completion_policy',
                                         COMPLETION_POLICY.ALL)

        self.failed = 0
        self.completed = 0

        self.completed_children = []

        self.POLICY = {FAILURE_POLICY.ONE: self._policyOneFails,
                       FAILURE_POLICY.ALL: self._policyAllFail,
                       COMPLETION_POLICY.ONE: self._policyOneCompletes,
                       COMPLETION_POLICY.ALL: self._policyAllComplete}

    def reset(self):
        self.children.extend(self.completed_children)
        self.completed_children = []
        self.failed = 0
        self.completed = 0

    def _policyOneFails(self, child):
        self.reset()
        return RESULT.FAIL

    def _policyAllFail(self, child):
        if self.failed >= len(self.children)+len(self.completed_children):
            self.reset()
            result = RESULT.FAIL
        else:
            result = RESULT.CONTINUE
        return result

    def _policyOneCompletes(self, child):
        self.reset()
        return RESULT.SUCCEED

    def _policyAllComplete(self, child):
        if self.completed >= len(self.children)+len(self.completed_children):
            self.reset()
            result = RESULT.SUCCEED
        else: 
            result = RESULT.CONTINUE
        return result

    def ifChildFails(self, child):
        self.failed += 1
        self.completed += 1
        self.children.remove(child)
        self.completed_children.append(child)
        return min(self.POLICY[self.failure_policy](child),
                   self.POLICY[self.completion_policy](child))

    def ifChildSucceeds(self, child):
        self.completed += 1
        self.children.remove(child)
        self.completed_children.append(child)
        return self.POLICY[self.completion_policy](child)

    def step(self, dt):
        results = []
        for c in tuple(self.children):
            c_result = c.step(dt)
            result = self.RESULT_TABLE[c_result](c)
            results.append(result)
        results.sort(reverse=True)
        return results[-1]

