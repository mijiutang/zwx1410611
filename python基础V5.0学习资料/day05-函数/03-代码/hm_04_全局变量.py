# 定义全局变量
g_num = 10


def func_1():
    print(g_num)  # 使用全局变量


def func_2():
    g_num = 20  # 定义局部变量
    print(g_num)


def func_3():
    global g_num   # 声明为全局变量
    g_num = 30
    print(g_num)


if __name__ == '__main__':
    print(g_num)  # 10
    func_1()  # 10
    func_2()  # 20
    func_1()  # 10
    print(g_num)  # 10
    func_3()  # 30  修改了全局变量, 将全局变量的值改为30 了
    func_1()  # 30
    g_num = 100
    func_1()  # 100  修改全局变量的值
    func_2()  # 20  局部变量
    func_3()  # 30
    func_1()  # 30

