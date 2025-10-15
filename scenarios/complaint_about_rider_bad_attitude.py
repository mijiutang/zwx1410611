
'''
处理“投诉骑手态度恶劣”的场景。
严格按照流程图的文字和步骤。
'''
from .utils import get_user_choice, show_action

def handle():
    """处理“投诉骑手态度恶劣”的场景。"""
    print("\n--- 开始处理场景：投诉骑手态度恶劣 ---")
    
    is_high_risk = get_user_choice(
        "判断是否高危问题（肢体冲突/恐吓威胁/抢夺等等）",
        ["是", "否"]
    )

    if is_high_risk == "是":
        show_action("流转事件中心处理组。")
    else:
        _handle_non_high_risk()

def _handle_non_high_risk():
    """处理非高危问题的投诉。"""
    delivery_type = get_user_choice(
        "判断配送类型",
        ["快送（混合快送）/专送（加盟）/跑腿", "代理"]
    )

    if delivery_type == "代理":
        show_action("联系代理侧负责人（BD/站长）协助处理，投诉站长联系CM，约定时间回复商家。", "【外呼站长-协助处理投诉问题】")
        show_action("追溯结果后同步商家。")
    else: # 快送/专送/跑腿
        complaint_type = get_user_choice(
            "判断投诉问题类型",
            ["投诉态度问题", "投诉非态度问题"]
        )
        if complaint_type == "投诉态度问题":
            _handle_attitude_complaint()
        else:
            _handle_other_complaint()

def _handle_attitude_complaint():
    """处理态度问题的投诉。"""
    show_action(
        "引导商家后台自行投诉。",
        "参考话术：老板您好，咱们在商家后台可以自行投诉骑手呢，您点击意见反馈-我要投诉—骑手问题—选择对应的场景提交或查看投诉结果，提交后审核时间为2个工作日，您后台关注下结果呢。"
    )
    merchant_agrees = get_user_choice("商家是否认可", ["认可", "不认可"])
    if merchant_agrees == "认可":
        show_action("认可结束-短信发送商家投诉路径。", "参考话术：小袋马上把投诉路径短信发给您，您注意查收呢，您放心，骑手问题平台也会加强监管呢。")
    else:
        show_action(
            "不认可-话术解释安抚，仍引导后台投诉。",
            "参考话术：a.老板，平台很重视您反馈的骑手服务问题，但是确实辛苦您在后台投诉下呢，端上提交的投诉系统会完整记录事件细节，确保信息准确性和后续处理依据；其次是端内投诉会直接触发对骑手的工单系统，平台处理时效快，也能第一时间推动骑手管理团队介入呢。\n"
            "b.老板，确实辛苦您在后台提交下了呢，完整的投诉记录是平台对骑手服务质量考核和改进的重要依据，需要商家侧发起才能形成闭环解决，所以需要您自行在端上完成投诉，感谢您的理解。"
        )

def _handle_other_complaint():
    """处理非态度问题的投诉。"""
    show_action(
        "安抚商家。",
        "参考话术：非常抱歉给您带来不便，小袋协助记录骑手问题会对骑手督导改进，并且会对骑手进行绩效扣款惩罚，为了避免此类问题再次发生，我们也会对骑手加大监控力度，提升服务质量，也希望您持续监督，感谢您的支持和理解。"
    )
    merchant_agrees = get_user_choice("商家是否认可", ["认可", "不认可"])
    if merchant_agrees == "认可":
        show_action("认可结束。")
    else:
        delivery_method = get_user_choice(
            "判断配送方式",
            ["专送（加盟）", "快送/混合快送"]
        )
        if delivery_method == "专送（加盟）":
            show_action("联系站长（我司)处理，投诉站长联系站长上级协助处理。", "【外呼站长-协助处理投诉问题】")
        else: # 快送/混合快送
            show_action("联系站长（非我司）处理，投诉站长联系站长上级协助处理。", "【外呼站长-协助处理投诉问题】")
        show_action("跟进结果回复商家。")
