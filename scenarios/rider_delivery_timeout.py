
'''
处理“骑手配送超时”的场景。
严格按照流程图的文字和步骤。
'''
from .utils import get_user_choice, show_action

def handle():
    """处理“骑手配送超时”的场景。"""
    print("\n--- 开始处理场景：骑手配送超时 ---")
    
    order_status = get_user_choice("判断配送状态", ["已送达", "配送中", "已退款"])

    if order_status == "已退款":
        show_action("走餐损流程。")
        # from . import food_damage
        # food_damage.handle()
    elif order_status == "已送达":
        _handle_delivered()
    else: # 配送中
        _handle_in_transit()

def _handle_delivered():
    """处理“已送达”状态的子流程。"""
    show_action("告知商家，明确是否有其他诉求。", "参考话术：1.老板查看您的订单餐品已经送达了，您是有其他售后问题处理吗？ 2.看到您的订单骑手已经点送达了，是用户有联系您反馈实际没有收到餐吗？")
    merchant_demand = get_user_choice(
        "商家的诉求是?",
        ["需要客服协助联系用户确认/解释/安抚", "抱怨或者反馈骑手配送相关问题", "要求退款给用户"]
    )

    if merchant_demand == "需要客服协助联系用户确认/解释/安抚":
        show_action("协助联系用户。", "【外呼用户-xxx】")
        user_response = get_user_choice("用户的反馈是?", ["用户认可", "用户不认可"])
        if user_response == "用户认可":
            show_action("用户认可则结案。")
        else:
            show_action("用户不认可，协助退款-责任方参考退款判责；不认可退款则流转纠纷。")
            _show_refund_rules()
    elif merchant_demand == "抱怨或者反馈骑手配送相关问题":
        show_action("安抚商家情绪，安抚骑手问题会加强监管。")
    else: # 要求退款给用户
        show_action("联系用户协商退款。", "【外呼用户-协商取消订单】")
        user_response = get_user_choice("用户的反馈是?", ["用户认可", "用户不认可"])
        if user_response == "用户认可":
            show_action("用户认可则协助退款-责任方参考退款判责。")
            _show_refund_rules()
        else:
            show_action("用户不认可流转纠纷。")

def _handle_in_transit():
    """处理“配送中”状态的子流程。"""
    rider_status = get_user_choice("联系骑手确认配送时间", ["可以确认", "联系不到/无法配送"])

    if rider_status == "可以确认":
        show_action("联系用户安抚配送中。", "【外呼用户-引导用户继续收餐】")
        user_response = get_user_choice("用户的反馈是?", ["用户认可", "用户不认可"])
        if user_response == "用户认可":
            show_action("用户认可则结案。")
        else:
            show_action("用户不认可，协助退款-责任方参考退款判责；不认可退款则流转纠纷。")
            _show_refund_rules()
    else: # 联系不到/无法配送
        show_action("联系用户协商退款。", "【外呼用户-协商取消订单】")
        user_response = get_user_choice("用户的反馈是?", ["用户认可", "用户不认可"])
        if user_response == "用户认可":
            show_action("用户认可则协助退款-责任方参考退款判责。")
            _show_refund_rules()
        else:
            show_action("用户不认可流转纠纷。")

def _show_refund_rules():
    """显示退款判责的通用规则说明。"""
    show_action("执行退款判责", "判责规则参考：1.配送2.0及跑腿，超最晚送达时间->骑手责；2.配送2.0，超预计送达但未超最晚送达->平台责；3.跑腿，超预计送达但未超最晚送达->平台责；4.骑手承认自身问题->骑手责。")
