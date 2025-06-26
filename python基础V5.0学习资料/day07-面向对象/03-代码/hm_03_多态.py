class Dog:
    def game(self):
        print('普通狗简单的玩耍...')


class XTQ(Dog):
    def game(self):
        print('哮天犬在天上玩耍...')


class Person:
    def play_with_dog(self, dog):
        """dog 是狗类或者其子类的对象"""
        print('人和狗在玩耍...', end='')
        dog.game()


if __name__ == '__main__':
    dog1 = Dog()
    xtq = XTQ()
    xw = Person()
    xw.play_with_dog(dog1)
    xw.play_with_dog(xtq)
