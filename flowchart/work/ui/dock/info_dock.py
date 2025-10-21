from PyQt5.QtWidgets import QDockWidget, QTextEdit
from PyQt5.QtCore import Qt

class InfoDock(QDockWidget):
    def __init__(self, title, initial_parsed_data, parent=None):
        super().__init__(title, parent)
        self.parsed_data = initial_parsed_data
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.setWidget(self.text_edit)
        self.update_content() # Display all content initially

    def _format_data_for_display(self, data, filtered_keys=None):
        """Formats the dictionary data into a readable string, applying filters if provided."""
        if not data:
            return "No data available."

        display_text = []
        keys_to_display = filtered_keys if filtered_keys is not None else data.keys()

        for key in keys_to_display:
            if key in data:
                value = data[key]
                display_text.append(f"{key}: {value}")
        return "\n".join(display_text)

    def update_content(self, filtered_keys=None):
        """Updates the QTextEdit with filtered content."""
        formatted_text = self._format_data_for_display(self.parsed_data, filtered_keys)
        self.text_edit.setPlainText(formatted_text)
