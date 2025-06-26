# 1. 定义名为 input_username 的函数, 获取用户输入的用户名
def input_username():
    """输入用户名"""
    return input('请输入用户名:')


# 2. 定义名为 input_password 的函数, 获取用户输入的密码
def input_password():
    """输入密码"""
    return input('请输入密码:')


# 3. 定义名为 login 的函数, 判断获取的用户名和密码信息
# 4. 要求当获取的用户名为:admin 并且密码为: 123456 时, 输出“登录成功!”，否则提示“用户名或 密码错误!”
def login():
    """登录函数"""
    if input_username() == 'admin' and input_password() == '123456':
        print('登录成功')
    else:
        print('用户名或密码错误')


login()
