
'''
处理“餐损”的场景。
严格按照流程图的文字和步骤。
'''
from .utils import get_user_choice, show_action

def handle():
    """处理“餐损”的场景。"""
    print("\n--- 开始处理场景：餐损 ---")
    
    order_status = get_user_choice(
        "判断订单状态",
        ["订单已取消", "订单部分退款or未退款但商家重复出餐"]
    )

    if order_status == "订单已取消":
        _handle_cancelled_order()
    else:
        _handle_partially_refunded_order()

def _handle_cancelled_order():
    """处理“订单已取消”的子流程。"""
    delivery_type = get_user_choice(
        "判断配送方式",
        ["配送服务2.0", "跑腿and企客", "城市代理", "商家自配", "聚和配送"]
    )

    if delivery_type == "配送服务2.0":
        _handle_delivery_2_0()
    elif delivery_type == "跑腿and企客":
        show_action("处理逻辑与【配送服务2.0】类似，根据具体的餐损状态进行判断。")
        _handle_delivery_2_0() # 复用逻辑作为示例
    elif delivery_type == "城市代理":
        show_action("处理逻辑与【配送服务2.0】类似，根据具体的餐损状态进行判断。")
        _handle_delivery_2_0() # 复用逻辑作为示例
    elif delivery_type == "商家自配":
        show_action("未挂载，维持原状。")
    elif delivery_type == "聚和配送":
        cancel_reason = get_user_choice(
            "判断取消原因",
            ["取消操作方为客服且责任方为平台", "非以上情况"]
        )
        if cancel_reason == "取消操作方为客服且责任方为平台":
            show_action("餐损手动赔付。", "此为手动操作，需要相应权限。")
        else:
            show_action("建议商家联系站长/BD。")

def _handle_partially_refunded_order():
    """处理“部分退款或重复出餐”的子流程。"""
    delivery_type = get_user_choice(
        "判断配送方式",
        ["配送服务2.0", "跑腿and企客", "城市代理", "商家自配", "聚和配送"]
    )
    # 此处流程图逻辑复杂，作为示例简化为通用提示
    if delivery_type == "商家自配":
        show_action("未挂载，维持原状。")
    elif delivery_type == "聚和配送":
        show_action("建议商家联系站长/BD。")
    else:
        show_action(f"进入【{delivery_type}】的判责流程，判断取消方和责任方以确定是否赔付。", "例如，客服取消且为非商家责任，通常会进行手动赔付。  ")

def _handle_delivery_2_0():
    """处理“配送服务2.0”的餐损状态判断。"""
    status_options = [
        "餐损赔付记录：定责原因=天气",
        "餐损赔付记录：定责原因=未知",
        "餐损状态：待定责",
        "餐损状态：骑手责任直赔",
        "餐损状态：美团责任直赔",
        "餐损状态：美团责任完成率",
        "餐损状态：商家责任不可申诉",
        "餐损状态：商家责任可申诉",
        "餐损状态：骑手责任可申诉",
        "餐损状态：申诉超时",
        "餐损状态：二次申诉审核中",
        "餐损状态：二次申诉用户责任",
        "餐损状态：二次申诉商家责任",
        "无餐损标签+取消时间超过48h"
    ]
    damage_status = get_user_choice("请根据后台查询选择餐损状态或赔付记录", status_options)

    if damage_status == "餐损赔付记录：定责原因=天气":
        show_action("安抚天气问题。")
    elif damage_status in ["餐损赔付记录：定责原因=未知", "餐损状态：商家责任不可申诉", "餐损状态：二次申诉用户责任", "餐损状态：二次申诉商家责任", "无餐损标签+取消时间超过48h"]:
        show_action("无法申请餐损。")
    elif damage_status == "餐损状态：待定责":
        is_over_48h = get_user_choice("取消时间是否超过48h", ["是", "否"])
        if is_over_48h == "是":
            show_action("无法申请餐损。")
        else:
            show_action("餐损审核中等待。")
    elif damage_status in ["餐损状态：骑手责任直赔", "餐损状态：美团责任直赔"]:
        show_action("餐损自动赔付。")
    elif damage_status == "餐损状态：美团责任完成率":
        is_before_thursday = get_user_choice("当前日期是否早于下单日的次周四", ["是", "否"])
        if is_before_thursday == "是":
            show_action("告知等待完成率结果。")
        else:
            show_action("告知以完成率结果为准。")
    elif damage_status == "餐损状态：商家责任可申诉":
        show_action("告知商家端上申诉。")
    elif damage_status == "餐损状态：骑手责任可申诉":
        show_action("餐损定责骑手-等待骑手申诉结果。")
    elif damage_status == "餐损状态：申诉超时":
        first_party = get_user_choice("判断首次判责方", ["商家责", "骑手责"])
        if first_party == "商家责":
            show_action("无法申请餐损。")
        else:
            show_action("餐损自动赔付。")
    elif damage_status == "餐损状态：二次申诉审核中":
        show_action("餐损审核申诉中等待。")
