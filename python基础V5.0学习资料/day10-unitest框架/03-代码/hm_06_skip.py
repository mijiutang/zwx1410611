import unittest

version = 29


class TestSkip(unittest.TestCase):
    @unittest.skip('没什么原因,就是不想执行')
    def test_1(self):
        print('方法一')

    @unittest.skipIf(version >= 30, '版本号大于等于 30, 测方法不用执行')
    def test_2(self):
        print('方法二')

    def test_3(self):
        print('方法三')


if __name__ == '__main__':
    unittest.main()
