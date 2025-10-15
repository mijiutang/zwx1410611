
'''
处理“用户计划有变/买多/买错/买少”的场景。
严格按照流程图的文字和步骤。
'''
from .utils import get_user_choice, show_action

def handle():
    """处理“用户计划有变/买多/买错/买少”的场景。"""
    print("\n--- 开始处理场景：用户计划有变/买多/买错/买少 ---")
    
    is_food_prepared = get_user_choice("核实商家是否出餐", ["是", "否"])

    if is_food_prepared == "否":
        show_action(
            "为保证用户体验，可以同意退款。",
            "参考话术：老板你还没有出餐的话，小袋建议您可以同意退款，既能给用户比较好的体验，也不会给您造成损失，相信用户如果有需求的话也会再次下单的。"
        )
    else: # 是
        show_action("联系用户收餐。", "【外呼用户-引导用户继续收餐】")
        user_response = get_user_choice(
            "用户的反馈是?",
            ["认可结案", "不认可流转纠纷", "联系不上/拒绝收餐"]
        )

        if user_response == "认可结案":
            show_action("用户同意继续收餐，问题解决。")
        elif user_response == "不认可流转纠纷":
            show_action("将问题升级至纠纷处理。")
        else: # 联系不上/拒绝收餐
            show_action("联系不上/拒绝收餐餐品处理方案。")
            delivery_type = get_user_choice("配送方式是?", ["美配", "自配"])
            if delivery_type == "美配":
                show_action("建议骑手上报异常，非商家原因建议拒绝退款。")
            else: # 自配
                show_action("建议带回，非商家原因建议拒绝退款。")

