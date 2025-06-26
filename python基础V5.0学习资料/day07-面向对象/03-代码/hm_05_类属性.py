class Tool:
    # 定义类属性 count,记录创建对象的个数
    count = 0

    def __init__(self, name):
        self.name = name  # 实例属性, 工具的名字
        # 修改类属性的值
        Tool.count += 1


if __name__ == '__main__':
    # 查看 创建对象的个数
    print(Tool.count)   # 查看类属性
    tool1 = Tool('锤子')
    print(Tool.count)
    tool2 = Tool('扳手')
    print(Tool.count)
    print(tool2.count)  # 先找实例属性 count, 找不到, 找类属性 count, 找到,使用
