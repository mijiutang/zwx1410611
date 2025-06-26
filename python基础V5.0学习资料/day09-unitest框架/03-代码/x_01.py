"""
学习 TestCase(测试用例) 的使用
"""


# 1. 导包 unittest
import unittest


# 2. 定义测试类, 只要继承 unittest.TestCase 类, 就是 测试类
class TestDemo(unittest.TestCase):
    # 3. 书写测试方法, 方法中的代码就是真正用例代码, 方法名必须以 test 开头
    def test_method1(self):
        print('测试方法一')

    def test_method2(self):
        print('测试方法二')


# 4. 执行
# 4.1 在类名或者方法名后边右键运行
# 4.1.1 在类名后边, 执行类中的所有的测试方法
# 4.1.2 在方法名后边, 只执行当前的测试方法

# 4.1 在主程序使用使用 unittest.main()  来执行,
# if __name__ == '__main__':
#     unittest.main()