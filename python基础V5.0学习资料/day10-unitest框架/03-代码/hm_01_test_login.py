import unittest

from tools import login


class TestLogin(unittest.TestCase):
    def test_username_password_ok(self):
        """正确的用户名和密码"""
        if "登录成功" == login('admin', '123456'):
            print('用例通过')
        else:
            print('用例不通过')

    def test_username_error(self):
        """错误的用户名"""
        if "登录失败" == login('root', '123456'):
            print('用例通过')
        else:
            print('用例不通过')

    def test_password_error(self):
        """错误的密码"""
        if "登录失败" == login('admin', '123123'):
            print('用例通过')
        else:
            print('用例不通过')

    def test_username_password_error(self):
        """错误的用户名和密码"""
        if "登录失败" == login('aaa', '123123'):
            print('用例通过')
        else:
            print('用例不通过')
