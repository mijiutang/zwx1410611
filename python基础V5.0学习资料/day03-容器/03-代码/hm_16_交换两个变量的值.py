a = 10
b = 20
# c = b, a  # 组包
# print(c)  # (20, 10)
# a, b = c  # 拆包 a(20)  b(10)
# print(a, b)

a, b = b, a
print(a, b)

x, y, z = 'abc'
print(y)  # b
