# 1, 类实例化的方式
my_dict1 = dict()
print(type(my_dict1), my_dict1)  # <class 'dict'> {}

# 2, 直接使用 {}  定义
# 2.1 定义空字典
my_dict2 = {}
print(my_dict2)

# 2.2 定义非空字典, 姓名, 年龄, 身高, 性别
my_dict = {"name": "小明", "age": 18, "height": 1.78, "isMen": True}
print(my_dict)

# 将年龄改为 20
my_dict['age'] = 20
print(my_dict)

# 添加 体重 weight
my_dict['weight'] = 65
print(my_dict)

my_dict.pop('weight')
print(my_dict)
my_dict.pop('height')
print(my_dict)