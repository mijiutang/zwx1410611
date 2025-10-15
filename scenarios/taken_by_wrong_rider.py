'''
处理“被其他骑手拿走/偷餐”的场景。
严格按照流程图的文字和步骤。
'''
from .utils import get_user_choice, show_action

def handle():
    """处理“被其他骑手拿走/偷餐”的场景。"""
    print("\n--- 开始处理场景：被其他骑手拿走/偷餐 ---")
    
    scenario = get_user_choice("请根据商家描述选择场景", ["骑手取错餐", "商家描述“偷餐”"])

    if scenario == "骑手取错餐":
        _handle_wrong_rider()
    else: # 偷餐
        _handle_stolen()

def _handle_wrong_rider():
    """处理取错餐的子流程。"""
    is_meituan_rider = get_user_choice("判断是否为美团骑手", ["是", "否/无法判断"])
    
    if is_meituan_rider == "是":
        show_action("确认取错餐的骑手（问商家）。")
        rider_response = get_user_choice(
            "联系骑手确认是否可以15min返餐及返餐时间",
            ["承认，可送回", "承认，无法送回", "不承认/不送回/联系不上"]
        )
        if rider_response == "承认，可送回":
            show_action("同步商家，建议等待骑手换餐。")
        elif rider_response == "承认，无法送回":
            show_action("与商家/用户协商退款（骑手责）；如用户不认可可升级纠纷。")
        else: # 不承认/不送回/联系不上
            show_action("信商，默认骑手责任，【外呼用户-协商取消订单】用户不认可退款升级纠纷。")
    else: # 否/无法判断
        show_action("建议商家自行排查/自行联系骑手协商返餐。")
        show_action("如果商家联系骑手后未联系到/无法返餐，引导重复出餐，商责不赔付。")

def _handle_stolen():
    """处理偷餐的子流程。"""
    show_action("索要凭证，核实是否有“美团”元素（头盔、餐箱、服装等），不主动问商家是否美团元素骑手。", "【询问商家提供取餐凭证】")
    has_meituan_element = get_user_choice("凭证中是否有美团元素?", ["有美团元素", "没有美团元素/没有凭证"])

    if has_meituan_element == "有美团元素":
        demand = get_user_choice("判断商家诉求", ["餐损", "处罚骑手"])
        if demand == "餐损":
            show_action("转至【骑手取错餐】-【是美团骑手】的流程处理。")
            _handle_wrong_rider() # 复用取错餐的逻辑
        else:
            show_action("升级风控1小时回复。")
    else: # 没有美团元素/没有凭证
        show_action("按【骑手取错餐】-【否/无法判断】的流程处理。")
        show_action("建议商家自行排查/自行联系骑手协商返餐。")
        show_action("如果商家联系骑手后未联系到/无法返餐，引导重复出餐，商责不赔付。")