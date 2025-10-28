#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
独立的约束配置编辑器
用于编辑和管理字段约束配置文件
"""

import sys
import os
import json
import yaml
from typing import Dict, List, Optional, Tuple

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QDialog, QDialogButtonBox,
    QMessageBox, QFileDialog, QHeaderView, QLabel, QComboBox,
    QLineEdit, QTextEdit, QCheckBox, QSpinBox, QFormLayout,
    QAbstractItemView
)
from PyQt6.QtCore import Qt


class FieldConstraint:
    """字段约束类"""
    
    def __init__(
        self,
        required: bool = False,
        pattern: Optional[str] = None,
        pattern_description: str = "",
        options: Optional[List[str]] = None,
        error_message: str = "",
        exclude_patterns: Optional[str] = None
    ):
        self.required = required
        self.pattern = pattern
        self.pattern_description = pattern_description
        self.options = options or []
        self.error_message = error_message
        self.exclude_patterns = exclude_patterns
        
        # 编译正则表达式
        import re
        self.compiled_pattern = re.compile(pattern) if pattern else None
        
        # 编译排除正则表达式
        self.compiled_exclude_patterns = []
        if exclude_patterns:
            # 每行一个排除模式
            patterns = [p.strip() for p in exclude_patterns.split('\n') if p.strip()]
            for p in patterns:
                try:
                    self.compiled_exclude_patterns.append(re.compile(p))
                except re.error as e:
                    print(f"无效的排除正则表达式 '{p}': {e}")
    
    def validate(self, value: str) -> Tuple[bool, str]:
        """验证输入值是否符合约束"""
        # 必填验证
        if self.required and not value.strip():
            return False, self.error_message or "此字段为必填项"
        
        # 如果值为空且不是必填，则跳过其他验证
        if not value.strip():
            return True, ""
        
        # 排除正则表达式验证 - 检查是否包含排除的字符或模式
        for compiled_pattern in self.compiled_exclude_patterns:
            if compiled_pattern.search(value):
                return False, f"输入不能包含: {compiled_pattern.pattern}"
        
        # 正则表达式验证
        if self.compiled_pattern and not self.compiled_pattern.match(value):
            return False, self.pattern_description or self.error_message or "输入格式不正确"
        
        # 选项验证
        if self.options and value not in self.options:
            return False, f"请选择预定义选项之一: {', '.join(self.options)}"
        
        return True, ""


class ConstraintConfig:
    """约束配置管理类"""
    
    def __init__(self):
        """初始化约束配置"""
        from collections import OrderedDict
        self.constraints: OrderedDict = OrderedDict()
    
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
    
    def load_from_file(self, file_path: str) -> bool:
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
                
                # 使用有序字典保持原始顺序
                from collections import OrderedDict
                if isinstance(constraint_data_dict, dict):
                    # 如果是普通字典，转换为OrderedDict保持原始顺序
                    ordered_constraints = OrderedDict()
                    for field_name, constraint_data in constraint_data_dict.items():
                        # 处理两种格式的约束数据
                        if isinstance(constraint_data, dict):
                            # 检查是否是简化的约束格式（只有type, required, description）
                            if 'type' in constraint_data and 'required' in constraint_data and 'description' in constraint_data:
                                # 简化格式，转换为标准格式
                                constraint = FieldConstraint(
                                    required=constraint_data.get('required', False),
                                    pattern=constraint_data.get('pattern'),
                                    pattern_description=constraint_data.get('pattern_description', ''),
                                    options=constraint_data.get('options', []),
                                    error_message=constraint_data.get('description', f"请输入有效的{field_name}"),
                                    exclude_patterns=constraint_data.get('exclude_patterns')
                                )
                            else:
                                # 标准格式，包含所有属性
                                constraint = FieldConstraint(
                                    required=constraint_data.get('required', False),
                                    pattern=constraint_data.get('pattern'),
                                    pattern_description=constraint_data.get('pattern_description', ''),
                                    options=constraint_data.get('options', []),
                                    error_message=constraint_data.get('error_message', '输入不符合要求'),
                                    exclude_patterns=constraint_data.get('exclude_patterns')
                                )
                        else:
                            # 简单格式，只包含值
                            constraint = FieldConstraint(
                                required=True,
                                error_message=f"请输入有效的{field_name}"
                            )
                        
                        ordered_constraints[field_name] = constraint
                    
                    # 使用OrderedDict替换普通字典
                    self.constraints = ordered_constraints
                
                return True
        except Exception as e:
            print(f"加载约束配置文件失败: {e}")
            return False
    
    def save_to_file(self, file_path: str) -> bool:
        """将约束配置保存到文件"""
        try:
            from collections import OrderedDict
            
            # 准备保存数据 - 使用统一的格式（不带constraints包装，使用type/description格式）
            save_data = OrderedDict()
            
            for field_name, constraint in self.constraints.items():
                # 使用统一的type/description格式
                constraint_data = OrderedDict()
                constraint_data["type"] = "string"
                constraint_data["required"] = constraint.required
                constraint_data["description"] = constraint.error_message
                
                if constraint.pattern:
                    constraint_data["pattern"] = constraint.pattern
                
                if constraint.pattern_description:
                    constraint_data["pattern_description"] = constraint.pattern_description
                
                if constraint.options:
                    constraint_data["options"] = constraint.options
                
                if constraint.exclude_patterns:
                    constraint_data["exclude_patterns"] = constraint.exclude_patterns
                
                save_data[field_name] = constraint_data
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.endswith(('.yml', '.yaml')):
                    # 使用自定义Dumper保持顺序
                    class OrderedDumper(yaml.SafeDumper):
                        pass
                    
                    def dict_representer(dumper, data):
                        return dumper.represent_mapping(
                            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                            data.items()
                        )
                    
                    OrderedDumper.add_representer(OrderedDict, dict_representer)
                    
                    yaml.dump(save_data, f, Dumper=OrderedDumper, 
                             allow_unicode=True, default_flow_style=False, indent=2,
                             sort_keys=False)  # 关键：不按键排序
                else:
                    json.dump(save_data, f, ensure_ascii=False, indent=4)
            
            return True
        except Exception as e:
            print(f"保存约束配置文件失败: {e}")
            return False


class ConstraintEditDialog(QDialog):
    """约束编辑对话框"""
    
    def __init__(self, field_name: str = "", constraint: Optional[FieldConstraint] = None, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.constraint = constraint
        
        self.setWindowTitle("编辑约束")
        self.setModal(True)
        self.resize(500, 400)
        
        self.init_ui()
        
        if self.constraint:
            self.load_constraint()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 表单布局
        form_layout = QFormLayout()
        
        # 字段名称
        self.field_name_edit = QLineEdit(self.field_name)
        form_layout.addRow("字段名称:", self.field_name_edit)
        
        # 必填
        self.required_check = QCheckBox()
        form_layout.addRow("必填:", self.required_check)
        
        # 正则表达式
        self.pattern_edit = QLineEdit()
        form_layout.addRow("正则表达式:", self.pattern_edit)
        
        # 正则表达式描述
        self.pattern_desc_edit = QLineEdit()
        form_layout.addRow("正则表达式描述:", self.pattern_desc_edit)
        
        # 选项
        self.options_edit = QTextEdit()
        self.options_edit.setPlaceholderText("每行一个选项")
        self.options_edit.setMaximumHeight(100)
        form_layout.addRow("选项:", self.options_edit)
        
        # 错误消息
        self.error_message_edit = QLineEdit()
        form_layout.addRow("错误消息:", self.error_message_edit)
        
        # 排除正则表达式
        self.exclude_patterns_edit = QTextEdit()
        self.exclude_patterns_edit.setPlaceholderText("每行一个排除正则表达式")
        self.exclude_patterns_edit.setMaximumHeight(60)
        form_layout.addRow("排除正则表达式:", self.exclude_patterns_edit)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_constraint(self):
        """加载约束数据"""
        if not self.constraint:
            return
        
        self.required_check.setChecked(self.constraint.required)
        self.pattern_edit.setText(self.constraint.pattern or "")
        self.pattern_desc_edit.setText(self.constraint.pattern_description or "")
        
        if self.constraint.options:
            self.options_edit.setPlainText("\n".join(self.constraint.options))
        
        self.error_message_edit.setText(self.constraint.error_message)
        
        if hasattr(self.constraint, 'exclude_patterns') and self.constraint.exclude_patterns:
            self.exclude_patterns_edit.setPlainText(self.constraint.exclude_patterns)
    
    def get_constraint(self) -> FieldConstraint:
        """获取约束数据"""
        options = []
        if self.options_edit.toPlainText().strip():
            # 获取选项并去重，保持顺序
            seen = set()
            unique_options = []
            for line in self.options_edit.toPlainText().split("\n"):
                option = line.strip()
                if option and option not in seen:
                    seen.add(option)
                    unique_options.append(option)
            options = unique_options
        
        exclude_patterns = self.exclude_patterns_edit.toPlainText().strip()
        
        # 对排除正则表达式进行去重处理
        if exclude_patterns:
            seen_patterns = set()
            unique_patterns = []
            for line in exclude_patterns.split("\n"):
                pattern = line.strip()
                if pattern and pattern not in seen_patterns:
                    seen_patterns.add(pattern)
                    unique_patterns.append(pattern)
            exclude_patterns = "\n".join(unique_patterns)
        
        return FieldConstraint(
            required=self.required_check.isChecked(),
            pattern=self.pattern_edit.text().strip() or None,
            pattern_description=self.pattern_desc_edit.text().strip(),
            options=options,
            error_message=self.error_message_edit.text().strip() or "输入不符合要求",
            exclude_patterns=exclude_patterns if exclude_patterns else None
        )


class ConstraintEditorWindow(QMainWindow):
    """约束编辑器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.constraint_config = ConstraintConfig()
        self.current_file_path = None
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache")
        
        self.setWindowTitle("约束配置编辑器")
        self.setGeometry(100, 100, 800, 600)
        
        self.init_ui()
        self.scan_cache_files()
    
    def init_ui(self):
        """初始化UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 文件路径显示和选择
        file_layout = QHBoxLayout()
        
        self.file_combo = QComboBox()
        self.file_combo.setMinimumWidth(400)
        self.file_combo.currentTextChanged.connect(self.on_file_selected)
        file_layout.addWidget(QLabel("约束文件:"))
        file_layout.addWidget(self.file_combo)
        
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.scan_cache_files)
        file_layout.addWidget(self.refresh_button)
        
        layout.addLayout(file_layout)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        self.open_button = QPushButton("打开文件")
        self.open_button.clicked.connect(self.open_file)
        toolbar_layout.addWidget(self.open_button)
        
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_file)
        self.save_button.setEnabled(False)
        toolbar_layout.addWidget(self.save_button)
        
        toolbar_layout.addStretch()
        
        self.edit_button = QPushButton("编辑约束")
        self.edit_button.clicked.connect(self.edit_constraint)
        toolbar_layout.addWidget(self.edit_button)
        
        layout.addLayout(toolbar_layout)
        
        # 约束表格
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels([
            "字段名称", "必填", "正则表达式", "选项数量", "错误消息", "排除正则表达式"
        ])
        
        # 禁用表格编辑功能
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # 添加双击事件处理
        self.table_widget.cellDoubleClicked.connect(self.on_table_double_clicked)
        
        # 设置列宽
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.table_widget)
    
    def open_file(self):
        """打开约束文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择约束配置文件", "", "YAML文件 (*.yaml *.yml);;JSON文件 (*.json);;所有文件 (*)"
        )
        
        if file_path:
            if self.constraint_config.load_from_file(file_path):
                self.current_file_path = file_path
                self.file_path_label.setText(f"当前文件: {file_path}")
                self.save_button.setEnabled(True)
                self.load_constraints()
                
                # 更新窗口标题，显示当前打开的文件名
                file_name = os.path.basename(file_path)
                base_name = os.path.splitext(file_name)[0]  # 去掉扩展名
                self.setWindowTitle(f"约束配置编辑器 - {base_name}")
            else:
                QMessageBox.warning(self, "错误", "约束配置加载失败！")
    
    def save_file(self):
        """保存约束文件"""
        if self.current_file_path:
            if self.constraint_config.save_to_file(self.current_file_path):
                QMessageBox.information(self, "成功", f"约束配置已保存到 {self.current_file_path}")
            else:
                QMessageBox.warning(self, "错误", "保存约束配置失败！")
    
    def load_constraints(self):
        """加载约束到表格"""
        self.table_widget.setRowCount(0)
        
        for field_name, constraint in self.constraint_config.constraints.items():
            row = self.table_widget.rowCount()
            self.table_widget.insertRow(row)
            
            # 字段名称
            self.table_widget.setItem(row, 0, QTableWidgetItem(field_name))
            
            # 必填
            self.table_widget.setItem(row, 1, QTableWidgetItem("是" if constraint.required else "否"))
            
            # 正则表达式
            pattern = constraint.pattern if constraint.pattern else ""
            self.table_widget.setItem(row, 2, QTableWidgetItem(pattern))
            
            # 选项数量
            option_count = str(len(constraint.options)) if constraint.options else "0"
            self.table_widget.setItem(row, 3, QTableWidgetItem(option_count))
            
            # 错误消息
            self.table_widget.setItem(row, 4, QTableWidgetItem(constraint.error_message))
            
            # 排除正则表达式
            exclude_patterns = getattr(constraint, 'exclude_patterns', '') if hasattr(constraint, 'exclude_patterns') else ""
            self.table_widget.setItem(row, 5, QTableWidgetItem(exclude_patterns))
    
    def on_table_double_clicked(self, row, column):
        """处理表格双击事件"""
        # 设置当前行为选中行
        self.table_widget.selectRow(row)
        # 调用编辑约束方法
        self.edit_constraint()
    
    def edit_constraint(self):
        """编辑选中的约束"""
        current_row = self.table_widget.currentRow()
        if current_row >= 0:
            field_name = self.table_widget.item(current_row, 0).text()
            constraint = self.constraint_config.get_constraint(field_name)
            
            dialog = ConstraintEditDialog(field_name, constraint, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_field_name = dialog.field_name_edit.text().strip()
                if new_field_name:
                    # 如果字段名改变，先删除旧的
                    if new_field_name != field_name:
                        self.constraint_config.remove_constraint(field_name)
                    
                    self.constraint_config.add_constraint(new_field_name, dialog.get_constraint())
                    self.load_constraints()
    
    def scan_cache_files(self):
        """扫描缓存目录中的YAML文件"""
        self.file_combo.clear()
        
        if not os.path.exists(self.cache_dir):
            QMessageBox.warning(self, "警告", f"缓存目录不存在: {self.cache_dir}")
            return
        
        # 获取所有YAML文件
        yaml_files = []
        for file in os.listdir(self.cache_dir):
            if file.endswith(('.yaml', '.yml')):
                yaml_files.append(file)
        
        if not yaml_files:
            QMessageBox.information(self, "信息", "缓存目录中没有找到YAML约束文件")
            return
        
        # 按名称排序
        yaml_files.sort()
        
        # 添加到下拉框
        self.file_combo.addItems(yaml_files)
        
        # 默认选择第一个文件
        if yaml_files:
            self.on_file_selected(yaml_files[0])
    
    def on_file_selected(self, file_name):
        """当选择文件时触发"""
        if not file_name:
            return
            
        file_path = os.path.join(self.cache_dir, file_name)
        if self.constraint_config.load_from_file(file_path):
            self.current_file_path = file_path
            self.load_constraints()
            self.save_button.setEnabled(True)
            
            # 更新窗口标题，显示当前选择的文件名
            base_name = os.path.splitext(file_name)[0]  # 去掉扩展名
            self.setWindowTitle(f"约束配置编辑器 - {base_name}")
        else:
            QMessageBox.warning(self, "错误", f"加载约束文件失败: {file_name}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = ConstraintEditorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()