"""定义人类, name 属性 age 属性(私有)"""


class Person:
    def __init__(self, name, age):
        self.name = name  # 公有
        self.__age = age  # 公有-->私有, 在属性名前加上两个下划线

    def __str__(self):  # 公有方法
        return f"{self.name}, {self.__age}"

    def set_age(self, age):  # 定义公有方法,修改私有属性
        if age < 0 or age > 120:
            print('提供的年龄信息不对')
            return
        self.__age = age


if __name__ == '__main__':
    xw = Person('小王', 18)
    print(xw)
    # xw.__age = 10000  # 添加一个公有属性 __age
    print(xw)
    xw.set_age(10000)
    print(xw)
