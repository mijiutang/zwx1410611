from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QHBoxLayout, QDialogButtonBox, QGridLayout, QGroupBox
from PyQt6.QtCore import Qt

class FilterDialog(QDialog):
    def __init__(self, all_keys, selected_keys=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("筛选显示键")
        self.all_keys = all_keys
        self.selected_keys = selected_keys if selected_keys is not None else []
        self.checkboxes = {}

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # "Displayed" Group Box
        displayed_group_box = QGroupBox("已显示")
        displayed_layout = QGridLayout()
        displayed_group_box.setLayout(displayed_layout)
        
        # "Not Displayed" Group Box
        not_displayed_group_box = QGroupBox("未显示")
        not_displayed_layout = QGridLayout()
        not_displayed_group_box.setLayout(not_displayed_layout)

        row_displayed = 0
        col_displayed = 0
        row_not_displayed = 0
        col_not_displayed = 0
        num_columns = 3

        for key in self.all_keys: # Iterate through all_keys to maintain order
            checkbox = QCheckBox(key)
            self.checkboxes[key] = checkbox

            if key in self.selected_keys:
                checkbox.setChecked(True)
                displayed_layout.addWidget(checkbox, row_displayed, col_displayed)
                col_displayed += 1
                if col_displayed >= num_columns:
                    col_displayed = 0
                    row_displayed += 1
            else:
                checkbox.setChecked(False)
                not_displayed_layout.addWidget(checkbox, row_not_displayed, col_not_displayed)
                col_not_displayed += 1
                if col_not_displayed >= num_columns:
                    col_not_displayed = 0
                    row_not_displayed += 1
        
        main_layout.addWidget(displayed_group_box)
        main_layout.addWidget(not_displayed_group_box)

        # OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def get_selected_keys(self):
        return [key for key, checkbox in self.checkboxes.items() if checkbox.isChecked()]