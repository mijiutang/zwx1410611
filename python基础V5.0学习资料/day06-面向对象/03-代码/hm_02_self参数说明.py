class Cat:
    def eat(self):  # self 是调用这个方法的对象
        """吃鱼的方法"""
        print(f'self:{id(self)}')
        print(f'小猫{self.name}, {self.age}岁 爱吃鱼...')


# 创建对象
tom = Cat()
# 通过对象 调用类中的方法
print(f"tom :{id(tom)}")
# 给 Tom 对象添加 name 属性
tom.name = '汤姆'
tom.age = 3
print(tom.name)
tom.eat()

blue_cat = Cat()
print(f'blue:{id(blue_cat)}')
blue_cat.name = '蓝猫'
blue_cat.age = 4
blue_cat.eat()
