def func1():
    num = 10  # 局部变量
    print(num)


def func2():
    num = 20
    print(num)


if __name__ == '__main__':
    func1()  # 10
    func2()  # 20
    func1()  # 10
