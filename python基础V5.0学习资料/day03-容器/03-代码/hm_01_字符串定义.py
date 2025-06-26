# 1. 使用单引号
str1 = 'hello'
# 2. 使用双引号定义
str2 = "hello"
# 3. 使用 三引号 定义
str3 = """hello"""
str4 = '''hello'''

print(type(str1), type(str2), type(str3), type(str4))

# 4. 定义字符串  I'm 小明, 字符串本身包含引号
# 4.1 如果字符串本身包含单引号,定义的时候不能使用 单引号,
# 4.2 如果字符串本身包含双引号,定义的时候不能使用 双引号,

str5 = "I'm 小明"
print(str5)  # I'm 小明

# 5. 转义字符 \n \t \' \"
str6 = 'I\'m 小明'
print(str6)  # I'm 小明

# 6. I\'m 小明  \\ --> \
str7 = 'I\\\'m 小明'
print(str7)  # I\'m 小明

# 7. 原生字符串 在字符串的前边 加上 r"", 字符串中的 \ 就不会进行转义
str8 = r'I\'m 小明'
print(str8)  # I\'m 小明

str7 = r'I\\\'m 小明'
print(str7)  # I\\\'m 小明

