
# 导入scenarios子目录中的所有场景处理模块
from scenarios import (
    taken_by_wrong_rider,
    food_damage,
    rider_accepts_but_no_pickup,
    rider_delivery_timeout,
    rider_accident,
    rider_confirms_delivery_early,
    spillage_or_leakage,
    missing_items,
    merchant_cannot_contact_user,
    user_changes_plan,
    no_rider_accepts_order,
    complaint_about_rider_bad_attitude
)

# 定义场景映射
# 将数字、场景名称和处理函数关联起来
SCENARIOS = {
    "1": ("被其他骑手拿走/偷餐", taken_by_wrong_rider.handle),
    "2": ("餐损", food_damage.handle),
    "3": ("骑手接单不取餐", rider_accepts_but_no_pickup.handle),
    "4": ("骑手配送超时", rider_delivery_timeout.handle),
    "5": ("骑手发生事故", rider_accident.handle),
    "6": ("骑手提前点击送达", rider_confirms_delivery_early.handle),
    "7": ("撒漏", spillage_or_leakage.handle),
    "8": ("少送", missing_items.handle),
    "9": ("商家联系不上用户", merchant_cannot_contact_user.handle),
    "10": ("用户计划有变/买错", user_changes_plan.handle),
    "11": ("无骑手接单", no_rider_accepts_order.handle),
    "12": ("投诉骑手态度恶劣", complaint_about_rider_bad_attitude.handle),
}

def main():
    """主函数，运行决策支持系统。"""
    print("\n欢迎使用外卖场景决策支持系统 (模块化版)。")
    
    while True:
        print("\n--- 请选择您要处理的场景 ---")
        for key, (name, _) in SCENARIOS.items():
            print(f"{key}. {name}")
        print("0. 退出")
        
        choice = input("请输入场景序号: ").strip()

        if choice == '0':
            print("感谢使用，系统已退出。")
            break

        if choice in SCENARIOS:
            name, handle_func = SCENARIOS[choice]
            try:
                handle_func()
            except Exception as e:
                print(f"\n处理场景 '{name}' 时发生错误: {e}")
                print("请检查对应的场景文件和输入。")
        else:
            print("无效的场景选择，请重新输入。")

if __name__ == "__main__":
    main()
