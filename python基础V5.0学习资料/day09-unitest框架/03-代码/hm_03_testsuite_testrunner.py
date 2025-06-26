# 1. 导包  unittest
import unittest
from hm_02_testcase1 import TestDemo1
from hm_02_testcase2 import TestDemo2

# 2. 实例化套件对象 unittest.TestSuite()
suite = unittest.TestSuite()

# 3. 添加用例方法
# 3.1 套件对象.addTest(测试类名('测试方法名'))  # 建议复制
suite.addTest(TestDemo1('test_method1'))
suite.addTest(TestDemo1('test_method2'))
suite.addTest(TestDemo2('test_method1'))
suite.addTest(TestDemo2('test_method2'))
# 4. 实例化 执行对象 unittest.TextTestRunner()
runner = unittest.TextTestRunner()
# 5. 执行对象执行 套件对象 执行对象.run(套件对象)
runner.run(suite)
