a = 1  # 本质: 将数据 1 的地址保存到变量 a 中, 通常理解: 将 1 保存到 a
b = a  # 本质: 将 变量 a中的引用保存到变量 b中.  通常理解 将 a 的值给 b
print(f"a: {a}, {id(a)}")
print(f"b: {b}, {id(b)}")
a = 2   # 本质: 将数据 2 的地址保存到变量a中, 只是改变 a的引用,即改变 a的值, 没有改变 b 的引用
print(f"a: {a}, {id(a)}")  # 2
print(f"b: {b}, {id(b)}")  # 1

my_list = [1, 2, 3]
my_list1 = my_list
print(f'my_list :{my_list}, {id(my_list)}')
print(f'my_list1:{my_list1}, {id(my_list1)}')
my_list[1] = 10  # 修改 列表my_list 中下标为 1 位置的引用
print(f'my_list :{my_list}, {id(my_list)}')   # [1, 10, 3]
print(f'my_list1:{my_list1}, {id(my_list1)}')  # 1 [1, 2, 3]  2[1, 10, 3]
