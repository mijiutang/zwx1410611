def show_info(name, age):
    print(f"name:{name}, age: {age}")


# 位置传参
show_info('小明', 18)

# 关键字传参
show_info(age=18, name='张三')

# 混合使用
show_info('李四', age=17)
