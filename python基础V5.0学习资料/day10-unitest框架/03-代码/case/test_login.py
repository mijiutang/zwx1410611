import unittest

from common.read_data import build_login_data
from tools import login
from parameterized import parameterized


class TestLogin(unittest.TestCase):
    @parameterized.expand(build_login_data())
    def test_login(self, username, password, expect):
        print(f'username: {username}, password: {password}, expect: {expect}')
        self.assertEqual(expect, login(username, password))
