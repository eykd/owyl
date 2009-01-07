# -*- coding: utf-8 -*-
"""owyl -- Owyl Behavior Trees

Behavior Trees are a form of U{hierarchical
logic<http://aigamedev.com/hierarchical-logic>}, and are quite useful
and flexible for implementing game AI.

Owyl implements a behavior tree using nested iterators/generators. A
top-level generator function, L{visit} (implementing the Visitor
Pattern), iterates through the tree, descending into child generators
as they are yielded, and passing yielded termination status values to
the parent generators.

Nested Generators
=================

  Tasks in the behavior tree are implemented as iterators (typically
  being generator functions wrapped by the L{task} decorator
  function).

  The first call to the task is at tree-building time. All passed
  arguments should be for static initialization. The task should
  return a factory function which itself should return an iterator.

  The factory function should accept **kwargs, which should be
  combined with the initialization keyword arugments and passed to the
  iterator at construction time.

  The iterator must yield values of None, True, False, or a child
  iterator. An iterator that yields child iterators must be ready to
  accept values yielded by the child. (See Termination Status Values,
  below.)


Termination Status Values
=========================

  As mentioned, iterators in the tree may yield values of None, True,
  False, or a child iterator:

    - B{None:} May be used to defer execution for another pass from the
      scheduler. An iterator yielding None will be queried again.

    - B{True:} Termination value signalling successful execution.

    - B{False:} Termination value signalling unsuccessful execution, or
      failure. Note: this is not considered an error value.

  True errors or exceptions should C{raise} the appropriate C{Error}
  or C{Exception}.
  
  For more information, see the discussion at
  U{http://aigamedev.com/hierarchical-logic/termination-status}.

For more information on Behavior Trees and hierarchical logic, please
see U{http://aigamedev.com/hierarchical-logic} and
U{http://aigamedev.com/hierarchical-logic/advice-2}.

Copyright 2008 David Eyk. All rights reserved.

$Author$\n
$Rev$\n
$Date$
"""

__author__ = "$Author$"[9:-2]
__revision__ = "$Rev$"[6:-2]
__date__ = "$Date$"[7:-2]

from core import *
from decorators import *
