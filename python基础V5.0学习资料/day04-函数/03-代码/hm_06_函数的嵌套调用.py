# 1. 定义名为test01的函数，打印当前函数的名称
def test01():
    print(1)
    print('func01')
    print(2)


# 2. 定义名为test02的函数，打印当前函数的名称，并 调用test01函数
def test02():
    print(3)
    print('func2')
    test01()
    print(4)


print(5)
test02()
print(6)

# 5 3 1 2 4 6
#
