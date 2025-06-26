my_str = 'good good study'

# 需求, 将 good 变为 GOOD
my_str1 = my_str.replace('good', 'GOOD')
print('my_str :', my_str)
print('my_str1:', my_str1)

# 将第一个 good 替换为 Good
my_str2 = my_str.replace('good', 'Good', 1)
print('my_str2:', my_str2)

# 将第二个 good  替换为 Good
# 先整体替换为 Good, 再将替换后的 第一个Good 替换为 good
my_str3 = my_str.replace('good', 'Good').replace('Good', 'good', 1)
print('my_str3:', my_str3)
