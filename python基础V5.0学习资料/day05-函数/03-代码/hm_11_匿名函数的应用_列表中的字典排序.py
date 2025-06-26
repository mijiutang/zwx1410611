user_list = [
    {'name': '张三', 'age': 22, 'title': '测试工程师'},
    {'name': '李四', 'age': 24, 'title': '开发工程师'},
    {'name': '王五', 'age': 21, 'title': '测试工程师'}
]


# user_list.sort()   # 只能对数字,字符串排序
# 根据字典的 age 键 排序
# 想要对列表中的字典排序,需要 key 形参来指定根据字典中的什么键排序
# key 这个参数需要传递一个函数,使用匿名函数
# 列表.sort(key=lambda x: x['键'])


def func(x):
    return x['age']


user_list.sort(key=lambda x: x['age'])
# user_list.sort(key=func)
print(user_list)
