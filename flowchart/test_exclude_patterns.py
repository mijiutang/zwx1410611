#!/usr/bin/env python3
"""
测试排除正则表达式功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.field_constraints import FieldConstraint, ConstraintConfig

def test_exclude_patterns():
    """测试排除正则表达式功能"""
    print("测试排除正则表达式功能...")
    
    # 创建一个带有排除正则表达式的约束
    constraint = FieldConstraint(
        required=True,
        exclude_patterns="test，123，[0-9]+"
    )
    
    # 测试有效值
    test_cases = [
        ("hello", True, "普通字符串应该通过"),
        ("测试", True, "中文字符串应该通过"),
        ("hello123", False, "包含数字应该被排除"),
        ("test", False, "包含test应该被排除"),
        ("123", False, "纯数字应该被排除"),
        ("", False, "空值应该被拒绝（必填）"),
    ]
    
    for value, expected, description in test_cases:
        is_valid, error_msg = constraint.validate(value)
        print(f"测试: '{value}' - 预期: {expected}, 实际: {is_valid} - {description}")
        if is_valid != expected:
            print(f"  错误: {error_msg}")
    
    # 测试多个排除模式
    print("\n测试多个排除模式...")
    constraint_multi = FieldConstraint(
        required=False,
        exclude_patterns="bad，error，[!@#$%^&*]"
    )
    
    test_cases_multi = [
        ("good", True, "good应该通过"),
        ("bad", False, "bad应该被排除"),
        ("error", False, "error应该被排除"),
        ("test@123", False, "包含特殊字符应该被排除"),
        ("", True, "空值应该通过（非必填）"),
    ]
    
    for value, expected, description in test_cases_multi:
        is_valid, error_msg = constraint_multi.validate(value)
        print(f"测试: '{value}' - 预期: {expected}, 实际: {is_valid} - {description}")
        if is_valid != expected:
            print(f"  错误: {error_msg}")

def test_constraint_config():
    """测试约束配置的保存和加载"""
    print("\n测试约束配置的保存和加载...")
    
    # 创建约束配置
    config = ConstraintConfig()
    
    # 添加带有排除正则表达式的约束
    config.add_constraint("username", FieldConstraint(
        required=True,
        exclude_patterns="admin，root，[0-9]+"
    ))
    
    config.add_constraint("email", FieldConstraint(
        required=True,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        exclude_patterns="test，example"
    ))
    
    # 保存到文件
    test_file = ".cache/test_exclude_patterns.yaml"
    os.makedirs(os.path.dirname(test_file), exist_ok=True)
    
    if config.save_to_file(test_file):
        print(f"成功保存约束配置到 {test_file}")
        
        # 读取文件内容
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print("文件内容:")
            print(content)
        
        # 加载配置
        new_config = ConstraintConfig()
        if new_config.load_from_file(test_file):
            print("成功加载约束配置")
            
            # 验证加载的约束
            username_constraint = new_config.get_constraint("username")
            if username_constraint and username_constraint.exclude_patterns:
                print(f"username的排除正则表达式: {username_constraint.exclude_patterns}")
            
            email_constraint = new_config.get_constraint("email")
            if email_constraint:
                print(f"email的正则表达式: {email_constraint.pattern}")
                if email_constraint.exclude_patterns:
                    print(f"email的排除正则表达式: {email_constraint.exclude_patterns}")
        else:
            print("加载约束配置失败")
    else:
        print("保存约束配置失败")

if __name__ == "__main__":
    test_exclude_patterns()
    test_constraint_config()