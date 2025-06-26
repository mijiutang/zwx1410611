# # 1. 获取用户输入的用户名和密码   input
# name = input('请输入用户名:')
# pwd = input('请输入密码:')
# # 2. 判断用户名是 admin 并且密码是 123456 时, 在控制台输出: 登录成功!
# if name == 'admin' and pwd == '123456':
#     print('登录成功!')
# # 3. 否则在控制台输出: 登录信息错误!
# else:
#     print('登录信息错误!')
#
#

# # 1. 定义两个整数变量 python_score、c_score，使用 input 获取成绩 编写代码判断成绩
# python_score = int(input('请输入 Python 成绩:'))
# c_score = int(input('请输入 C 成绩:'))
# # 2. 要求只要有一门成绩 > 60 分就输出合格
# if python_score > 60 or c_score > 60:
#     print('合格')


# 1. 获取用户输入的用户名
name = input('请输入用户名:')
# 2. 判断用户名是 admin 时, 在控制台输出: 欢迎 admin 登录!
# 3. 用户名是 test 时, 在控制台输出: 欢迎 test 登录!
if name == 'admin' or name == 'test':
    print(f'欢迎 {name} 登录!')
# 4. 如果是其他信息, 在控制台输出: 查无此人!
else:
    print('查无此人!')
