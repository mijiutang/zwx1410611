from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QTextEdit, QCheckBox, QGridLayout, QFileDialog
from PyQt5.QtCore import pyqtSignal, Qt
import json
import os
import re
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode

# 使用相对路径设置缓存目录，避免权限问题
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, ".cache")
CRAWLER_SETTINGS_FILE = os.path.join(CACHE_DIR, "crawler_settings.json")

class CrawlerDialog(QDialog):
    # Modified to pass base_url, start_index, end_index, cookie_string, output_folder, log_callback
    scrape_url_signal = pyqtSignal(str, int, int, str, str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("爬取信号数据")
        self.setGeometry(200, 200, 700, 550) # Increased size

        self._init_ui()
        self._load_settings()
        self._update_range_inputs_state()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)

        # URL Input
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入要爬取的网址 (必须包含sessionIndex=数字)")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        main_layout.addLayout(url_layout)

        # Cookie Input
        cookie_layout = QHBoxLayout()
        cookie_label = QLabel("Cookie:")
        self.cookie_input = QLineEdit()
        self.cookie_input.setPlaceholderText("请输入Cookie字符串 (可选)")
        cookie_layout.addWidget(cookie_label)
        cookie_layout.addWidget(self.cookie_input)
        main_layout.addLayout(cookie_layout)

        # Output Folder Input
        output_folder_layout = QHBoxLayout()
        output_folder_label = QLabel("输出文件夹:")
        self.output_folder_input = QLineEdit()
        self.output_folder_input.setPlaceholderText("选择保存JSON文件的根文件夹")
        self.output_folder_button = QPushButton("选择")
        self.output_folder_button.clicked.connect(self._select_output_folder)
        output_folder_layout.addWidget(output_folder_label)
        output_folder_layout.addWidget(self.output_folder_input)
        output_folder_layout.addWidget(self.output_folder_button)
        main_layout.addLayout(output_folder_layout)

        # Session Index Range
        range_group_box = QGridLayout()
        self.enable_range_checkbox = QCheckBox("启用 sessionIndex 范围爬取")
        self.enable_range_checkbox.stateChanged.connect(self._update_range_inputs_state)
        range_group_box.addWidget(self.enable_range_checkbox, 0, 0, 1, 2)

        start_label = QLabel("起始 sessionIndex:")
        self.start_index_input = QLineEdit()
        self.start_index_input.setValidator(self.create_int_validator())
        range_group_box.addWidget(start_label, 1, 0)
        range_group_box.addWidget(self.start_index_input, 1, 1)

        end_label = QLabel("结束 sessionIndex:")
        self.end_index_input = QLineEdit()
        self.end_index_input.setValidator(self.create_int_validator())
        range_group_box.addWidget(end_label, 2, 0)
        range_group_box.addWidget(self.end_index_input, 2, 1)
        main_layout.addLayout(range_group_box)

        # Log Display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        main_layout.addWidget(self.log_display)

        # Buttons
        button_layout = QHBoxLayout()
        self.scrape_button = QPushButton("爬取")
        self.scrape_button.clicked.connect(self._on_scrape_clicked)
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.scrape_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

    def create_int_validator(self):
        from PyQt5.QtGui import QIntValidator
        return QIntValidator(0, 999999999, self) # Adjust range as needed

    def _update_range_inputs_state(self):
        enabled = self.enable_range_checkbox.isChecked()
        self.start_index_input.setEnabled(enabled)
        self.end_index_input.setEnabled(enabled)

    def _select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹", self.output_folder_input.text())
        if folder:
            self.output_folder_input.setText(folder)

    def _on_scrape_clicked(self):
        url = self.url_input.text()
        cookie_string = self.cookie_input.text()
        output_folder = self.output_folder_input.text()
        start_index = -1
        end_index = -1

        if not url:
            self.append_log("错误: URL不能为空。")
            return
        if not output_folder:
            self.append_log("错误: 输出文件夹不能为空。")
            return

        # Validate URL format for sessionIndex
        if "sessionIndex=" not in url:
            self.append_log("错误: URL必须包含 'sessionIndex=' 参数。")
            return
        
        # Check if URL ends with sessionIndex=digits
        match = re.search(r"sessionIndex=(\d+)$", url)
        if not match:
            self.append_log("错误: URL中的sessionIndex参数必须以数字结尾。")
            return
        
        base_url = url # Will be modified if range is enabled

        if self.enable_range_checkbox.isChecked():
            try:
                start_index = int(self.start_index_input.text())
                end_index = int(self.end_index_input.text())
                if start_index > end_index:
                    self.append_log("错误: 起始 sessionIndex 不能大于结束 sessionIndex。")
                    return
                
                # Construct base_url without sessionIndex for range scraping
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)
                if 'sessionIndex' in query_params:
                    del query_params['sessionIndex']
                
                # Reconstruct URL without sessionIndex
                parsed_url = parsed_url._replace(query=urlencode(query_params, doseq=True))
                base_url = urlunparse(parsed_url) + ("&" if parsed_url.query else "?") + "sessionIndex="

            except ValueError:
                self.append_log("错误: 起始和结束 sessionIndex 必须是有效的整数。")
                return
        else:
            # If range is not enabled, extract the single sessionIndex from the URL
            try:
                start_index = int(match.group(1))
                end_index = start_index
            except ValueError:
                self.append_log("错误: 无法从URL中解析单个sessionIndex。")
                return

        self._save_settings() # Save settings before emitting signal
        self.scrape_url_signal.emit(base_url, start_index, end_index, cookie_string, output_folder, self.append_log)

    def append_log(self, message):
        self.log_display.append(message)

    def _load_settings(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        if os.path.exists(CRAWLER_SETTINGS_FILE):
            try:
                with open(CRAWLER_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.url_input.setText(settings.get("last_url", ""))
                    self.cookie_input.setText(settings.get("last_cookie", ""))
                    self.output_folder_input.setText(settings.get("last_output_folder", ""))
                    self.enable_range_checkbox.setChecked(settings.get("enable_range", False))
                    self.start_index_input.setText(str(settings.get("last_start_index", "")))
                    self.end_index_input.setText(str(settings.get("last_end_index", "")))
            except json.JSONDecodeError:
                pass # Handle corrupted settings file

    def _save_settings(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        settings = {
            "last_url": self.url_input.text(),
            "last_cookie": self.cookie_input.text(),
            "last_output_folder": self.output_folder_input.text(),
            "enable_range": self.enable_range_checkbox.isChecked(),
            "last_start_index": self.start_index_input.text(),
            "last_end_index": self.end_index_input.text()
        }
        with open(CRAWLER_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
