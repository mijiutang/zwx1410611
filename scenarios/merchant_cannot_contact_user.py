
'''
处理“商家联系不上用户”的场景。
严格按照流程图的文字和步骤。
'''
from .utils import get_user_choice, show_action

def handle():
    """处理“商家联系不上用户”的场景。"""
    print("\n--- 开始处理场景：商家联系不上用户 ---")
    
    flow_type = get_user_choice("判断履约or售后（根据订单信号、商家诉求）", ["履约", "售后"])

    if flow_type == "售后":
        _handle_after_sales()
    else:
        _handle_fulfillment()

def _handle_after_sales():
    """处理售后的子流程。"""
    reason = get_user_choice("核实商家联系用户的原因", ["评价问题", "非评价问题"])
    if reason == "评价问题":
        show_action("不协助联系（包括不发短信、不提供号码）。", "在线侧：曝光卡片-在线联系用户。电话侧只话术安抚，告知无法帮忙联系，让商家不要担心差评，平台会公正处理。")
    else:
        show_action("协助联系用户。", "【外呼用户-xx】")
        can_contact = get_user_choice("是否能联系上用户?", ["能联系到", "联系不到"])
        if can_contact == "能联系到":
            show_action("根据用户回复反馈给商家。")
        else:
            show_action("短信告知用户商家等待联系，建议商家隐私号IM继续联系用户。", "【短信通知用户-商家等待联系中】+主安抚/建议。联系不到用户-联系跟单。")

def _handle_fulfillment():
    """处理履约的子流程。"""
    payment_status = get_user_choice("判断支付状态", ["未发起退款", "已发起退款"])
    if payment_status == "已发起退款":
        show_action("结合IM隐私号、上文，信号判责责任方。")
        responsibility = get_user_choice("责任方是?", ["用户责", "骑手责"])
        if responsibility == "用户责":
            show_action("用户责不建议退款，告知可拒绝退款。", "参考话术：小袋核实属于用户责任，您可以点拒绝退款，如果后续用户二次申诉退款会有消费者客服介入处理呢。")
        else:
            show_action("可协助骑手责退款，安抚关注餐损定责/后台申请餐损。", "参考话术：小袋核实是骑手责任，小袋可以联系用户判责骑手退款，您看可以吗。餐损跟单。")
    else: # 未发起退款
        _handle_fulfillment_no_refund()

def _handle_fulfillment_no_refund():
    """处理履约中且未发起退款的流程。"""
    show_action("确认餐品位置（隐私号、问商家、问骑手）。", "【外呼骑手-核实餐品所在位置】")
    location = get_user_choice("餐品位置在?", ["在收餐位置", "返餐途中或已返回门店"])
    if location == "在收餐位置":
        show_action("协助联系用户。", "【外呼用户-引导用户继续收餐】")
        can_contact = get_user_choice("是否联系到了用户?", ["联系到了", "联系不到"])
        if can_contact == "联系到了":
            show_action("告知订单情况，如用户同意可以把真实号码告知商家。")
        else:
            show_action("短信告知用户商家等待联系，建议商家隐私号IM继续联系用户。", "【短信通知用户-商家等待联系中】+主动告知餐品处置方案。联系不到用户-联系跟单。餐品处置方案：1.美配：让骑手上报异常先送其他餐品... 2.自配：地址准确的话可以妥善放置并拍照...")
    else: # 返餐途中或已返回门店
        show_action("返餐中：联系骑手是否可以再次配送【外呼骑手-核实骑手是否可以继续配送】。已返回门店：咨询商家是否可再次配送。")
        can_resend = get_user_choice("是否可以再次配送?", ["可以配送", "不可配送"])
        if can_resend == "可以配送":
            show_action("联系用户是否要餐。", "【外呼用户-未送达确认是否还要餐】")
            wants_food = get_user_choice("用户是否要餐?", ["要餐", "不要餐/未联系到用户"])
            if wants_food == "要餐":
                show_action("继续配送（美配30min内需点二次配送）。")
            else:
                show_action("用户责不退款+给商家建议。", "【短信通知用户-商家等待联系中】。对商家的参考话术：1.老板小袋没有联系到用户，如果骑手返餐后用户想要餐可以建议用户自取或支付配送费...。联系不到用户-联系跟单。")
        else: # 不可配送
            show_action("联系用户自取。", "【外呼用户-是否可以到店自取】")
            can_pickup = get_user_choice("用户反馈是?", ["同意自取", "不自取/联系不到"])
            if can_pickup == "同意自取":
                show_action("告知商家用户会来自取。")
            else:
                show_action("用户责不退款。", "未联系到则短信通知用户【短信通知用户-商家等待联系中】。联系不到用户-联系跟单。")
