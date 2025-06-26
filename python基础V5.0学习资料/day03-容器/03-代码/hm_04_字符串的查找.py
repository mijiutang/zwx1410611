# 1. 现有字符串数据: '黑马程序员'
# 2. 请设计程序, 实现判断"黑马"和"白马"是否存在于数据中
# 3. 要求如果数据存在, 则输出数据所在位置

my_str = '黑马程序员'
# sub_str = '黑马'
sub_str = '白马'
result = my_str.find(sub_str)
if result == -1:
    print(f'{sub_str}不存在')
else:
    print(f'{sub_str}存在, 下标位置为:', result)
