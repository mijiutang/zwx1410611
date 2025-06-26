# 1. 导包  unittest
import unittest
from hm_02_testcase1 import TestDemo1
from hm_02_testcase2 import TestDemo2

# 2. 实例化套件对象 unittest.TestSuite()
suite = unittest.TestSuite()

# 3. 添加用例方法
# 3.2 添加整个测试类
# 套件对象.addTest(unittest.makeSuite(测试类名))  # 在不同的 Python 版本中,可能没有提示
suite.addTest(unittest.makeSuite(TestDemo1))
suite.addTest(unittest.makeSuite(TestDemo2))
# 4. 实例化 执行对象 unittest.TextTestRunner()
runner = unittest.TextTestRunner()
# 5. 执行对象执行 套件对象 执行对象.run(套件对象)
runner.run(suite)
