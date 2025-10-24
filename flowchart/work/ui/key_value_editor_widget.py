from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QAbstractItemView, QMessageBox, QComboBox, QHeaderView
from PyQt5.QtCore import pyqtSignal, Qt
from ui.dock.combo_box_delegate import ComboBoxDelegate # Import the new delegate
import os
import json

class KeyValueEditorWidget(QWidget):
    data_changed = pyqtSignal(dict)

    def __init__(self, initial_data=None, task_items_file_path=None, parent=None):
        super().__init__(parent)
        self.current_data = initial_data if initial_data is not None else {}
        self.task_items_file_path = task_items_file_path
        self.task_item_options = {} # Stores options for each task item
        self.save_target_file_path = None # New attribute to store the target file for saving
        self.init_ui()
        
        # Load initial task items if path is provided
        if self.task_items_file_path:
            self._load_task_items_from_file()
        
        # Set the custom delegate for the "内容" column (column 1) AFTER task_item_options is loaded
        self.combo_box_delegate = ComboBoxDelegate(self, self.task_item_options)
        self.table_widget.setItemDelegateForColumn(1, self.combo_box_delegate)
        self.combo_box_delegate.add_option_requested.connect(self._handle_add_option_request) # Connect the new signal

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["任务项", "内容"])
        # Auto-resize columns
        self.table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents) # Key column
        self.table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch) # Value column
        # Auto-adjust row height for word wrap
        self.table_widget.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_widget.setWordWrap(True) # Re-enable word wrap for the table
        self.table_widget.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.AnyKeyPressed)
        self.table_widget.itemChanged.connect(self.save_changes) # Connect itemChanged for auto-save
        self.main_layout.addWidget(self.table_widget)
        self.table_widget.hide() # Hide initially

        self.load_data(self.current_data)

        control_layout = QHBoxLayout()
        
        self.main_layout.addLayout(control_layout)

    def _load_task_items_from_file(self):
        try:
            with open(self.task_items_file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                if isinstance(json_data, dict):
                    self.task_item_options = json_data
                    for task_item, options in self.task_item_options.items():
                        row_position = self.table_widget.rowCount()
                        self.table_widget.insertRow(row_position)
                        self.table_widget.setItem(row_position, 0, QTableWidgetItem(task_item))
                        
                        if isinstance(options, list) and options:
                            combo_box = QComboBox()
                            combo_box.addItems(options)
                            combo_box.setEditable(True)
                            combo_box.currentTextChanged.connect(self.save_changes) # Connect for auto-save
                            self.table_widget.setCellWidget(row_position, 1, combo_box)
                        else:
                            self.table_widget.setItem(row_position, 1, QTableWidgetItem(""))
                else:
                    QMessageBox.warning(self, "错误", "任务项文件格式不正确，应为JSON对象。")
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "错误", f"解析任务项JSON文件失败: {e}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载任务项文件失败: {e}")

    def load_data(self, data):
        # 断开信号，防止在加载数据时触发保存
        self.table_widget.itemChanged.disconnect(self.save_changes) 
        
        self.table_widget.setRowCount(0) # Clear existing rows
        self.current_data = data
        for key, value in self.current_data.items():
            row_position = self.table_widget.rowCount()
            self.table_widget.insertRow(row_position)
            key_item = QTableWidgetItem(key)
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable) # Make key column non-editable
            self.table_widget.setItem(row_position, 0, key_item)
            
            # Always create a QTableWidgetItem for the value column
            item = QTableWidgetItem(str(value))
            item.setFlags(item.flags() | Qt.TextWordWrap) # Enable word wrap
            self.table_widget.setItem(row_position, 1, item)

        # 重新连接信号
        self.table_widget.itemChanged.connect(self.save_changes)

    def save_changes(self):
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
            
        self.current_data = updated_data
        self.data_changed.emit(self.current_data)
        
        if self.save_target_file_path:
            try:
                with open(self.save_target_file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_data, f, ensure_ascii=False, indent=4)
                # QMessageBox.information(self, "保存", f"更改已保存到 {os.path.basename(self.save_target_file_path)}。") # Removed intrusive message
            except Exception as e:
                QMessageBox.warning(self, "错误", f"保存文件失败: {e}")
        # else: # Removed message for unsaved changes in memory
            # QMessageBox.information(self, "保存", "更改已保存到内存中，但未指定保存文件。")

    def get_data(self):
        # Ensure data is up-to-date before returning
        self.save_changes() 
        return self.current_data

    def set_save_target(self, file_path):
        self.save_target_file_path = file_path

    def show_table(self):
        self.table_widget.show()

    def set_task_items_file(self, file_path):
        self.task_items_file_path = file_path
        self._load_task_items_from_file()
        # Update the delegate's task_item_options
        self.combo_box_delegate.task_item_options = self.task_item_options
        # After loading new task items, refresh the table to reflect new combo box options
        self.load_data(self.get_data())

    def _handle_add_option_request(self, key, new_option):
        if key in self.task_item_options and isinstance(self.task_item_options[key], list):
            if new_option not in self.task_item_options[key]:
                self.task_item_options[key].append(new_option)
                # Sort the options for consistency
                self.task_item_options[key].sort()
                QMessageBox.information(self, "添加成功", f"'{new_option}' 已添加到 '{key}' 的选项中。")
                
                # Save the updated task_item_options to the current task file
                if self.task_items_file_path:
                    try:
                        with open(self.task_items_file_path, 'w', encoding='utf-8') as f:
                            json.dump(self.task_item_options, f, ensure_ascii=False, indent=4)
                    except Exception as e:
                        QMessageBox.warning(self, "保存失败", f"保存任务项文件失败: {e}")
                
                # Refresh the table to update the QComboBoxes with the new option
                self.load_data(self.get_data())
            else:
                QMessageBox.information(self, "已存在", f"'{new_option}' 已在 '{key}' 的选项中。")
        else:
            QMessageBox.warning(self, "错误", f"无法为 '{key}' 添加选项，因为它没有预定义的选项列表。") # Reload current data to update combo boxes