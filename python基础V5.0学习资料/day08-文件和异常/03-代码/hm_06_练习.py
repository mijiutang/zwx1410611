import json

with open('info2.json', encoding='utf-8') as f:
    data_list = json.load(f)  # 列表
    for data in data_list:
        # sex = "男" if data.get('isMan') else "女"
        if data.get('isMan'):
            sex = "男"
        else:
            sex = '女'
        print(f"姓名: {data.get('name')}, 年龄: {data.get('age')}"
              f"性别: {sex}, 城市: {data.get('address').get('city')}")

    # 条件为True 执行的代码 if 判断条件 else 条件为 False 执行的代码
    # a = 'a ' if 3 > 1 else 'b'
