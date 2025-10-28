"""
约束管理界面模块
用于管理和配置字段约束
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QMessageBox, QFileDialog, QHeaderView, QComboBox, 
    QLineEdit, QLabel, QFormLayout, QDialogButtonBox, QTabWidget,
    QTextEdit, QSplitter, QWidget, QCheckBox, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import yaml
import json
from .field_constraints import constraint_config, FieldConstraint


class ConstraintEditDialog(QDialog):
    """约束编辑对话框"""
    
    def __init__(self, field_name="", constraint=None, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.constraint = constraint if constraint else FieldConstraint()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(f"编辑约束 - {self.field_name}")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # 创建表单布局
        form_layout = QFormLayout()
        
        # 字段名称
        self.field_name_edit = QLineEdit(self.field_name)
        form_layout.addRow("字段名称:", self.field_name_edit)
        
        # 必填复选框
        self.required_checkbox = QCheckBox()
        self.required_checkbox.setChecked(self.constraint.required)
        form_layout.addRow("必填字段:", self.required_checkbox)
        
        # 最小长度
        self.min_length_spin = QSpinBox()
        self.min_length_spin.setMinimum(0)
        self.min_length_spin.setMaximum(10000)
        self.min_length_spin.setValue(self.constraint.min_length if self.constraint.min_length is not None else 0)
        form_layout.addRow("最小长度:", self.min_length_spin)
        
        # 最大长度
        self.max_length_spin = QSpinBox()
        self.max_length_spin.setMinimum(0)
        self.max_length_spin.setMaximum(10000)
        self.max_length_spin.setValue(self.constraint.max_length if self.constraint.max_length is not None else 0)
        form_layout.addRow("最大长度:", self.max_length_spin)
        
        # 正则表达式
        self.pattern_edit = QLineEdit(self.constraint.pattern if self.constraint.pattern else "")
        form_layout.addRow("正则表达式:", self.pattern_edit)
        
        # 正则表达式描述
        self.pattern_desc_edit = QLineEdit(self.constraint.pattern_description)
        form_layout.addRow("正则描述:", self.pattern_desc_edit)
        
        # 错误消息
        self.error_msg_edit = QLineEdit(self.constraint.error_message)
        form_layout.addRow("错误消息:", self.error_msg_edit)
        
        # 预定义选项
        self.options_edit = QTextEdit()
        if self.constraint.options:
            self.options_edit.setPlainText("\n".join(self.constraint.options))
        form_layout.addRow("预定义选项(每行一个):", self.options_edit)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_constraint(self):
        """获取编辑后的约束"""
        options_text = self.options_edit.toPlainText().strip()
        options = options_text.split("\n") if options_text else []
        
        min_length = self.min_length_spin.value()
        max_length = self.max_length_spin.value()
        
        return FieldConstraint(
            required=self.required_checkbox.isChecked(),
            min_length=min_length if min_length > 0 else None,
            max_length=max_length if max_length > 0 else None,
            pattern=self.pattern_edit.text().strip() if self.pattern_edit.text().strip() else None,
            pattern_description=self.pattern_desc_edit.text().strip(),
            options=options,
            error_message=self.error_msg_edit.text().strip()
        )


class ConstraintManagerDialog(QDialog):
    """约束管理对话框"""
    
    def __init__(self, constraint_file_path=None, parent=None):
        super().__init__(parent)
        self.constraint_file_path = constraint_file_path
        self.init_ui()
        self.load_constraints()
        
    def init_ui(self):
        self.setWindowTitle("字段约束管理")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        self.add_button = QPushButton("添加约束")
        self.add_button.clicked.connect(self.add_constraint)
        toolbar_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("编辑约束")
        self.edit_button.clicked.connect(self.edit_constraint)
        toolbar_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("删除约束")
        self.delete_button.clicked.connect(self.delete_constraint)
        toolbar_layout.addWidget(self.delete_button)
        
        toolbar_layout.addStretch()
        
        self.load_button = QPushButton("加载配置")
        self.load_button.clicked.connect(self.load_constraints_from_file)
        toolbar_layout.addWidget(self.load_button)
        
        self.save_button = QPushButton("保存配置")
        self.save_button.clicked.connect(self.save_constraints_to_file)
        toolbar_layout.addWidget(self.save_button)
        
        layout.addLayout(toolbar_layout)
        
        # 约束表格
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(7)
        self.table_widget.setHorizontalHeaderLabels([
            "字段名称", "必填", "最小长度", "最大长度", "正则表达式", "选项数量", "错误消息"
        ])
        
        # 设置列宽
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.table_widget)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_constraints(self):
        """加载约束到表格"""
        self.table_widget.setRowCount(0)
        
        for field_name, constraint in constraint_config.constraints.items():
            row = self.table_widget.rowCount()
            self.table_widget.insertRow(row)
            
            # 字段名称
            self.table_widget.setItem(row, 0, QTableWidgetItem(field_name))
            
            # 必填
            self.table_widget.setItem(row, 1, QTableWidgetItem("是" if constraint.required else "否"))
            
            # 最小长度
            min_len = str(constraint.min_length) if constraint.min_length is not None else ""
            self.table_widget.setItem(row, 2, QTableWidgetItem(min_len))
            
            # 最大长度
            max_len = str(constraint.max_length) if constraint.max_length is not None else ""
            self.table_widget.setItem(row, 3, QTableWidgetItem(max_len))
            
            # 正则表达式
            pattern = constraint.pattern if constraint.pattern else ""
            self.table_widget.setItem(row, 4, QTableWidgetItem(pattern))
            
            # 选项数量
            option_count = str(len(constraint.options)) if constraint.options else "0"
            self.table_widget.setItem(row, 5, QTableWidgetItem(option_count))
            
            # 错误消息
            self.table_widget.setItem(row, 6, QTableWidgetItem(constraint.error_message))
    
    def add_constraint(self):
        """添加新约束"""
        dialog = ConstraintEditDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            field_name = dialog.field_name_edit.text().strip()
            if field_name:
                constraint_config.add_constraint(field_name, dialog.get_constraint())
                self.load_constraints()
    
    def edit_constraint(self):
        """编辑选中的约束"""
        current_row = self.table_widget.currentRow()
        if current_row >= 0:
            field_name = self.table_widget.item(current_row, 0).text()
            constraint = constraint_config.get_constraint(field_name)
            
            dialog = ConstraintEditDialog(field_name, constraint, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_field_name = dialog.field_name_edit.text().strip()
                if new_field_name:
                    # 如果字段名改变，先删除旧的
                    if new_field_name != field_name:
                        constraint_config.remove_constraint(field_name)
                    
                    constraint_config.add_constraint(new_field_name, dialog.get_constraint())
                    self.load_constraints()
    
    def delete_constraint(self):
        """删除选中的约束"""
        current_row = self.table_widget.currentRow()
        if current_row >= 0:
            field_name = self.table_widget.item(current_row, 0).text()
            reply = QMessageBox.question(
                self, "确认删除", 
                f"确定要删除字段 '{field_name}' 的约束吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                constraint_config.remove_constraint(field_name)
                self.load_constraints()
    
    def load_constraints_from_file(self):
        """从文件加载约束配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择约束配置文件", "", "YAML文件 (*.yaml *.yml);;JSON文件 (*.json);;所有文件 (*)"
        )
        
        if file_path:
            if constraint_config.load_from_file(file_path):
                self.constraint_file_path = file_path
                self.load_constraints()
                QMessageBox.information(self, "成功", "约束配置加载成功！")
            else:
                QMessageBox.warning(self, "错误", "约束配置加载失败！")
    
    def save_constraints_to_file(self):
        """保存约束配置到文件"""
        if not self.constraint_file_path:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存约束配置", "field_constraints.yaml", 
                "YAML文件 (*.yaml *.yml);;JSON文件 (*.json);;所有文件 (*)"
            )
            if file_path:
                self.constraint_file_path = file_path
        
        if self.constraint_file_path:
            try:
                # 准备保存数据
                save_data = {"constraints": {}}
                
                for field_name, constraint in constraint_config.constraints.items():
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
                with open(self.constraint_file_path, 'w', encoding='utf-8') as f:
                    if self.constraint_file_path.endswith(('.yml', '.yaml')):
                        yaml.dump(save_data, f, allow_unicode=True, default_flow_style=False, indent=2)
                    else:
                        json.dump(save_data, f, ensure_ascii=False, indent=4)
                
                QMessageBox.information(self, "成功", f"约束配置已保存到 {self.constraint_file_path}")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"保存约束配置失败: {e}")