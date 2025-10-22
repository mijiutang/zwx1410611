import sys
import os
import threading
import time
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox, 
    QFileDialog, QCheckBox, QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QIcon

# 导入crawler_info.py中的功能
from crawler_info import SignalExtractor, open_chrome_browser

class WorkerSignals(QObject):
    """工作线程信号类"""
    log = pyqtSignal(str)
    finished = pyqtSignal(bool)
    signal_data = pyqtSignal(str)

class CrawlerWorker(threading.Thread):
    """爬虫工作线程"""
    def __init__(self, url, force_login=False, cookie_string=None):
        super().__init__()
        self.url = url
        self.force_login = force_login
        self.cookie_string = cookie_string
        self.signals = WorkerSignals()
        self.page = None
        self.browser = None
        self.playwright = None
        self._stop_event = threading.Event()
    
    def run(self):
        try:
            # 定义日志回调函数
            def log_callback(message):
                self.signals.log.emit(message)
            
            # 打开浏览器
            self.page, self.browser, self.playwright = open_chrome_browser(
                self.url, 
                force_login=self.force_login, 
                log_callback=log_callback,
                cookie_string=self.cookie_string
            )
            
            if self.page and not self._stop_event.is_set():
                self.signals.log.emit("浏览器已成功打开，开始提取信号数据...")
                
                # 提取信号数据
                extractor = SignalExtractor(self.page)
                signal_data = extractor.extract_signal_data()
                
                if signal_data:
                    self.signals.signal_data.emit(signal_data)
                    self.signals.log.emit("信号数据提取完成！")
                else:
                    self.signals.log.emit("未能提取到信号数据")
                
                self.signals.finished.emit(True)
            else:
                self.signals.log.emit("浏览器打开失败")
                self.signals.finished.emit(False)
                
        except Exception as e:
            self.signals.log.emit(f"发生错误: {str(e)}")
            self.signals.finished.emit(False)
    
    def stop(self):
        """停止爬虫并关闭浏览器"""
        self._stop_event.set()
        if self.browser:
            try:
                self.browser.close()
            except:
                pass
        if self.playwright:
            try:
                self.playwright.stop()
            except:
                pass

