import unittest

from common.read_data import build_add_data_2
from tools import add
from parameterized import parameterized

data = [(1, 1, 2), (1, 2, 3), (2, 3, 5), (4, 5, 9)]


class TestAdd(unittest.TestCase):
    # @parameterized.expand(build_add_data())
    # @parameterized.expand(build_add_data_1())
    @parameterized.expand(build_add_data_2())
    def test_add(self, a, b, expect):
        print(f'a:{a}, b:{b}, expect：{expect}')
        self.assertEqual(expect, add(a, b))


if __name__ == '__main__':
    unittest.main()