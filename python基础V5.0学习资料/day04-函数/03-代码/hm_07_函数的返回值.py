# 设计一个函数用于获取两个数中的较大数，数据来自于函数的参数
def get_max(a, b):
    if a > b:
        return a
    else:
        return b
    print('我会执行吗, 不会执行')


# 调用
num = get_max(10, 20)
print(num)
# 1 会  2 不会

