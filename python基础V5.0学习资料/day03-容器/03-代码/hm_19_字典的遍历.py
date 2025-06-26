my_dict = {'name': '小明', 'age': 18, 'sex': '男'}

for k in my_dict:
    print(k)

print('*' * 30)
for k in my_dict.keys():
    print(k)

print('-' * 30)
for v in my_dict.values():
    print(v)

print('_*_' * 30)
for k, v in my_dict.items():
    print(k, v)