import unittest

from tools import add


class TestAdd(unittest.TestCase):
    def test_1(self):
        self.assertEqual(2, add(1, 1))

    def test_2(self):
        self.assertEqual(3, add(1, 2))

    def test_3(self):
        self.assertEqual(7, add(3, 4))

    def test_4(self):
        self.assertEqual(9, add(4, 5))