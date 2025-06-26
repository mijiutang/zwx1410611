import unittest

from htmltestreport import HTMLTestReport
from hm_04_pa1 import TestAdd

# 套件

suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(TestAdd))

# 运行对象
# runner = HTMLTestReport(报告的文件路径后缀.html, 报告的标题, 其他的描述信息)
# runner = HTMLTestReport('test_add_report.html', '加法用例测试报告', 'xxx')
# runner = HTMLTestReport('./report/test_add_report.html', '加法用例测试报告', 'xxx')
runner = HTMLTestReport('report/test_add_report.html', '加法用例测试报告', 'xxx')
runner.run(suite)