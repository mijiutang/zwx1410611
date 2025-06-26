# nums = [10, 20, 30, 40, 50]
#
# for i in range(len(nums)):  # 下标
#     print(nums[i])
#     nums[i] += 10
#
# print(nums)
#
# i = 0
# while i < len(nums):
#     print(nums[i])
#     nums[i] += 10
#     i += 1
# print(nums)


data_list = [
    {'desc': '用户名密码验证码 OK',
     'username': '13888888888',
     'password': '123456',
     'verify_code': '8888',
     'expect': "登录成功"
     },
    {'desc': '用户名不存在',
     'username': '',
     'password': '123456',
     'verify_code': '8888',
     'expect': "用户名不存在"
     },
    {'desc': '密码错误',
     'username': '13888888888',
     'password': '123123',
     'verify_code': '8888',
     'expect': "密码错误"
     }
]

new_list = []

for data in data_list:  # data  字典
    print(f"用户名:{data.get('username')}, 密码: {data.get('password')}, "
          f"验证码: {data.get('verify_code')}, 期望结果:{data.get('expect')}")

    t = (data.get('username'), data.get('password'), data.get('verify_code'), data.get('expect'))
    new_list.append(t)

print(new_list)