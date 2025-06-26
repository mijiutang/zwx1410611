# with open('a.txt', encoding='utf-8') as f:
#     buf = f.read()
#     print(buf)

f = open('a.txt', encoding='utf-8')
data = f.read()
print(data)
f.close()
