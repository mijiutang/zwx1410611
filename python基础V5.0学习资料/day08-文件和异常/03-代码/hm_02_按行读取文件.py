with open('a.txt', encoding='utf-8') as f:
    buf = f.readline()
    print(buf)  # aaaaaa
    buf1 = f.readline()
    print(buf1)  # bbbbbb
