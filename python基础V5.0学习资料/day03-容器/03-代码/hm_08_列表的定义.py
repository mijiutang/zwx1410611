# 方式1, 使用类实例化的方式
# 1.1 定义空列表  变量 = list()
list1 = list()
print(type(list1), list1)  # <class 'list'> []

# 1.2 定义非空列表 , 也称为 类型转换  list(可迭代类型)  可迭代类型,能够使用 for 循环 就是 可迭代类型(比如 容器)
# 将容器中的 每个数据 都作为列表中一个数据进行保存
list2 = list('abcd')
print(list2)  # ['a', 'b', 'c', 'd']


# 方式2, 直接使用 [] 进行定义(使用较多)
# 2.1 定义空列表
list3 = []
print(list3)
# 2.2 定义非空列表
list4 = [1, 3.14, 'hello', False]
print(list4)

# 获取 列表中 第一个数据
print(list4[0])  # 1
# 获取列表中最后一个数据
print(list4[-1])  # False
# 获取中间两个数据即 3.14 和 'hello' (1 和 2)
print(list4[1: 3])  # [3.14, 'hello']

