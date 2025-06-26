# 1. 导包 unittest
import unittest


# 2. 定义测试类, 只要继承 unittest.TestCase 类, 就是 测试类
class TestDemo2(unittest.TestCase):
    # 3. 书写测试方法, 方法中的代码就是真正用例代码, 方法名必须以 test 开头
    def test_method1(self):
        print('测试方法2-1')

    def test_method2(self):
        print('测试方法2-2')

