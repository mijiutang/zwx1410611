
'''
处理“骑手接单不取餐”的场景。
严格按照流程图的文字和步骤。
'''
from .utils import get_user_choice, show_action

def handle():
    """处理“骑手接单不取餐”的场景。"""
    print("\n--- 开始处理场景：骑手接单不取餐 ---")
    
    order_status = get_user_choice("判断订单状态", ["进行中", "已取消", "已完成"])

    if order_status == "已取消":
        show_action("转至【餐损】处理流程。")
        # from . import food_damage
        # food_damage.handle()
    elif order_status == "已完成":
        show_action("告知商家订单已完成，进一步核实商家问题。", "参考话术：1.查看您的订单显示已完成，是还有其他问题需要处理吗？ 2.看到您的订单骑手已经点送达了，您是想反馈骑手接单后取餐慢的情况吗？")
    else: # 进行中
        _handle_in_progress()

def _handle_in_progress():
    """处理“进行中”订单的子流程。"""
    rider_status = get_user_choice(
        "外呼骑手是否可以取餐",
        ["可以取餐", "无法取餐", "联系不到骑手"]
    )

    if rider_status == "可以取餐":
        show_action("反馈商家即可。")
    elif rider_status == "无法取餐":
        has_terminate_button = get_user_choice("判断是否有终止调度按钮", ["有终止按钮", "没有终止按钮"])
        if has_terminate_button == "有终止按钮":
            show_action("与商家共识取消配送，引导商家重新发起配送。", "【终止调度】参考话术：您久等了老板，小袋联系骑手核实到骑手无法继续配送了，为了不影响订单履约，小袋帮您取消配送，您可以后台重新发起配送，等待新的骑手取餐，您看可以吗")
        else:
            _handle_no_terminate_button()
    else: # 联系不到骑手
        has_refund_demand = get_user_choice("根据隐私号、历史对话判断商家是否有退款诉求", ["是", "否"])
        if has_refund_demand == "是":
            _handle_refund_package()
        else:
            _handle_no_terminate_button() # 逻辑复用

def _handle_no_terminate_button():
    """处理没有终止按钮时的配送方式判断。"""
    delivery_type = get_user_choice(
        "判断配送方式",
        ["专送（加盟）/代理商", "美团跑腿", "快送/混合快送/全程送", "非以上配送方式"]
    )

    if delivery_type == "专送（加盟）/代理商":
        show_action("联系站长是否可协助调度。", "【外呼站长-协调调度骑手】")
    elif delivery_type == "美团跑腿":
        is_over_20_min = get_user_choice("超骑手接单时间20分钟", ["是", "否"])
        if is_over_20_min == "是":
            show_action("引导商家后台点击催取餐。")
        else:
            show_action("安抚等待取餐。")
    elif delivery_type == "快送/混合快送/全程送":
        is_prep_over_10_min = get_user_choice("出餐时间大于10分钟", ["是", "否"])
        if is_prep_over_10_min == "是":
            show_action("建议商家换骑手（按钮）。")
        else:
            show_action("建议商家催取餐（按钮）。")
    else: # 非以上配送方式
        show_action("引导商家自配或安抚耐心等待。", "参考话术：为了用户有更好的收餐体验，建议您可以转自配送餐，平台会为您补偿配送费，您看可以吗")

def _handle_refund_package():
    """处理退款方案包的占位符。"""
    show_action("执行【退款方案包】。", "此方案包逻辑复杂，通常包括：根据是否超时判断责任方（骑手/平台），然后联系用户协商退款。如用户不同意则升级纠纷。")
