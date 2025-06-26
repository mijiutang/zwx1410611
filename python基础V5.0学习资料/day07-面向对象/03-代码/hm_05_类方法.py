class Tool:
    # 定义类属性 count,记录创建对象的个数
    count = 0

    def __init__(self, name):
        self.name = name  # 实例属性, 工具的名字
        # 修改类属性的值
        Tool.count += 1

    @classmethod
    def show_tool_count(cls):  # cls 就是类对象, 类名
        return cls.count


if __name__ == '__main__':
    # 查看 创建对象的个数
    print(Tool.show_tool_count())
    tool1 = Tool('锤子')
    print(Tool.show_tool_count())
    tool2 = Tool('扳手')
    print(tool2.show_tool_count())
