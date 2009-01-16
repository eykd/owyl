==========
 memojito
==========

memojito is included with the Owyl examples for simplicity of
packaging. Please see memojito's licensing information in LICENSE.txt.

Memojito's full distribution may be found at
<http://pypi.python.org/pypi/memojito>.

memojito provides a simple set of decorators for
storing call returns as memos on an object.

Let's try it out w/ a dummy class::

>>> import memojito
>>> class MyMsg(object):
...     bang='!'
...     @memojito.memoizedproperty
...     def txt2(self):
...         #extreme intense calculation
...         return '%s world' %self.txt1
...         
...     @memojito.memoize
...     def getMsg(self, to, **instruction):
...         lst = ['%s--%s' %t for t in instruction.items()]
...         instxt = ' '.join(lst)
...         return ("%s: %s%s %s" %(to, self.txt2, self.bang, instxt)).strip()
...     
...     @memojito.clearbefore
...     def clearbefore(self):
...         return self.txt2
...     
...     @memojito.clearafter
...     def clearafter(self):
...         return self.txt2
...     
...     def __init__(self, txt1):
...         self.txt1 = txt1

>>> msg = MyMsg('hello')
>>> msg.txt2
'hello world'

>>> msg.txt1 = 'goodbye cruel'

Even though we've twiddled txt1, txt2 is not recalculated::

>>> msg.txt2
'hello world'

The memo is stored by a hast of the method's name, args,
and a frozenset of any kwargs.

>>> key = ('txt2', (msg,), frozenset([]))
>>> msg._memojito_[hash(key)]
'hello world'

The clear after decorator with clear the memos after
returning the methods value::

>>> msg.clearafter()
'hello world'

The clear before does the opposite, allowing new values to be
calculated::

>>> msg.clearafter()
'goodbye cruel world'

memojito supports memoization of multiple signatures as long as all
signature values are hashable::

>>> print msg.getMsg('Ernest')
Ernest: goodbye cruel world!

>>> print msg.getMsg('J.D.', **{'raise':'roofbeams'})
J.D.: goodbye cruel world! raise--roofbeams

We can alter data underneath, but nothing changes::

>>> msg.txt1 = 'sound and fury'
>>> print msg.getMsg('J.D.', **{'raise':'roofbeams'})
J.D.: goodbye cruel world! raise--roofbeams

>>> print msg.getMsg('Ernest')
Ernest: goodbye cruel world!

If we alter the signature, our msg is recalculated, but since mst.txt2
is a memo, only the values passed in change::

>>> ins = {'tale':'told by idiot', 'signify':'nothing'}
>>> print msg.getMsg('Bill F.', **ins)
Bill F.: goodbye cruel world! tale--told by idiot signify--nothing

>>> print msg.getMsg('J.D.', **{'catcher':'rye'})
J.D.: goodbye cruel world! catcher--rye

If change the bang, the memo remains the same::

>>> msg.bang='#!'
>>> print msg.getMsg('J.D.', **{'catcher':'rye'})
J.D.: goodbye cruel world! catcher--rye

>>> print msg.getMsg('Ernest')
Ernest: goodbye cruel world!

clearing works the same as for properties::

>>> print msg.clearafter()
goodbye cruel world

Our shebang appears::

>>> print msg.getMsg('Ernest')
Ernest: sound and fury world#!

Our message to faulkner now is semantically correct::

>>> ins = dict(tale='told by idiot', signify='nothing')
>>> print msg.getMsg('Bill F.', **ins)
Bill F.: sound and fury world#! tale--told by idiot signify--nothing
