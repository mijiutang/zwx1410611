import json
from app import BASE_DIR

def build_add_data():
    with open('../data/add_data.json') as f:
        data = json.load(f)  # [[], [], []]  ---> [(), ()]

    return data


def build_add_data_1():
    with open('../data/add_data_1.json') as f:
        data_list = json.load(f)  # [{}, {}, {}]  ----> [(), ()]

        new_list = []
        for data in data_list:  # data 字典
            # 字典中的值，是否都需要
            a = data.get('a')
            b = data.get('b')
            expect = data.get('expect')
            new_list.append((a, b, expect))

        return new_list


def build_add_data_2():
    with open(BASE_DIR + '/data/add_data_1.json') as f:
        data_list = json.load(f)  # [{}, {}, {}]  ----> [(), ()]

        new_list = []
        for data in data_list:  # data 字典
            # 字典中的值，是否都需要
            new_list.append(tuple(data.values()))

        return new_list


def build_login_data():
    with open(BASE_DIR + '/data/login_data.json', encoding='utf-8') as f:
        data_list = json.load(f)  # [{}, {}] ---> [()]
        new_list = []
        for data in data_list:
            # 字典中的 desc 不需要
            username = data.get('username')
            password = data.get('password')
            expect = data.get('expect')
            new_list.append((username, password, expect))

        return new_list


if __name__ == '__main__':
    # print(build_add_data_2())
    print(build_login_data())