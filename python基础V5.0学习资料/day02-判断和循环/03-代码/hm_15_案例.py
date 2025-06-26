while True:
    # 1. 提示用户输入登录系统的用户名和密码
    username = input('请输入用户名:')
    if username == 'exit':
        break
    password = input('请输入密码:')
    # 2. 校验用户名和密码是否正确(正确的用户名:admin、密码:123456)
    if username == 'admin' and password == '123456':
        # 3. 如果用户名和密码都正确，打印“登录成功!”，并结束程序
        print('登录成功')
        break
    else:
        # 4. 如果用户名或密码错误，打印“用户名或密码错误!”，提示用户继续输入用户名和密码登录
        print('用户名或密码错误! 请再次输入')
