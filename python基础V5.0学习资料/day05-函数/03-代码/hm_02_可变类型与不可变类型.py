my_tuple = (1, 2, [10, 20])  # 元组中 存储的 1 的地址, 2 的地址, 列表的地址

print(my_tuple, id(my_tuple), id(my_tuple[-1]), id(my_tuple[-1][-1]))
my_tuple[-1][-1] = 30  # 修改的列表中最后一个位置的引用
print(my_tuple, id(my_tuple), id(my_tuple[-1]), id(my_tuple[-1][-1]))