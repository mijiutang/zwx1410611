try:
    num = int(input('请输入一个整数数字:'))
    num1 = 8 / num
    print(num1)
except ValueError:  #
    print('输入的内容非数字,请重新输入')
except ZeroDivisionError:
    print('不能输出数字 0, 请重新输入')