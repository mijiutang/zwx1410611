my_str = 'abcdefg'

# 需求1 : 打印字符串中 abc 字符 start 0, end 3, step 1
print(my_str[0:3:1])  # abc

# 1.1 如果步长是 1, 可以省略不写
print(my_str[0:3])  # abc

# 1.2 如果 start 开始位置的下标为 0, 可以不写,但是冒号不能少
print(my_str[:3])  # abc

# 需求 2: 打印字符串中的 efg , start 4, end 7, step 1
print(my_str[4: 7])  # efg
# 2.1 如果取到最后一个字符, end  可以不写,但是冒号不能少
print(my_str[4:])  # efg

# 需求 3: 打印字符串中的 aceg , start 0, end 7(最后), 步长 2
print(my_str[::2])  # aceg

# 练习: cf
print(my_str[2:6:3])

# 特殊情况, 步长为 -1, 反转(逆序) 字符串
print(my_str[::-1])   # gfedcba
