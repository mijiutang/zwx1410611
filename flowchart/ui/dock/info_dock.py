from PyQt6.QtWidgets import QDockWidget, QTextEdit
from PyQt6.QtCore import Qt

class InfoDock(QDockWidget):
    def __init__(self, title, initial_parsed_data, parent=None):
        super().__init__(title, parent)
        self.parsed_data = initial_parsed_data
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.setWidget(self.text_edit)
        self.highlight_enabled = False # New attribute to control highlighting
        self.update_content() # Display all content initially

    def set_highlight_enabled(self, enabled):
        self.highlight_enabled = enabled

    def _format_data_for_display(self, data, filtered_keys=None):
        """Formats the dictionary data into a readable string with highlighted keys, applying filters if provided."""
        if not data:
            return "<p>No data available.</p>"

        display_text = []
        keys_to_display = filtered_keys if filtered_keys is not None else data.keys()

        for key in keys_to_display:
            if key in data:
                value = data[key]
                if self.highlight_enabled: # Apply highlighting if enabled
                    display_text.append(f"<p><strong style='color: #2c3e50; background-color: pink;'>{key}:</strong> {value}</p>")
                else:
                    display_text.append(f"<p><strong>{key}:</strong> {value}</p>")
        return "\n".join(display_text)

    def update_content(self, filtered_keys=None):
        """Updates the QTextEdit with filtered content using HTML formatting."""
        # 检查是否有自定义格式化文本
        if hasattr(self, 'custom_formatted_text'):
            # 应用高亮格式到自定义文本
            custom_text = self.custom_formatted_text
            if self.highlight_enabled:
                # 对自定义文本中的键名应用高亮格式
                # 使用正则表达式匹配HTML段落中的键名模式（假设格式为"<p>键名:"）
                import re
                # 使用全局替换，确保所有匹配的键都被高亮
                # 匹配所有<p>标签后跟着非冒号字符直到冒号的内容，包括空行后的键
                custom_text = re.sub(r'<p>([^:<>\s][^:<>*]*):', 
                                     r'<p><strong style="color: #2c3e50; background-color: pink;">\1:</strong>', 
                                     custom_text)
            self.text_edit.setHtml(custom_text)
            # 显示后清理自定义文本，以便下次更新正常工作
            delattr(self, 'custom_formatted_text')
        else:
            formatted_text = self._format_data_for_display(self.parsed_data, filtered_keys)
            self.text_edit.setHtml(formatted_text)