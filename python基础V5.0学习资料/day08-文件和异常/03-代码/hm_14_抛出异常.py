import tools

try:
    pwd = tools.input_password()
    print(f"获取的密码是: {pwd}")
except Exception as e:
    print(e)
