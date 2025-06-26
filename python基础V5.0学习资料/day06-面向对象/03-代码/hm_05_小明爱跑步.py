class Person:
    def __init__(self, name, weight):
        self.name = name  # 姓名
        self.weight = weight  # 体重

    def __str__(self):
        return f"{self.name} 目前的体重为 {self.weight} kg"

    def run(self):
        """跑步的方法"""
        # 体重减少 0.5kg
        # self.weight = self.weight - 0.5
        self.weight -= 0.5
        print(f'{self.name} 跑步了, 体重减少 0.5 kg')

    def eat(self):
        """吃东西的方法"""
        # 体重增加 1kg
        self.weight += 1
        print(f"{self.name} 大餐一顿, 体重增加了 1kg")


if __name__ == '__main__':
    # 创建对象
    xming = Person('小明', 75.0)
    print(xming)
    xming.run()
    print(xming)
    xming.eat()
    print(xming)
    xmei = Person('小美', 45.0)
    print(xmei)
    xmei.run()
    xmei.run()
    print(xmei)
    xmei.eat()
    print(xmei)
