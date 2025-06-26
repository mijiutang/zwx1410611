import unittest


class TestAssert(unittest.TestCase):
    def test_equal_1(self):
        self.assertEqual(10, 10)  # 用例通过

    def test_assert_2(self):
        self.assertEqual(10, 11)  # 用例不通过

    def test_in(self):
        # self.assertIn('admin', '欢迎 admin 登录')  # 包含 通过
        # self.assertIn('admin', '欢迎 adminnnnnnnn 登录')  # 包含 通过
        # self.assertIn('admin', '欢迎 aaaaaadminnnnnnnn 登录')  # 包含 通过
        # self.assertIn('admin', '欢迎 adddddmin 登录')  # 不包含 不通过
        self.assertIn('admin', 'admin')  # 包含 通过
