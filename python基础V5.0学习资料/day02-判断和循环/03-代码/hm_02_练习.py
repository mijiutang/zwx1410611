# 1. 获取用户输入的用户名信息  input
name = input('请输入用户名:')
# 2. 如果用户名信息是 admin, 就在控制台输出 "欢迎admin登录"
if name == 'admin':
    print('欢迎admin登录')
else:
    # 3. 如果用户名信息不是 admin, 就在控制台输出"用户名错误!"
    print('用户名错误!')
