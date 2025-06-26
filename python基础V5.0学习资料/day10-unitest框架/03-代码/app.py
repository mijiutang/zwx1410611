import os

# __file__ 特殊的变量,表示当前代码文件名
# path1 = os.path.abspath(__file__)
# print(path1)
# path2 = os.path.dirname(path1)
# print(path2)

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(__file__)


if __name__ == '__main__':
    print(BASE_DIR)
