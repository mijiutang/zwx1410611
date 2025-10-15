
import time

def get_user_choice(prompt, options):
    """一个帮助函数，用来获取用户的选择。"""
    print(f"\n--- 需要人工判断 ---")
    print(prompt)
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    
    while True:
        try:
            choice_str = input(f"请选择 (1-{len(options)}): ")
            if not choice_str:
                continue
            choice = int(choice_str)
            if 1 <= choice <= len(options):
                return options[choice - 1]
            else:
                print(f"无效选择，请输入 1 到 {len(options)} 之间的数字。")
        except ValueError:
            print("无效输入，请输入一个数字。")

def show_action(action, details=''):
    """显示建议的操作。"""
    print(f"\n-> 建议操作：{action}")
    if details:
        print(f"   参考话术/说明：{details}")
    time.sleep(1) # 模拟处理延迟

