def input_password():
    """输入密码的函数"""
    pwd = input('请输入密码:')
    if len(pwd) < 8:
        # raise 异常对象
        raise Exception('密码长度不足 8 位')
    else:
        return pwd
