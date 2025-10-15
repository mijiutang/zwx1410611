
'''
处理“骑手提前点击送达”的场景。
严格按照流程图的文字和步骤。
'''
from .utils import get_user_choice, show_action

def handle():
    """处理“骑手提前点击送达”的场景。"""
    print("\n--- 开始处理场景：骑手提前点击送达 ---")
    
    delivery_type = get_user_choice("判断配送方式", ["非自配", "自配"])

    if delivery_type == "自配":
        show_action("属于商家自行配送的，建议自行联系配送人员核实处理。")
        return

    # 非自配流程
    show_action("判断是否收餐（问商家、隐私号、问用户）。", "【外呼用户-引导用户继续收餐】")
    is_received = get_user_choice("用户是否已收餐?", ["是", "否"])

    if is_received == "是":
        show_action("致歉商家。", "参考话术：1.非常抱歉给您添麻烦了，小袋联系用户已经收餐，这个是骑手的问题，后续平台会加强骑手的监管。 2.给您和用户带来不好的体验了，小袋会记录骑手问题由平台监管，平台后续会持续关注，避免因骑手问题导致的问题。")
        wants_complaint = get_user_choice("商家是否要求投诉骑手?", ["是", "否"])
        if wants_complaint == "是":
            show_action("转至【投诉骑手】处理流程。")
    else: # 否
        _handle_not_received()

def _handle_not_received():
    """处理用户未收到餐的子流程。"""
    show_action("联系骑手核实餐品情况。", "【外呼骑手-核实是否送达餐品】")
    rider_status = get_user_choice(
        "骑手反馈的餐品情况是?",
        ["餐在骑手处", "餐在用户位置，但并未与共识", "餐品丢失", "联系不到骑手"]
    )

    if rider_status == "餐在骑手处":
        show_action("核实用户是否要餐。", "【外呼用户-引导用户继续收餐】")
        wants_food = get_user_choice("用户是否愿意等待?", ["愿意等待", "不愿意等待"])
        if wants_food == "愿意等待":
            show_action("回复商家，告知用户愿意等待。")
        else:
            show_action("与商家/用户协商退款（骑手责）；如果用户不同意退款流转纠纷。")
    
    elif rider_status == "餐在用户位置，但并未与共识":
        show_action("安抚用户取餐。", "【外呼用户-引导用户继续收餐】")
        show_action("若用户不取餐则协商退款（骑手责）；如果用户不同意退款升级纠纷。")

    elif rider_status == "餐品丢失":
        show_action("与用户/商家协商退款（骑手责），用户不认可可以升级纠纷。", "【外呼用户-协商取消订单】【升级转接】")

    else: # 联系不到骑手
        show_action("根据判责条件判责责任方。")
        responsibility = get_user_choice("责任方是?", ["骑手责", "无法判责/用户责"])
        if responsibility == "骑手责":
            show_action("与用户/商家协商退款，用户不认可可以升级纠纷。")
        else:
            show_action("不建议退款。", "参考话术：小袋联系骑手未接通，这个不是咱们商家问题您不要退款呢，如果用户二次申诉退款会有用户客服介入处理呢。")
