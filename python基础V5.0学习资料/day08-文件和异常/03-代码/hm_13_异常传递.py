# 1. 定义函数 demo1() 提示用户输入一个整数并且返回
def demo1():
    num = int(input('请输入一个整数'))
    return num


# 2. 定义函数 demo2() 调用 demo1()
def demo2():
    demo1()


# 3. 在主程序中调用 demo2()
if __name__ == '__main__':
    try:
        demo2()
    except Exception as e:
        print(e)
