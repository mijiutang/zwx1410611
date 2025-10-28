from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QAbstractItemView, QMessageBox, QComboBox, QHeaderView
from PyQt6.QtCore import pyqtSignal, Qt
from .dock.combo_box_delegate import ComboBoxDelegate # Import the new delegate
from .field_constraints import constraint_config # Import the constraint configuration
import os
import json
import yaml

class KeyValueEditorWidget(QWidget):
    data_changed = pyqtSignal(dict)

    def __init__(self, initial_data=None, parent=None):
        super().__init__(parent)
        self.current_data = initial_data if initial_data is not None else {}
        self.task_item_options = {} # Stores options for each task item
        self.save_target_file_path = None # New attribute to store the target file for saving
        
        # 尝试加载约束配置文件
        cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")
        constraint_file_path = os.path.join(cache_dir, "field_constraints.yaml")
        if os.path.exists(constraint_file_path):
            constraint_config.load_from_file(constraint_file_path)
            # 从约束配置中提取字段和选项
            self._load_fields_from_constraints()
        
        self.init_ui()
        
        # Set the custom delegate for the "内容" column (column 1) AFTER task_item_options is loaded
        self.combo_box_delegate = ComboBoxDelegate(self, self.task_item_options)
        self.table_widget.setItemDelegateForColumn(1, self.combo_box_delegate)
        self.combo_box_delegate.add_option_requested.connect(self._handle_add_option_request) # Connect the new signal
        
        # 设置表格属性，避免重影
        self.table_widget.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        # 移除WA_OpaquePaintEvent属性，因为它可能导致黑色背景问题

    def _load_fields_from_constraints(self):
        """从约束配置中提取字段和选项"""
        self.task_item_options = {}
        
        # 遍历约束配置中的所有字段
        for field_name, constraint in constraint_config.constraints.items():
            # 如果字段有预定义选项，则使用这些选项
            if hasattr(constraint, 'options') and constraint.options:
                self.task_item_options[field_name] = constraint.options
            else:
                # 否则创建空列表，表示可以自由输入
                self.task_item_options[field_name] = []
        
        # 更新ComboBoxDelegate的选项
        if hasattr(self, 'combo_box_delegate'):
            self.combo_box_delegate.update_options(self.task_item_options)
            
        # 重新加载当前数据以更新表格中的下拉框
        if hasattr(self, 'current_data') and self.current_data:
            self.load_data(self.current_data)
    
    def init_ui(self):
        self.main_layout = QVBoxLayout(self)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["任务项", "内容"])
        # Auto-resize columns
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Key column
        self.table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Value column
        # Auto-adjust row height for word wrap
        self.table_widget.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table_widget.setWordWrap(True) # Re-enable word wrap for the table
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.AnyKeyPressed)
        self.table_widget.itemChanged.connect(self.save_changes) # Connect itemChanged for auto-save
        self.main_layout.addWidget(self.table_widget)
        self.table_widget.hide() # Hide initially

        self.load_data(self.current_data)

        control_layout = QHBoxLayout()
        
        self.main_layout.addLayout(control_layout)



    def load_data(self, data):
        # 断开信号，防止在加载数据时触发保存
        try:
            self.table_widget.itemChanged.disconnect(self.save_changes)
        except TypeError:
            # 如果信号未连接，则忽略错误
            pass 
        
        # 彻底清理表格，避免残留
        # 1. 关闭所有活动的编辑器
        for row in range(self.table_widget.rowCount()):
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item:
                    self.table_widget.closePersistentEditor(item)
        
        # 2. 移除所有单元格部件
        for row in range(self.table_widget.rowCount()):
            for col in range(self.table_widget.columnCount()):
                widget = self.table_widget.cellWidget(row, col)
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()
                    self.table_widget.removeCellWidget(row, col)
        
        # 3. 清除所有表格项
        self.table_widget.clearContents()
        
        # 4. 清除所有行
        self.table_widget.setRowCount(0)
        
        # 5. 重置表格选择和当前单元格
        self.table_widget.setCurrentCell(-1, -1)
        self.table_widget.clearSelection()
        
        # 6. 强制刷新视图
        self.table_widget.viewport().update()
        self.table_widget.update()
        
        # 7. 重置表格样式
        self.table_widget.setStyleSheet("")
        
        self.current_data = data
        
        for key, value in self.current_data.items():
            row_position = self.table_widget.rowCount()
            self.table_widget.insertRow(row_position)
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemFlag.ItemIsEditable) # Make key column non-editable
            self.table_widget.setItem(row_position, 0, key_item)
            
            # Always create a QTableWidgetItem for the value column
            item = QTableWidgetItem(str(value))
            # The TextWordWrap flag is deprecated in PyQt6 and was causing a crash.
            # The word wrap is handled by the table view's properties now.
            self.table_widget.setItem(row_position, 1, item)

        # 重新连接信号
        self.table_widget.itemChanged.connect(self.save_changes)
        
        # 确保表格在加载数据后可见
        self.table_widget.show()

    def save_changes(self):
        # 关闭所有活动的编辑器，避免重影
        # QTableWidget没有closePersistentEditors方法，需要逐个关闭
        for row in range(self.table_widget.rowCount()):
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item:
                    self.table_widget.closePersistentEditor(item)
        
        updated_data = {}
        for i in range(self.table_widget.rowCount()):
            key_item = self.table_widget.item(i, 0)
            # Try to get QComboBox first, then QTableWidgetItem
            value_widget = self.table_widget.cellWidget(i, 1)
            value = ""
            if isinstance(value_widget, QComboBox):
                value = value_widget.currentText()
            else:
                value_item = self.table_widget.item(i, 1)
                if value_item:
                    value = value_item.text()

            if key_item:
                key = key_item.text()
                if key:
                    updated_data[key] = value
                else:
                    QMessageBox.warning(self, "警告", f"第 {i+1} 行的键不能为空，该行将被忽略。")
        
        # 验证数据是否符合约束
        is_valid, errors = constraint_config.validate_all(updated_data)
        if not is_valid:
            # 显示验证错误
            error_messages = []
            for field_name, error_msg in errors.items():
                error_messages.append(f"- {field_name}: {error_msg}")
            
            QMessageBox.warning(
                self, 
                "验证失败", 
                "以下字段不符合约束要求:\n\n" + "\n".join(error_messages)
            )
            return False  # 验证失败，不保存数据
            
        self.current_data = updated_data
        self.data_changed.emit(self.current_data)
        
        if self.save_target_file_path:
            try:
                # Ensure the directory exists before saving
                save_dir = os.path.dirname(self.save_target_file_path)
                if save_dir and not os.path.exists(save_dir):
                    os.makedirs(save_dir, exist_ok=True)
                    
                with open(self.save_target_file_path, 'w', encoding='utf-8') as f:
                    # Determine file format by extension
                    if self.save_target_file_path.endswith(('.yml', '.yaml')):
                        yaml.dump(self.current_data, f, allow_unicode=True, default_flow_style=False, indent=2)
                    else:
                        json.dump(self.current_data, f, ensure_ascii=False, indent=4)
                # QMessageBox.information(self, "保存", f"更改已保存到 {os.path.basename(self.save_target_file_path)}。") # Removed intrusive message
                return True  # 保存成功
            except Exception as e:
                file_format = "YAML" if self.save_target_file_path.endswith(('.yml', '.yaml')) else "JSON"
                QMessageBox.warning(self, "错误", f"保存{file_format}文件失败: {e}")
                return False  # 保存失败
        # else: # Removed message for unsaved changes in memory
            # QMessageBox.information(self, "保存", "更改已保存到内存中，但未指定保存文件。")
        return True  # 内存保存成功

    def get_data(self):
        # Ensure data is up-to-date before returning
        self.save_changes() 
        return self.current_data

    def set_save_target(self, file_path):
        self.save_target_file_path = file_path

    def show_table(self):
        # 只显示表格，不进行清理
        # 清理逻辑已经在load_data方法中处理
        self.table_widget.show()



    def _handle_add_option_request(self, key, new_option):
        if key in self.task_item_options and isinstance(self.task_item_options[key], list):
            if new_option not in self.task_item_options[key]:
                self.task_item_options[key].append(new_option)
                # Sort the options for consistency
                self.task_item_options[key].sort()
                QMessageBox.information(self, "添加成功", f"'{new_option}' 已添加到 '{key}' 的选项中。")
                
                # Update the constraint configuration file
                self._update_constraint_file(key, new_option)
                
                # 彻底清理表格，避免残留
                # 1. 关闭所有活动的编辑器
                for row in range(self.table_widget.rowCount()):
                    for col in range(self.table_widget.columnCount()):
                        item = self.table_widget.item(row, col)
                        if item:
                            self.table_widget.closePersistentEditor(item)
                
                # 2. 移除所有单元格部件
                for row in range(self.table_widget.rowCount()):
                    for col in range(self.table_widget.columnCount()):
                        widget = self.table_widget.cellWidget(row, col)
                        if widget:
                            widget.setParent(None)
                            widget.deleteLater()
                            self.table_widget.removeCellWidget(row, col)
                
                # 3. 清除所有表格项
                self.table_widget.clearContents()
                
                # 4. 清除所有行
                self.table_widget.setRowCount(0)
                
                # 5. 重置表格选择和当前单元格
                self.table_widget.setCurrentCell(-1, -1)
                self.table_widget.clearSelection()
                
                # 6. 强制刷新视图
                self.table_widget.viewport().update()
                self.table_widget.update()
                
                # 7. 重置表格样式
                self.table_widget.setStyleSheet("")
                
                # Refresh the table to update the QComboBoxes with the new option
                self.load_data(self.get_data())
            else:
                QMessageBox.information(self, "已存在", f"'{new_option}' 已在 '{key}' 的选项中。")
        else:
            QMessageBox.warning(self, "错误", f"无法为 '{key}' 添加选项，因为它没有预定义的选项列表。") # Reload current data to update combo boxes
    
    def _update_constraint_file(self, field_name, new_option):
        """更新约束配置文件中的选项"""
        if field_name in constraint_config.constraints:
            constraint = constraint_config.constraints[field_name]
            if hasattr(constraint, 'options') and constraint.options:
                if new_option not in constraint.options:
                    constraint.options.append(new_option)
                    
                    # 保存更新后的约束配置
                    cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")
                    constraint_file_path = os.path.join(cache_dir, "field_constraints.yaml")
                    if not constraint_config.save_to_file(constraint_file_path):
                        QMessageBox.warning(self, "错误", f"保存约束配置失败: 无法写入文件 {constraint_file_path}")
