import unittest

from hm_06_test_add import TestAdd

suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(TestAdd))

unittest.TextTestRunner().run(suite)