'''
处理“撒漏”的场景。
严格按照流程图的文字和步骤。
'''
from .utils import get_user_choice, show_action

def handle():
    """处理“撒漏”的场景。"""
    print("\n--- 开始处理场景：餐撒 ---")
    
    refund_status = get_user_choice("是否已发起退款", ["已发起退款", "未发起退款"])

    if refund_status == "已发起退款":
        is_fxc_involved = get_user_choice("是否放心吃理赔中", ["是", "否"])
        if is_fxc_involved == "是":
            show_action("放心吃理赔中，则建议拒绝退款等待放心吃理赔结果。")
        else:
            show_action("未发起放心吃理赔/没有放心吃，处理退款。", "用户如果没有凭证，则通过隐私号或问骑手【外呼骑手-核实餐品是否撒漏】来明确责任方才可给出退款建议。")
    else: # 未发起退款
        has_fxc = get_user_choice("是否有放心吃", ["有放心吃", "无放心吃"])
        if has_fxc == "有放心吃":
            show_action("优先引导申请放心吃。", "【建议商家申请放心吃理赔】；不认可申请放心吃，则走“无放心吃”的方案。")
            use_fxc = get_user_choice("商家是否同意使用放心吃", ["同意", "不同意"])
            if use_fxc == "不同意":
                _handle_no_fxc()
        else:
            _handle_no_fxc()

def _handle_no_fxc():
    """处理没有放心吃保险的流程。"""
    show_action("通过IM隐私号、对话历史、【外呼骑手-核实餐品是否撒漏】等方式明确责任方。")
    responsibility = get_user_choice("责任方是?", ["骑手责任", "非骑手责任"])
    
    if responsibility == "骑手责任":
        show_action("与商家和用户协商退款，双方均认可后才可操作。", "【外呼用户-协商取消订单】、【处理整单/部分退款】")
    else: # 非骑手责任
        show_action(
            "告知商家无法排除商责，退款的话没有餐损。",
            "参考话术：小袋联系骑手表示没有撒餐，不是您的问题的话，您不要同意用户的退款，如果用户二次申诉退款，会有消费者介入，您等待处理结果即可。"
        )
