from PyQt5.QtWidgets import QStyledItemDelegate, QComboBox, QMessageBox, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal

class ComboBoxDelegate(QStyledItemDelegate):
    # 定义添加选项请求信号
    add_option_requested = pyqtSignal(str, str)
    
    def __init__(self, parent=None, task_item_options=None):
        super().__init__(parent)
        self.task_item_options = task_item_options if task_item_options is not None else {}

    def createEditor(self, parent, option, index):
        # 获取当前单元格对应的键
        key_index = index.sibling(index.row(), 0)
        key = key_index.data(Qt.DisplayRole)

        # 如果键有预定义选项列表且不为空，则创建可编辑的下拉框
        if key in self.task_item_options and isinstance(self.task_item_options[key], list) and self.task_item_options[key]:
            editor = QComboBox(parent)
            editor.addItems(self.task_item_options[key])
            editor.setEditable(True)
            return editor
        # 否则使用默认编辑器
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        # 为下拉框编辑器设置当前值
        if isinstance(editor, QComboBox):
            value = index.model().data(index, Qt.DisplayRole)
            editor.setCurrentText(str(value))
        else:
            super().setEditorData(editor, index)

    def _handle_value_mismatch(self, model, index, key, new_value):
        """处理值不匹配的情况，显示消息框并根据用户选择执行相应操作"""
        msg_box = QMessageBox()
        msg_box.setWindowTitle("值不匹配提醒")
        msg_box.setText(f"'{new_value}' 不在 '{key}' 的预定义选项中。")
        msg_box.setInformativeText("您希望如何处理？")
        
        yes_button = msg_box.addButton("是 (保留)", QMessageBox.YesRole)
        no_button = msg_box.addButton("否 (清空)", QMessageBox.NoRole)
        add_button = msg_box.addButton("添加到下拉框", QMessageBox.AcceptRole)

        msg_box.exec_()

        if msg_box.clickedButton() == yes_button:
            model.setData(index, new_value, Qt.EditRole)
        elif msg_box.clickedButton() == no_button:
            model.setData(index, "", Qt.EditRole)
        elif msg_box.clickedButton() == add_button:
            self.add_option_requested.emit(key, new_value)
            model.setData(index, new_value, Qt.EditRole)

    def setModelData(self, editor, model, index):
        # 获取键信息
        key_index = index.sibling(index.row(), 0)
        key = key_index.data(Qt.DisplayRole)
        
        # 根据编辑器类型获取新值
        if isinstance(editor, QComboBox):
            new_value = editor.currentText()
        else:
            # 假设是类似QLineEdit的文本编辑器
            new_value = editor.text()

        # 检查是否需要进行值验证
        has_predefined_options = (key in self.task_item_options and 
                                isinstance(self.task_item_options[key], list) and 
                                self.task_item_options[key])
        
        if has_predefined_options:
            # 如果有预定义选项且新值不在其中，则调用处理函数
            if new_value not in self.task_item_options[key]:
                self._handle_value_mismatch(model, index, key, new_value)
            else:
                # 值在预定义选项中，直接设置
                model.setData(index, new_value, Qt.EditRole)
        else:
            # 没有预定义选项，直接设置值
            model.setData(index, new_value, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        # 设置编辑器的几何位置
        editor.setGeometry(option.rect)
