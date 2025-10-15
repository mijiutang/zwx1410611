
'''
处理“无骑手接单”的场景。
严格按照流程图的文字和步骤。
'''
from .utils import get_user_choice, show_action

def handle():
    """处理“无骑手接单”的场景。"""
    print("\n--- 开始处理场景：无骑手接单 ---")
    
    is_over_30_min = get_user_choice("是否已超过无人接单判定时间30分钟，且为非2.0商家", ["是", "否"])

    if is_over_30_min == "是":
        _handle_ask_merchant_demand()
    else:
        is_over_15_min = get_user_choice("无人接单时间是否超过15min", ["是", "否"])
        if is_over_15_min == "是":
            _handle_ask_merchant_demand()
        else:
            show_action("特别注意：如接单时间小于15分钟，优先执行加急方案，如不认可，仅执行话术方案（耐心等待、自配、小费），不执行外呼、退款等方案。")

def _handle_ask_merchant_demand():
    """处理询问商家诉求的流程。"""
    demand = get_user_choice("询问商家诉求：加急or退款", ["加急", "退款"])
    if demand == "加急":
        _handle_expedite()
    else:
        _handle_refund()

def _handle_refund():
    """处理退款流程。"""
    show_action("外呼用户-协商取消订单。")
    call_status = get_user_choice("外呼用户状态", ["接通", "未接通"])
    if call_status == "接通":
        user_agrees = get_user_choice("判断用户是否认可", ["是", "否"])
        if user_agrees == "是":
            show_action("处理整单退款，餐损跟单。")
        else:
            show_action("升级纠纷。")
    else: # 未接通
        show_action("不可退款，建议商家继续联系用户或等待骑手接单（订单跟单）。")

def _handle_expedite():
    """处理加急流程（促履约）。"""
    show_action("进入促履约流程。")
    delivery_type = get_user_choice(
        "判断配送方式",
        ["代理商/专送/混合专送/美团企客配送(站长有派单能力)", "快送/混合快送/全城送/美团跑腿/美团直送（站长无派单能力）", "拼好饭（站长无派单能力）"]
    )
    if delivery_type == "代理商/专送/混合专送/美团企客配送(站长有派单能力)":
        is_over_time = get_user_choice("是否超过无人接单判定时间", ["是", "否"])
        if is_over_time == "是":
            show_action("外呼站长-协调调度骑手或退款。")
        else:
            show_action("外呼站长-协调调度骑手。")
    elif delivery_type == "快送/混合快送/全城送/美团跑腿/美团直送（站长无派单能力）":
        is_over_time = get_user_choice("是否超过无人接单判定时间", ["是", "否"])
        if is_over_time == "是":
            show_action("增加小费或转自配或退款。")
        else:
            show_action("增加小费或转自配。（订单跟单）")
    else: # 拼好饭
        is_over_time = get_user_choice("是否超过无人接单判定时间", ["是", "否"])
        if is_over_time == "是":
            show_action("耐心等待或转自配或退款。")
        else:
            show_action("耐心等待或转自配。（订单跟单）")
