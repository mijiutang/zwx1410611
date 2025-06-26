import unittest

from tools import add


class TestAdd(unittest.TestCase):
    def test_1(self):
        """1,1,2"""
        if 2 == add(1, 1):
            print(f'用例 {1}, {1}, {2}通过')
        else:
            print(f'用例 {1}, {1}, {2}不通过')

    def test_2(self):
        if 3 == add(1, 2):
            print(f'用例 {1}, {2}, {3}通过')
        else:
            print(f'用例 {1}, {2}, {3}不通过')

    def test_3(self):
        if 7 == add(3, 4):
            print(f'用例 {3}, {4}, {7}通过')
        else:
            print(f'用例 {3}, {4}, {7}不通过')

    def test_4(self):
        if 9 == add(4, 5):
            print(f'用例 {4}, {5}, {9}通过')
        else:
            print(f'用例 {4}, {5}, {9}不通过')
