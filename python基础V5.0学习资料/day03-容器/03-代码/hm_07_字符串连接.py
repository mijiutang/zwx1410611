list1 = ['hello', 'Python', 'and', 'itcast', 'and', 'itheima']

# 将 列表中数据使用 空格 组成新的字符串
str1 = ' '.join(list1)
print(str1)  # hello Python and itcast and itheima

# 使用 逗号 连接
str2 = ','.join(list1)
print(str2)  # hello,Python,and,itcast,and,itheima

# 使用 _*_ 连接
str3 = '_*_'.join(list1)
print(str3)  # hello_*_Python_*_and_*_itcast_*_and_*_itheima

