import unittest

# 实例化加载对象并加载用例,得到套件对象
# suite = unittest.TestLoader().discover('用例所在的目录', '用例代码文件名*.py')
suite = unittest.TestLoader().discover('.', 'hm_02*.py')
# 实例化执行对象并执行
# runner = unittest.TextTestRunner()
# runner.run(suite)

unittest.TextTestRunner().run(suite)
