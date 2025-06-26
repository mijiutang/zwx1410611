# 定义空列表
list1 = []

print(list1)
# 添加数据 张三
list1.append('张三')
print(list1)

# 添加李四
list1.append('李四')
print(list1)
list1.append('王五')
list1.append('赵六')
print(list1)

# 删除最后一个数据
list1.pop()
print(list1)
# 删除第二个数据
name = list1.pop(1)
print('删除的对象为:', name)
print(list1)

