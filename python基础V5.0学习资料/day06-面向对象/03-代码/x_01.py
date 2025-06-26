class A:
    def func(self):
        print(self.name)
        name = 40

    def show(self):
        print(self.name)
        self.name = 30


a = A()
a.name = 10
b = A()
b.name = 20

# a.func()  # 10
# b.show()  # 20
# b.func()  # 30
a.func()  # 10
a.func()  # 40 10
