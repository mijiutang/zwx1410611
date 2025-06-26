try:
    num = int(input('请输入一个整数数字:'))
    num1 = 8 / num
    print(num1)
except Exception as e:
    print(f'发生了异常, {e}')
