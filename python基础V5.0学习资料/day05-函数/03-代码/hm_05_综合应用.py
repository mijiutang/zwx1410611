def func1():
    list1.append(10)


def func2():
    list1 = [1, 1]  # 定义局部变量, 不影响全局变量
    list1.append(0)


def func3():
    global list1  # 全局变量
    list1.pop()  # 删除最后一个数据


def func_5():
    list1.pop()  # 用的全局变量,没有改引用


def func4():
    global list1  # 全局变量
    list1 = [1]


if __name__ == '__main__':
    list1 = [1, 2]
    func1()
    print(list1)  # ①[1, 2]  ②[1, 2, 10](√)  ③报错
    func2()
    print(list1)   # ① [1, 1, 0] ②[1, 2, 10](√) ③报错
    func3()
    print(list1)  # [1, 2]
    # func_5()
    # print(list1)  # ②[1, 2]   ①[1]对
    func4()
    print(list1)  # [1]  
