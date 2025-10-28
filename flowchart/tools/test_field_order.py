#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试约束编辑器的字段顺序保持功能
"""

import sys
import os
import tempfile
import yaml
from collections import OrderedDict

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from constraint_editor import ConstraintConfig, FieldConstraint

def test_field_order():
    """测试字段顺序是否保持"""
    # 创建临时测试文件
    test_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8')
    
    # 创建有序的测试数据
    test_data = OrderedDict()
    test_data["zebra_field"] = {
        "type": "string",
        "required": True,
        "description": "Zebra字段"
    }
    test_data["apple_field"] = {
        "type": "string",
        "required": False,
        "description": "Apple字段"
    }
    test_data["banana_field"] = {
        "type": "string",
        "required": True,
        "description": "Banana字段"
    }
    
    # 写入测试文件
    yaml.dump(test_data, test_file, allow_unicode=True, default_flow_style=False, indent=2)
    test_file.close()
    
    # 加载文件
    config = ConstraintConfig()
    success = config.load_from_file(test_file.name)
    
    if not success:
        print("加载测试文件失败")
        return False
    
    # 检查字段顺序
    field_names = list(config.constraints.keys())
    expected_order = ["zebra_field", "apple_field", "banana_field"]
    
    if field_names == expected_order:
        print("字段顺序保持正确:", field_names)
    else:
        print("字段顺序不正确:", field_names)
        print("期望顺序:", expected_order)
        return False
    
    # 保存文件
    save_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8')
    save_file.close()
    
    success = config.save_to_file(save_file.name)
    
    if not success:
        print("保存测试文件失败")
        return False
    
    # 读取保存的文件并检查顺序
    with open(save_file.name, 'r', encoding='utf-8') as f:
        saved_data = yaml.safe_load(f)
    
    saved_field_names = list(saved_data.keys())
    
    if saved_field_names == expected_order:
        print("保存后字段顺序保持正确:", saved_field_names)
    else:
        print("保存后字段顺序不正确:", saved_field_names)
        print("期望顺序:", expected_order)
        return False
    
    # 清理临时文件
    os.unlink(test_file.name)
    os.unlink(save_file.name)
    
    return True

if __name__ == "__main__":
    print("测试字段顺序保持功能...")
    if test_field_order():
        print("测试通过！")
    else:
        print("测试失败！")