# with open('a.txt', encoding='utf-8') as f:
#     while True:
#         buf = f.readline()  # 文件读完了,返回 空字符串
#         if buf == "":
#             break
#         else:
#             print(buf, end='')


with open('a.txt', encoding='utf-8') as f:
    while True:
        buf = f.readline()  # 文件读完了,返回 空字符串
        if buf:   # 空字符串 是 False, 非空字符串 是 True
            print(buf, end='')
        else:
            break
