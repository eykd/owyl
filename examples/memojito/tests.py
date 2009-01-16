import os, sys, unittest
try:
    from zope.testing import doctest
except ImportError:
    import doctest
    
optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS

def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('README.txt', package="memojito",
                             optionflags=optionflags),
        ))

if __name__=="__main__":
    import unittest
    unittest.TextTestRunner().run(test_suite())
