class Cat:
    def eat(self):  # self  暂时不管
        """吃鱼的方法"""
        print('小猫爱吃鱼...')

    def drink(self):
        """喝水的方法"""
        print('小猫要喝水')


# 创建对象
tom = Cat()
# 通过对象 调用类中的方法
tom.eat()
tom.drink()


