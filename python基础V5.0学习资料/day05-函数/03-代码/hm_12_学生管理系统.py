# 定义一个列表, 保存所有学生信息
# stu_list = []
stu_list = [{'name': 'aa', 'age': '11'}, {'name': 'bb', 'age': '22'}, {'name': 'cc', 'age': '33'}]


def make_student():
    """录入单个学生信息"""
    name = input('请输入姓名:')
    age = input('请输入年龄:')
    # 将学生信息存入字典
    stu_dict = {"name": name, "age": age}
    # 返回单个学生信息
    return stu_dict


def show_stu_info():
    """展示学生信息"""
    print('---------学生列表信息-----------')
    j = 1  # 初始序号
    for stu_dict in stu_list:  # stu_dict 字典
        print(f"{j}\t\t{stu_dict.get('name')}\t\t{stu_dict.get('age')}")
        j += 1  # 修改序号
    print('-------------------------------')


def get_student_counts():
    """获取学生的数量"""
    return len(stu_list)


def search_student():
    """查询学生的信息"""
    name = input('请输入要查询的学生姓名:')
    for stu_dict in stu_list:
        if name == stu_dict.get('name'):
            # 找到了这个学生
            print(f'姓名:{name}, 年龄: {stu_dict.get("age")}')
            # 终止
            return  # 结束函数的执行

    # 写在循环的外边
    print(f'对不起, 名字叫 [{name}]的学生不存在')


if __name__ == '__main__':
    # 录入三个学生信息
    # for i in range(3):
    #     stu = make_student()
    #     # 需要将单个学生添加到列表
    #     stu_list.append(stu)
    #
    # print(stu_list)
    # 展示学生信息
    show_stu_info()
    # 获取学生数量
    print('学生总数为: ', get_student_counts())
    search_student()


