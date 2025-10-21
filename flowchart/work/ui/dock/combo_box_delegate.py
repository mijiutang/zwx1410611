from PyQt5.QtWidgets import QStyledItemDelegate, QComboBox, QMessageBox, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal # Import pyqtSignal

class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, task_item_options=None):
        super().__init__(parent)
        self.task_item_options = task_item_options if task_item_options is not None else {}

    def createEditor(self, parent, option, index):
        key_index = index.sibling(index.row(), 0)
        key = key_index.data(Qt.DisplayRole)

        if key in self.task_item_options and isinstance(self.task_item_options[key], list) and self.task_item_options[key]:
            editor = QComboBox(parent)
            editor.addItems(self.task_item_options[key])
            editor.setEditable(True)
            return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if isinstance(editor, QComboBox):
            value = index.model().data(index, Qt.DisplayRole)
            editor.setCurrentText(str(value))
        else:
            super().setEditorData(editor, index)

    add_option_requested = pyqtSignal(str, str) # Signal to request adding a new option

    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox):
            new_value = editor.currentText()
            key_index = index.sibling(index.row(), 0)
            key = key_index.data(Qt.DisplayRole)

            if key in self.task_item_options and isinstance(self.task_item_options[key], list) and self.task_item_options[key]:
                # Check if new_value is in the predefined options
                if new_value not in self.task_item_options[key]:
                    msg_box = QMessageBox()
                    msg_box.setWindowTitle("值不匹配提醒")
                    msg_box.setText(f"'{new_value}' 不在 '{key}' 的预定义选项中。")
                    msg_box.setInformativeText("您希望如何处理？")
                    
                    yes_button = msg_box.addButton("是 (保留)", QMessageBox.YesRole)
                    no_button = msg_box.addButton("否 (清空)", QMessageBox.NoRole)
                    add_button = msg_box.addButton("添加到下拉框", QMessageBox.AcceptRole) # Using AcceptRole for custom action

                    msg_box.exec_()

                    if msg_box.clickedButton() == yes_button:
                        model.setData(index, new_value, Qt.EditRole)
                    elif msg_box.clickedButton() == no_button:
                        model.setData(index, "", Qt.EditRole)
                    elif msg_box.clickedButton() == add_button:
                        self.add_option_requested.emit(key, new_value)
                        model.setData(index, new_value, Qt.EditRole) # Set the value after emitting signal
                else:
                    model.setData(index, new_value, Qt.EditRole)
            else: # If no predefined options, or not a list, just set the value
                model.setData(index, new_value, Qt.EditRole)
        else:
            # For non-QComboBox editors (e.g., QLineEdit for plain text cells)
            new_value = editor.text() # Assuming editor is a QLineEdit or similar
            key_index = index.sibling(index.row(), 0)
            key = key_index.data(Qt.DisplayRole)

            if key in self.task_item_options and isinstance(self.task_item_options[key], list) and self.task_item_options[key]:
                if new_value not in self.task_item_options[key]:
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
                else:
                    model.setData(index, new_value, Qt.EditRole)
            else:
                model.setData(index, new_value, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
