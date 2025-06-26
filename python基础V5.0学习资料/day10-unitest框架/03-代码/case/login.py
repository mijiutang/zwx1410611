import unittest

from app import BASE_DIR
from case.test_login import TestLogin
from htmltestreport import HTMLTestReport

suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(TestLogin))

runner = HTMLTestReport(BASE_DIR + '/report/login_report.html', '登录测试报告', 'V1.0')
runner.run(suite)