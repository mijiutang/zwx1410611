"""
定义 Cat 类, 包含属性 name 和 age, 打印对象的时候,可以输出对象的姓名和年龄
类名: Cat
属性: name, age
方法: __str__ ,  __init__
"""


class Cat:
    def __init__(self, name, age):
        self.name = name  # 添加 name 属性
        self.age = age  # 添加 age 属性

    def __str__(self):  # 一般不使用 print,直接返回
        return f"姓名: {self.name}, 年龄: {self.age}"


# 创建对象
tom = Cat('汤姆', 3)
print(tom)
print(dir(tom))
