"""
字段约束配置模块
用于定义和管理表格字段的验证规则
"""

import re
import yaml
import json
import os
from typing import Dict, List, Optional, Union, Callable


class FieldConstraint:
    """字段约束类，定义单个字段的验证规则"""
    
    def __init__(self, 
                 required: bool = False,
                 max_length: Optional[int] = None,
                 min_length: Optional[int] = None,
                 pattern: Optional[str] = None,
                 pattern_description: str = "",
                 options: Optional[List[str]] = None,
                 custom_validator: Optional[Callable[[str], bool]] = None,
                 error_message: str = "输入不符合要求"):
        """
        初始化字段约束
        
        Args:
            required: 是否为必填字段
            max_length: 最大长度限制
            min_length: 最小长度限制
            pattern: 正则表达式模式
            pattern_description: 正则表达式描述
            options: 预定义选项列表
            custom_validator: 自定义验证函数
            error_message: 验证失败时的错误消息
        """
        self.required = required
        self.max_length = max_length
        self.min_length = min_length
        self.pattern = pattern
        self.pattern_description = pattern_description
        self.options = options if options is not None else []
        self.custom_validator = custom_validator
        self.error_message = error_message
        
        # 编译正则表达式
        self.compiled_pattern = re.compile(pattern) if pattern else None
    
    def validate(self, value: str) -> tuple[bool, str]:
        """
        验证输入值是否符合约束
        
        Args:
            value: 要验证的值
            
        Returns:
            (是否通过验证, 错误消息)
        """
        # 必填验证
        if self.required and not value.strip():
            return False, "此字段为必填项"
        
        # 如果值为空且不是必填，则跳过其他验证
        if not value.strip():
            return True, ""
        
        # 长度验证
        if self.max_length is not None and len(value) > self.max_length:
            return False, f"输入长度不能超过{self.max_length}个字符"
            
        if self.min_length is not None and len(value) < self.min_length:
            return False, f"输入长度不能少于{self.min_length}个字符"
        
        # 正则表达式验证
        if self.compiled_pattern and not self.compiled_pattern.match(value):
            return False, self.pattern_description or "输入格式不正确"
        
        # 选项验证
        if self.options and value not in self.options:
            return False, f"请选择预定义选项之一: {', '.join(self.options)}"
        
        # 自定义验证
        if self.custom_validator and not self.custom_validator(value):
            return False, self.error_message
        
        return True, ""


