class LoginPage:
    """登录页面"""
    def __init__(self, username, password, code):
        self.username = username  # 用户名
        self.password = password  # 密码
        self.verify_code = code   # 验证码

    def login(self):
        print(f"1. 输入用户名: {self.username}")
        print(f"2. 输入密码: {self.password}")
        print(f"3. 输入验证码: {self.verify_code}")
        print(f"4. 点击登录")


if __name__ == '__main__':
    admin = LoginPage('admin', '123456', '8888')
    admin.login()
