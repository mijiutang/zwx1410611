# 1. 类实例化方式
# 1.1 定义空元组(不用)
tuple1 = tuple()
print(type(tuple1), tuple1)  # <class 'tuple'> ()
# 1.2 类型转换 , 将列表(其他可迭代类型)转换为元组
tuple2 = tuple([1, 2, 3])
print(tuple2)

# 2. 直接使用 () 定义
# 2.1 定义空元组
tuple3 = ()
# 2.2 非空元组
tuple4 = (1, 2, 'hello', 3.14, True)
print(tuple4)

print(tuple4[2])  # hello

# 2.3 定义只有一个数据的元组,  数据后必须有一个逗号
tuple5 = (10,)
print(tuple5)