class ConstraintConfig:
    """约束配置管理类"""
    
    def __init__(self):
        """初始化约束配置"""
        self.constraints: Dict[str, FieldConstraint] = {}
        self._load_default_constraints()
    
    def _load_default_constraints(self):
        """加载默认约束配置"""
        # 示例约束配置
        self.add_constraint("是否建议剔除", FieldConstraint(
            required=True,
            options=["是", "否"],
            error_message="请选择'是'或'否'"
        ))
        
        self.add_constraint("剔除原因", FieldConstraint(
            required=False,
            max_length=500,
            error_message="剔除原因不能超过500个字符"
        ))
        
        self.add_constraint("实验场景", FieldConstraint(
            required=True,
            max_length=100,
            error_message="实验场景为必填项且不能超过100个字符"
        ))
        
        self.add_constraint("联系方式", FieldConstraint(
            pattern=r"^1[3-9]\d{9}$",
            pattern_description="请输入有效的11位手机号码",
            error_message="手机号码格式不正确"
        ))
        
        self.add_constraint("邮箱", FieldConstraint(
            pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            pattern_description="请输入有效的邮箱地址",
            error_message="邮箱格式不正确"
        ))
    
    def add_constraint(self, field_name: str, constraint: FieldConstraint):
        """添加字段约束"""
        self.constraints[field_name] = constraint
    
    def remove_constraint(self, field_name: str):
        """移除字段约束"""
        if field_name in self.constraints:
            del self.constraints[field_name]
    
    def get_constraint(self, field_name: str) -> Optional[FieldConstraint]:
        """获取字段约束"""
        return self.constraints.get(field_name)
    
    def validate_field(self, field_name: str, value: str) -> tuple[bool, str]:
        """验证单个字段"""
        constraint = self.get_constraint(field_name)
        if not constraint:
            return True, ""  # 没有约束则默认通过
        
        return constraint.validate(value)
    
    def validate_all(self, data: Dict[str, str]) -> tuple[bool, Dict[str, str]]:
        """
        验证所有字段
        
        Args:
            data: 字段名到值的映射
            
        Returns:
            (是否全部通过验证, 字段名到错误消息的映射)
        """
        all_valid = True
        errors = {}
        
        for field_name, value in data.items():
            is_valid, error_msg = self.validate_field(field_name, value)
            if not is_valid:
                all_valid = False
                errors[field_name] = error_msg
        
        return all_valid, errors
    
    def load_from_file(self, file_path: str):
        """从文件加载约束配置"""
        try:
            # 确保路径格式正确
            normalized_path = os.path.normpath(file_path)
            
            # 检查文件是否存在
            if not os.path.exists(normalized_path):
                print(f"约束文件不存在: {normalized_path}")
                return False
            
            with open(normalized_path, 'r', encoding='utf-8') as f:
                if normalized_path.endswith(('.yml', '.yaml')):
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
                
                # 清空现有约束
                self.constraints.clear()
                
                # 从配置文件加载约束
                # 支持两种格式：带"constraints"包装的和不带包装的
                constraint_data_dict = config_data if 'constraints' not in config_data else config_data['constraints']
                
                for field_name, constraint_data in constraint_data_dict.items():
                    # 处理两种格式的约束数据
                    if isinstance(constraint_data, dict):
                        # 标准格式，包含所有属性
                        # 检查是否是简化的约束格式（只有type, required, description）
                        if 'type' in constraint_data and 'required' in constraint_data and 'description' in constraint_data:
                            # 简化格式，转换为标准格式
                            constraint = FieldConstraint(
                                required=constraint_data.get('required', False),
                                error_message=constraint_data.get('description', f"请输入有效的{field_name}")
                            )
                        else:
                            # 标准格式，包含所有属性
                            constraint = FieldConstraint(
                                required=constraint_data.get('required', False),
                                max_length=constraint_data.get('max_length'),
                                min_length=constraint_data.get('min_length'),
                                pattern=constraint_data.get('pattern'),
                                pattern_description=constraint_data.get('pattern_description', ''),
                                options=constraint_data.get('options', []),
                                error_message=constraint_data.get('error_message', '输入不符合要求')
                            )
                    else:
                        # 简单格式，只包含值
                        constraint = FieldConstraint(
                            required=True,
                            error_message=f"请输入有效的{field_name}"
                        )
                    
                    self.add_constraint(field_name, constraint)
                
                return True
        except Exception as e:
            print(f"加载约束配置文件失败: {e}")
            return False
    
    def save_to_file(self, file_path: str):
        """将约束配置保存到文件"""
        try:
            # 准备保存数据
            save_data = {"constraints": {}}
            
            for field_name, constraint in self.constraints.items():
                constraint_data = {
                    "required": constraint.required,
                    "error_message": constraint.error_message
                }
                
                if constraint.min_length is not None:
                    constraint_data["min_length"] = constraint.min_length
                
                if constraint.max_length is not None:
                    constraint_data["max_length"] = constraint.max_length
                
                if constraint.pattern:
                    constraint_data["pattern"] = constraint.pattern
                
                if constraint.pattern_description:
                    constraint_data["pattern_description"] = constraint.pattern_description
                
                if constraint.options:
                    constraint_data["options"] = constraint.options
                
                save_data["constraints"][field_name] = constraint_data
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.endswith(('.yml', '.yaml')):
                    yaml.dump(save_data, f, allow_unicode=True, default_flow_style=False, indent=2)
                else:
                    json.dump(save_data, f, ensure_ascii=False, indent=4)
            
            return True
        except Exception as e:
            print(f"保存约束配置文件失败: {e}")
            return False


# 全局约束配置实例
constraint_config = ConstraintConfig()