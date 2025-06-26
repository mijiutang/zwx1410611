class Dog:
    def bark(self):
        print('汪汪汪叫......')


class XTQ(Dog):
    # 需要哮天犬 嗷嗷嗷叫, 父类中的 bark 方法,不能满足子类对象的需要, 覆盖式重写
    def bark(self):
        print('嗷嗷嗷叫.....')
    pass


if __name__ == '__main__':
    xtq = XTQ()
    xtq.bark()
