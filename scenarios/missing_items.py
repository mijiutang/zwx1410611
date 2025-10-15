
'''
处理“少送”的场景。
严格按照流程图的文字和步骤。
'''
from .utils import get_user_choice, show_action

def handle():
    """处理“少送”的场景。"""
    print("\n--- 开始处理场景：少送 ---")
    
    order_status = get_user_choice("判断订单状态", ["进行中/已送达", "已退款"])

    if order_status == "已退款":
        show_action("执行餐损流程。")
        # from . import food_damage
        # food_damage.handle()
    else:
        _handle_in_progress_or_delivered()

def _handle_in_progress_or_delivered():
    """处理“进行中/已送达”的子流程。"""
    show_action("判断用户是否要餐（通过对话历史、隐私号、问商家、问用户）。", "【外呼用户-餐品少送确认是否还要餐】")
    wants_food = get_user_choice("用户是否要餐?", ["要餐", "不要餐"])

    if wants_food == "要餐":
        _handle_wants_food()
    else:
        _handle_does_not_want_food()

def _handle_wants_food():
    """处理用户仍想要餐的流程。"""
    show_action("联系骑手核实少送是否属实，并协商补送。", "【外呼骑手-核实餐品是否少送-协商补送】")
    rider_response = get_user_choice(
        "骑手反馈是?",
        ["骑手承认，可以补送", "骑手承认，但不可补送", "骑手不承认，一般都不会给补送"]
    )
    if rider_response == "骑手承认，可以补送":
        show_action("提醒骑手，如用户不愿意等需要退款则骑手责。")
        show_action("联系用户安抚等待，用户认可则结束；不认可要求退款可退，同时需共识给商家。", "不认可仅退款需要赔偿流转纠纷【升级转接】。此时需要输出熔断话术。")
    elif rider_response == "骑手承认，但不可补送":
        show_action("提醒骑手，如退款，骑手责。")
        show_action("建议自配补送，或协商用户退款。", "如用户不认可，升级纠纷。")
    else: # 骑手不承认
        show_action("协商商家补送。")
        can_resend = get_user_choice("商家是否可补送?", ["可补送", "不可补送"])
        if can_resend == "可补送":
            show_action("联系用户安抚等待，协调补送事宜。")
        else:
            show_action("如果商家诉求是退款，则根据IM隐私号以及上文判断责任方。")
            _determine_responsibility_for_refund()

def _handle_does_not_want_food():
    """处理用户不想要餐的流程（即退款流程）。"""
    refund_status = get_user_choice("判断退款状态", ["已发起二次退款申诉", "未退款、首次申请退款处理中/已拒绝"])
    if refund_status == "已发起二次退款申诉":
        show_action("引导商家关注消费者客服处理结果。")
    else:
        show_action("判断责任方（IM/隐私号记录，问骑手，通过上文或问商家）。")
        _determine_responsibility_for_refund()

def _determine_responsibility_for_refund():
    """根据责任方判断退款处理方式。"""
    responsibility = get_user_choice("责任方是?", ["用户责任", "商家责任", "骑手责任"])
    if responsibility == "用户责任":
        show_action("建议商家与用户协商解决，禁止直接引导商家拒绝退款。")
    elif responsibility == "商家责任":
        show_action("建议商家与用户协商解决，如商家要求退款，可协助协商用户退款但是无餐损。")
    else: # 骑手责任
        show_action("退款中-引导商家后台操作退款，骑手责部分退款可赔付餐损，如商家要求协助，可协助操作。非退款进行中-协商用户退款。")
