str1 = 'hello Python\tand itcast and\nitheima'

# 1. 默认 按照空白字符分隔
list1 = str1.split()
print(list1)  # ['hello', 'Python', 'and', 'itcast', 'and', 'itheima']

# 2. 按照 空格分隔
list2 = str1.split(' ')
print(list2)  # ['hello', 'Python\tand', 'itcast', 'and\nitheima']

# 3. 按照 and  分隔
list3 = str1.split('and')
print(list3)  # ['hello Python\t', ' itcast ', '\nitheima']

