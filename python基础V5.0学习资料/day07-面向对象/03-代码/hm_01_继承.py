# 1. 定义动物类，动物有姓名和年龄属性，具有吃和睡的行为
class Animal:
    """动物类"""
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def eat(self):
        """吃"""
        print(f'{self.name} 吃东西')

    def sleep(self):
        """睡"""
        print(f"{self.name} 睡觉")


# 2. 定义猫类，猫类具有动物类的所有属性和方法，并且具有抓老鼠的特殊行为
class Cat(Animal):
    """猫类"""
    def catch(self):
        print(f"{self.name} 会抓老鼠...")


# 3. 定义狗类，狗类具有动物类的所有属性和方法，并且具有看门的特殊行为
class Dog(Animal):
    """狗类"""
    def look_the_door(self):
        """看门"""
        print(f"{self.name} 正在看家....")


# 4. 定义哮天犬类，哮天犬类具有狗类的所有属性和方法，并且具有飞的特殊行为
class XTQ(Dog):
    """哮天犬类"""
    def fly(self):
        """飞"""
        print(f"{self.name} 在天上飞...")


if __name__ == '__main__':
    ani = Animal('佩奇', 2)
    ani.eat()
    ani.sleep()
    cat = Cat('黑猫警长', 10)
    cat.eat()  # 调用 父类 animal 中的方法
    cat.sleep()  # 调用 父类 animal 中的方法
    cat.catch()  # 调用自己类的方法
    dog = Dog('旺财', 3)
    dog.eat()
    dog.sleep()
    dog.look_the_door()
    xtq = XTQ('哮天犬', 100)
    xtq.eat()
    xtq.sleep()
    xtq.look_the_door()
    xtq.fly()
