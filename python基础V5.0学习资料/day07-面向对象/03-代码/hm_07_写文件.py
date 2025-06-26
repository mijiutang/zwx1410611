# # 1, 打开文件
# f = open('a.txt', 'w', encoding='utf-8')
# # 2, 写文件
# # f.write('hello python!')
# f.write('好好学习\n天天向上')
# # 3, 关闭文件
# f.close()
#
#

with open('a.txt', 'a', encoding='utf-8') as f:
    f.write('good good study\n')