class CrawlerGUI(QMainWindow):
    """爬虫GUI主窗口"""
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和大小
        self.setWindowTitle("爬虫工具 - 信号数据提取")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # URL输入区域
        url_layout = QHBoxLayout()
        url_label = QLabel("目标URL:")
        url_label.setMinimumWidth(80)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入要爬取的网址")
        self.url_input.setText("https://aida-eval.sankuai.com/vue/model-training/labeling/data-labeling/task-labeling")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        main_layout.addLayout(url_layout)
        
        # Cookie自动加载（无需手动输入）
        cookie_note_layout = QHBoxLayout()
        cookie_note_label = QLabel("Cookie将自动从缓存文件加载")
        cookie_note_label.setStyleSheet("color: #666; font-style: italic;")
        cookie_note_layout.addWidget(cookie_note_label)
        cookie_note_layout.addStretch()
        main_layout.addLayout(cookie_note_layout)
        
        # 选项区域
        options_layout = QHBoxLayout()
        self.force_login_checkbox = QCheckBox("强制登录")
        self.force_login_checkbox.setToolTip("勾选此项将强制重新登录")
        options_layout.addWidget(self.force_login_checkbox)
        options_layout.addStretch()
        main_layout.addLayout(options_layout)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        self.start_button = QPushButton("开始爬取")
        self.start_button.setMinimumHeight(40)
        self.start_button.clicked.connect(self.start_crawling)
        
        self.stop_button = QPushButton("停止爬取")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_crawling)
        
        self.save_button = QPushButton("保存结果")
        self.save_button.setMinimumHeight(40)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_results)
        
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addWidget(self.save_button)
        main_layout.addLayout(buttons_layout)
        
        # 日志显示区域
        log_label = QLabel("操作日志:")
        main_layout.addWidget(log_label)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.WidgetWidth)
        self.log_text.setStyleSheet("background-color: #f5f5f5; color: #333;")
        main_layout.addWidget(self.log_text, 1)
        
        # 信号数据显示区域
        signal_label = QLabel("提取的信号数据:")
        main_layout.addWidget(signal_label)
        self.signal_text = QTextEdit()
        self.signal_text.setReadOnly(True)
        self.signal_text.setLineWrapMode(QTextEdit.WidgetWidth)
        main_layout.addWidget(self.signal_text, 2)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
    
    def log_message(self, message):
        """记录日志消息"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
        self.statusBar().showMessage(message)
    
    def start_crawling(self):
        """开始爬取任务"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "警告", "请输入目标URL")
            return
        
        # 禁用开始按钮，启用停止按钮
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.save_button.setEnabled(False)
        self.signal_text.clear()
        
        # 获取参数
        force_login = self.force_login_checkbox.isChecked()
        cookie_file_path = r"C:\Users\1\Desktop\workfast\zwx1410611\flowchart\work\.cache\cookies.json"
        
        # 读取cookie文件内容
        cookie_string = None
        if os.path.exists(cookie_file_path):
            try:
                with open(cookie_file_path, 'r', encoding='utf-8') as f:
                    cookies_data = json.load(f)
                    # 将cookies数据转换为name=value;格式的字符串
                    cookie_pairs = []
                    for cookie in cookies_data:
                        if 'name' in cookie and 'value' in cookie:
                            cookie_pairs.append(f"{cookie['name']}={cookie['value']}")
                    if cookie_pairs:
                        cookie_string = "; ".join(cookie_pairs)
                        self.log_message(f"已从 {cookie_file_path} 加载Cookie")
                    else:
                        self.log_message(f"Cookie文件 {cookie_file_path} 存在但内容为空")
            except Exception as e:
                self.log_message(f"读取Cookie文件失败: {str(e)}")
        else:
            self.log_message(f"警告: Cookie文件 {cookie_file_path} 不存在")
        
        # 创建并启动工作线程
        self.worker = CrawlerWorker(url, force_login, cookie_string)
        self.worker.signals.log.connect(self.log_message)
        self.worker.signals.finished.connect(self.crawling_finished)
        self.worker.signals.signal_data.connect(self.display_signal_data)
        self.worker.start()
        
        self.log_message("开始爬取任务...")
    
    def stop_crawling(self):
        """停止爬取任务"""
        if self.worker and self.worker.is_alive():
            self.log_message("正在停止爬取任务...")
            self.worker.stop()
            self.worker.join(timeout=5)
            self.log_message("爬取任务已停止")
            self.reset_ui_state()
    
    def crawling_finished(self, success):
        """爬取任务完成"""
        self.log_message(f"爬取任务{'成功' if success else '失败'}")
        self.reset_ui_state(finished=True)
    
    def display_signal_data(self, data):
        """显示提取的信号数据并自动保存"""
        self.signal_text.setPlainText(data)
        self.save_button.setEnabled(True)
        
        # 自动保存到默认路径
        if data.strip():
            default_path = "C:\\Users\\1\\Desktop\\workfast\\zwx1410611\\flowchart\\信号.txt"
            try:
                # 确保目录存在
                os.makedirs(os.path.dirname(default_path), exist_ok=True)
                with open(default_path, 'w', encoding='utf-8') as f:
                    f.write(data)
                self.log_message(f"=== 信号数据已自动保存到: {default_path} ===")
                self.log_message(f"输出路径: {default_path}")
            except Exception as e:
                self.log_message(f"自动保存失败: {str(e)}")
    
    def reset_ui_state(self, finished=False):
        """重置UI状态"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        if finished and self.signal_text.toPlainText().strip():
            self.save_button.setEnabled(True)
    
    def save_results(self):
        """保存提取的信号数据"""
        data = self.signal_text.toPlainText()
        if not data.strip():
            QMessageBox.warning(self, "警告", "没有可保存的数据")
            return
        
        # 默认保存路径
        default_path = "C:\\Users\\1\\Desktop\\workfast\\zwx1410611\\flowchart\\信号.txt"
        
        # 打开文件保存对话框
        filename, _ = QFileDialog.getSaveFileName(
            self, "保存信号数据", default_path, "文本文件 (*.txt);;所有文件 (*)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(data)
                self.log_message(f"=== 信号数据已手动保存到: {filename} ===")
                self.log_message(f"输出路径: {filename}")
                QMessageBox.information(self, "成功", "数据保存成功！")
            except Exception as e:
                self.log_message(f"保存失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"保存文件时出错: {str(e)}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.worker and self.worker.is_alive():
            reply = QMessageBox.question(
                self, "确认", "爬取任务正在进行中，确定要关闭窗口吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.stop_crawling()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

if __name__ == "__main__":
    # 确保中文正常显示
    os.environ["QT_FONT_DPI"] = "96"
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 设置全局字体
    font = QFont("SimHei", 9)
    app.setFont(font)
    
    # 创建并显示窗口
    window = CrawlerGUI()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())