student_list = [["张三", "18", "功能测试"], ["李四", "20", "自动化测试"], ["王五", "21", "自动化测试"]]

# 张三
print(student_list[0][0])
# 李四
print(student_list[1][0])

# 张三 的信息添加一个 性别 男 ---> 向张三所在的列表 添加数据
student_list[0].append('男')
print(student_list)
# 删除 性别
student_list[0].pop()
print(student_list)

# 打印 所有人员的年龄
for info in student_list:  # info 是 列表
    print(info[1])
