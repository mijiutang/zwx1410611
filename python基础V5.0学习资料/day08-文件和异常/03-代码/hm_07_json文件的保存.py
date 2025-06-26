import json

info = [{'name': '小明', 'age': 18}]

with open('info3.json', 'w', encoding='utf-8') as f:
    # json.dump(info, f)  #
    # json.dump(info, f, ensure_ascii=False)  # 直接显示中文
    json.dump(info, f, ensure_ascii=False, indent=2)  # 直接显示中文

import random
random.randint()