my_list = [1, 2, 1, 2, 5, 2, 2, 4, 13]

# 方式一
list1 = list(set(my_list))
print(list1)

# 方式二
new_list = []   # 定义新列表 ,保存去重后的数据

# # 遍历原列表
# for i in my_list:
#     # 判断数据是否存在新列表
#     if i in new_list:
#         # 存在 什么都不操作
#         pass
#     else:
#         # 不存在, 添加到新列表
#         new_list.append(i)

# 遍历原列表
for i in my_list:
    # 判断数据是否存在新列表
    if i not in new_list:
        # 不存在, 添加到新列表
        new_list.append(i)

print(new_list)
