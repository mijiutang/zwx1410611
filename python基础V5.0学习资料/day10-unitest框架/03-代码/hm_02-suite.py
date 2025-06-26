import unittest

from hm_02_assert import TestAssert

suite = unittest.TestSuite()

suite.addTest(unittest.makeSuite(TestAssert))
unittest.TextTestRunner().run(suite)