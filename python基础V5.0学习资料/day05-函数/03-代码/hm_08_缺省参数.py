"""
定义 show_info 参数 姓名,年龄, 性别, 将年龄设置为默认参数 18, 性别设置为默认 保密
"""


def show_info(name, age=18, sex='保密'):
    print(name, age, sex)


# 调用
show_info('张三', 18, '男')
# 李四
show_info('李四')
# 王五 19
show_info('王五', 19)
# 赵六  男
show_info('赵六', sex='男')
