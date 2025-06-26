class Cat:
    def __init__(self, name):
        print('我是 init 方法, 我被调用了')  # 验证使用,正式代码不要
        self.name = name

    def eat(self):
        print(f"小猫 {self.name} 爱吃鱼")


# init 方法 创建对象之后 会自动调用
# 1 会  2 不会
# Cat  # 2 不是创建对象
# Cat()   # 1 因为是创建对象

# tom = Cat   # 2  不是创建对象, 即 tom  也是类
#
# blue = Cat()  # 1 创建对象
# b = blue  # 2 不是创建对象, 只是引用的传递
#
# t = tom()   # 1, tom  已经是类, 类名()  就是创建对象

blue_cat = Cat('蓝猫')
print(blue_cat.name)
blue_cat.eat()

black_cat = Cat('黑猫')
black_cat.eat()
