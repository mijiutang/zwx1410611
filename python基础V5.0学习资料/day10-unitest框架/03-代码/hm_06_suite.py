import unittest

from hm_06_skip import TestSkip

suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(TestSkip))

unittest.TextTestRunner().run(suite)