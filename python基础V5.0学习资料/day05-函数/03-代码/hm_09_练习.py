def my_sum(*args):   # args 是元组
    num = 0
    for i in args:
        num += i

    return num


print(my_sum())  #
print(my_sum(1))  # 1
print(my_sum(1, 2))  # 3
print(my_sum(1, 2, 3))  # 6

my_tuple = (1, 2, 3, 4, 5)
# 需求对 元组中的所有数据使用 my_sum 进行求和
# 想要把列表(元组) 中的数据作为位置参数进行传递, 只需要在列表(元组)前边加上一个 * ,进行拆包即可
print(my_sum(*my_tuple))  # 15
