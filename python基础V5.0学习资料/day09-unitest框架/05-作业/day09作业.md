## day09 作业

## 题目 1

```python
1. 定义 TestCase文件 case1.py, 在文件中 定义一个测试类 TestDemo1, 在测试类中 定义两个测试方法, 直接输出打印一句话即可

2. 直接运行 case1.py, 查看结果

3. 定义 TestCase文件 case2.py, 在文件中 定义一个测试类 TestDemo2, 在测试类中 定义两个测试方法, 直接输出打印一句话即可

4. 直接运行 case2.py, 查看结果

5. 使用 TestSuite 和 TestRunner 将 case1.py 和 case2.py 进行组装,运行
```



## 题目2

```yacas 
完成对 login 函数的测试
```

```python
# 假设对某网站的登录进行测试
def login(username, password):
    if username == 'admin' and password == '123456':
        return '登录成功'
    else:
        return '登录失败'
    
# 1. 这个是开发书写的代码功能,不要修改我的 login 函数
# 2. 可以认为这函数就是 tpshop 登录

设计测试数据:
正确的用户名和密码: admin,123456, 登录成功
错误的用户名: root, 123456, 登录失败
错误的密码: admin, 123123, 登录失败
错误的用户名和错误的密码: aaa, 123123, 登录失败
```



