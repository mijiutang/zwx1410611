import json


with open('info.json', encoding='utf-8') as f:
    buf = json.load(f)
    print(type(buf))
    print(buf)
    # 姓名
    print(buf.get('name'))
    # 城市
    print(buf.get('address').get('city'))
    # 第二个爱好
    print(buf.get('like')[1])
    # 学校
    print(buf.get('school'))

