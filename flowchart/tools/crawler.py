from playwright.sync_api import sync_playwright
import time
import json
import os
import re
from urllib.parse import unquote
from bs4 import BeautifulSoup
import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject

# Define the root directory for the crawler script
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class SignalEmitter(QObject):
    """信号发射器，用于在线程间安全传递消息"""
    new_text = pyqtSignal(str)

class ConsoleOutputRedirector:
    """自定义输出流，用于将print输出重定向到QTextEdit"""
    def __init__(self, text_edit):
        self.text_edit = text_edit
        self.buffer = []
        # 创建信号发射器
        self.emitter = SignalEmitter()
        # 连接信号到槽函数
        self.emitter.new_text.connect(self.append_text_safely)
    
    def write(self, message):
        # 将消息添加到缓冲区
        self.buffer.append(message)
        # 当遇到换行符时，发送信号
        if '\n' in message:
            content = ''.join(self.buffer)
            # 发送信号，而不是直接更新UI
            self.emitter.new_text.emit(content.strip())
            self.buffer = []
    
    def flush(self):
        pass
    
    def append_text_safely(self, text):
        """安全地向文本框添加内容（在GUI线程中执行）"""
        self.text_edit.append(text)

class CrawlerThread(QThread):
    """爬虫工作线程，在后台执行抓取任务"""
    finished = pyqtSignal(bool)
    progress = pyqtSignal(int)
    log_message = pyqtSignal(str)
    
    def __init__(self, url, batch_mode=False, start_index=1, end_index=1, thread_id=0, crawl_type="left", parent=None):
        super().__init__(parent)
        self.url = url
        self.batch_mode = batch_mode
        self.start_index = start_index
        self.end_index = end_index
        self.thread_id = thread_id
        self.crawl_type = crawl_type  # 新增：抓取类型，"left"或"right"
        self.total_urls = end_index - start_index + 1 if batch_mode else 1
        # 为每个线程创建独立的浏览器数据目录
        self.chrome_data_dir = os.path.join(ROOT_DIR, '.cache', 'chrome_data', f'thread_{thread_id}')
    
    def run(self):
        try:
            success = self.perform_crawling()
            self.finished.emit(success)
        except Exception as e:
            error_msg = f"线程 {self.thread_id} 执行出错: {e}"
            self.log_message.emit(error_msg)
            self.finished.emit(False)
    
    def perform_crawling(self):
        """执行抓取任务"""
        if not self.batch_mode:
            # 单个URL抓取
            self.log_message.emit(f"线程 {self.thread_id} 开始抓取URL: {self.url}")
            success = open_chrome_browser(
                url=self.url,
                force_login=False,
                save_html=False,
                save_target_contents=True,
                auto_close=True,  # 自动关闭浏览器
                chrome_data_dir=self.chrome_data_dir,  # 使用线程特定的数据目录
                crawl_type=self.crawl_type  # 传递抓取类型
            )
            self.progress.emit(100)
            return success
        else:
            # 批量抓取（单个线程处理的URL范围）
            all_success = True
            base_url = self.url
            completed_count = 0
            
            # 检查URL中是否已包含sessionIndex参数
            if 'sessionIndex=' in base_url:
                # 移除现有的sessionIndex参数
                base_url = re.sub(r'sessionIndex=[^&]*&?', '', base_url)
                # 移除可能的尾部&符号
                if base_url.endswith('&'):
                    base_url = base_url[:-1]
            
            # 确保URL末尾有合适的分隔符
            separator = '&' if '?' in base_url else '?'
            
            for index in range(self.start_index, self.end_index + 1):
                # 构建包含当前sessionIndex的URL
                batch_url = f"{base_url}{separator}sessionIndex={index}"
                self.log_message.emit(f"线程 {self.thread_id} 开始抓取第 {index} 个URL")
                
                # 执行抓取
                success = open_chrome_browser(
                    url=batch_url,
                    force_login=False,
                    save_html=False,
                    save_target_contents=True,
                    auto_close=True,  # 自动关闭浏览器
                    chrome_data_dir=self.chrome_data_dir,  # 使用线程特定的数据目录
                    crawl_type=self.crawl_type  # 传递抓取类型
                )
                
                completed_count += 1
                progress = int((completed_count / self.total_urls) * 100)
                self.progress.emit(progress)
                
                if not success:
                    all_success = False
                    self.log_message.emit(f"线程 {self.thread_id} 第 {index} 个URL抓取失败")
                else:
                    self.log_message.emit(f"线程 {self.thread_id} 第 {index} 个URL抓取成功")
            
            return all_success

def save_cookies(context, filename=os.path.join(ROOT_DIR, '.cache', 'cookies.json')):
    cookies = context.cookies()
    with open(filename, 'w') as f:
        json.dump(cookies, f, indent=2)
    print(f"Cookies已保存到 {filename}")

def load_cookies(context, filename=os.path.join(ROOT_DIR, '.cache', 'cookies.json')):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        print(f"已从 {filename} 加载cookies")
        return True
    return False

def extract_url_parameter(url, param_name, default_value="", decode=False):
    """从URL中提取指定的参数值
    
    Args:
        url: 要提取参数的URL
        param_name: 要提取的参数名称
        default_value: 如果参数不存在时返回的默认值
        decode: 是否对提取的值进行URL解码
        
    Returns:
        提取的参数值或默认值
    """
    try:
        # 构建正则表达式匹配参数
        pattern = f'{param_name}=([^&]+)'
        match = re.search(pattern, url)
        if match:
            value = match.group(1)
            # 如果需要解码，则执行URL解码
            if decode:
                value = unquote(value)
            return value
    except Exception as e:
        print(f"提取URL参数'{param_name}'失败: {e}")
    # 如果无法提取，返回默认值
    return default_value

# 为了保持向后兼容性，可以保留原来的函数接口
def extract_task_name(url):
    """从URL中提取taskName参数值"""
    return extract_url_parameter(url, 'taskName', "未命名任务", decode=True)

def extract_session_index(url):
    """从URL中提取sessionIndex参数值，如果没有则返回默认值1"""
    return extract_url_parameter(url, 'sessionIndex', "1")

def open_chrome_browser(
    url,
    force_login=False,
    save_html=False,
    save_target_contents=False,  # 提取div内部内容
    auto_close=False,  # 是否自动关闭浏览器
    chrome_data_dir=os.path.join(ROOT_DIR, '.cache', 'chrome_data'),  # 线程特定的浏览器数据目录
    crawl_type="left"  # 抓取类型："left"（左侧信号项）或"right"（右侧表单标签）
):
    try:
        with sync_playwright() as p:
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            # 创建浏览器数据目录
            os.makedirs(chrome_data_dir, exist_ok=True)
            browser = p.chromium.launch_persistent_context(
                user_data_dir=chrome_data_dir,
                executable_path=chrome_path,
                headless=False,
                viewport={"width": 1280, "height": 720}
            )
            page = browser.pages[0] if browser.pages else browser.new_page()
            
            if not force_login:
                load_cookies(browser)
            
            page.goto(url)
            time.sleep(3)  # 等待页面加载完全
            
            # 登录检测逻辑
            if force_login or "login" in page.url or page.query_selector('input[type="password"]'):
                print("检测到需要登录...")
                # 在GUI模式下，这里仍然需要用户手动登录
                # 但是我们不再阻塞程序执行
                print("请在浏览器中完成登录，程序将继续执行...")
                # 给用户一些时间进行登录
                time.sleep(10)
                save_cookies(browser)
            
            # 保存完整HTML（可选）
            if save_html:
                html_content = page.content()
                with open("full_page.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                print("完整页面HTML已保存到 full_page.html")
            
            # 提取目标内容（核心逻辑）
            if save_target_contents:
                # 从URL中提取taskName和sessionIndex
                task_name = extract_task_name(url)
                session_index = extract_session_index(url)
                
                # 创建输出目录
                output_dir = os.path.join(ROOT_DIR, 'out', task_name)
                if not os.path.exists(output_dir):
                    try:
                        os.makedirs(output_dir)
                        print(f"已创建文件夹: {output_dir}")
                    except Exception as e:
                        print(f"创建文件夹失败: {e}")
                        # 如果创建失败，使用当前目录作为备选
                        output_dir = os.getcwd()
                
                # 使用Playwright的API提取数据
                extracted_data = {}
                
                if crawl_type == "left":
                    # 提取左侧信号项结构
                    extracted_data["左侧信号项"] = {}
                    signal_items = page.query_selector_all('div.signal-item')
                    
                    for item in signal_items:
                        # 提取信号名称
                        signal_name_elem = item.query_selector('div.signal-item-name')
                        if signal_name_elem:
                            signal_name = signal_name_elem.text_content().strip()
                            
                            # 提取对应的值
                            signal_value_elem = item.query_selector('div.signal-item-value .hwt-highlights')
                            signal_value = ''
                            if signal_value_elem:
                                signal_value = signal_value_elem.text_content().strip()
                            
                            # 将信号名称和值添加到结果中
                            if signal_name and signal_name not in extracted_data["左侧信号项"]:
                                extracted_data["左侧信号项"][signal_name] = signal_value
                    
                    # 生成输出文件名 - 仅使用sessionIndex作为文件名
                    left_output_file = os.path.join(output_dir, f"{session_index}.json")
                    
                    # 保存左侧数据为JSON文件
                    with open(left_output_file, 'w', encoding='utf-8') as f:
                        json.dump(extracted_data.get("左侧信号项", {}), f, ensure_ascii=False, indent=4)
                    
                    # 保存URL到同目录的url.txt文件
                    url_file = os.path.join(output_dir, "url.txt")
                    with open(url_file, 'w', encoding='utf-8') as f:
                        f.write(page.url)
                    
                    # 统计并显示结果
                    signal_count = len(extracted_data.get("左侧信号项", {}))
                    print(f"\n抓取完成！")
                    print(f"共提取到 {signal_count} 个左侧信号项")
                    print(f"左侧信号项已保存到: {left_output_file}")
                    print(f"URL已保存到: {url_file}")
                else:
                    # 提取右侧表单标签
                    extracted_data["右侧表单标签"] = {}
                    
                    # 匹配class="query-item-right-annotation"的div元素
                    annotation_divs = page.query_selector_all('div.query-item-right-annotation')
                    for div in annotation_divs:
                        # 查找所有表单项
                        form_items = div.query_selector_all('form.label-metrics-item')
                        for form_item in form_items:
                            # 查找表单项的标签
                            label_elem = form_item.query_selector('label.mtd-form-item-label span[style*="color: rgb(22, 119, 255)"]')
                            if label_elem:
                                label_text = label_elem.text_content().strip()
                                if label_text:
                                    # 查找对应的输入框或选择框
                                    input_value = ""
                                    
                                    # 尝试获取输入框的值
                                    input_elem = form_item.query_selector('input.mtd-input')
                                    if input_elem:
                                        # 获取输入框的实际值，包括modelvalue属性
                                        input_value = input_elem.get_attribute('value') or input_elem.get_attribute('modelvalue') or ""
                                    
                                    # 如果没有输入框，尝试获取文本域的值
                                    if not input_value:
                                        textarea_elem = form_item.query_selector('textarea.mtd-textarea')
                                        if textarea_elem:
                                            # 获取文本域的实际内容
                                            input_value = textarea_elem.input_value() or textarea_elem.text_content().strip() or ""
                                    
                                    # 将标签和值添加到结果中
                                    extracted_data["右侧表单标签"][label_text] = input_value
                    
                    # 生成输出文件名 - 保存到与左侧相同的目录下的result子目录
                    # 创建result子目录
                    result_dir = os.path.join(output_dir, 'result')
                    os.makedirs(result_dir, exist_ok=True)
                    
                    # 命名规则改为：使用{sessionid}_result.json作为文件名，保存在result子目录中
                    right_output_file = os.path.join(result_dir, f"{session_index}_result.json")
                    
                    # 保存右侧数据为JSON文件
                    with open(right_output_file, 'w', encoding='utf-8') as f:
                        json.dump(extracted_data.get("右侧表单标签", {}), f, ensure_ascii=False, indent=4)
                    
                    # 保存URL到同目录的url.txt文件
                    url_file = os.path.join(result_dir, "url.txt")
                    with open(url_file, 'w', encoding='utf-8') as f:
                        f.write(url)
                    
                    # 统计并显示结果
                    label_count = len(extracted_data.get("右侧表单标签", {}))
                    print(f"\n抓取完成！")
                    print(f"共提取到 {label_count} 个右侧表单标签")
                    print(f"右侧表单标签已保存到: {right_output_file}")
                    print(f"URL已保存到: {url_file}")
            
            print(f"已打开: {url}")
            
            # 根据auto_close参数决定是否自动关闭浏览器
            if not auto_close:
                input("按回车键关闭浏览器...")
            
            save_cookies(browser)
            browser.close()
            return True
            
    except Exception as e:
        print(f"打开浏览器失败: {e}")
        return False

class MainWindow(QMainWindow):
    """主窗口类"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和大小
        self.setWindowTitle("网页内容抓取工具")
        self.setGeometry(100, 100, 800, 800)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # URL输入区域
        url_layout = QHBoxLayout()
        url_label = QLabel("目标URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入要抓取的网页URL")
        
        # 添加两个独立的抓取按钮
        self.crawl_left_button = QPushButton("爬取信息（左侧信号项）")
        self.crawl_left_button.clicked.connect(lambda: self.start_crawling(crawl_type="left"))
        
        self.crawl_right_button = QPushButton("爬取任务类型（右侧表单标签）")
        self.crawl_right_button.clicked.connect(lambda: self.start_crawling(crawl_type="right"))
        
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.crawl_left_button)
        url_layout.addWidget(self.crawl_right_button)
        
        # 批量抓取设置区域
        batch_layout = QHBoxLayout()
        self.batch_checkbox = QPushButton("启用批量抓取")
        self.batch_checkbox.setCheckable(True)
        self.batch_checkbox.setChecked(False)
        
        batch_layout.addWidget(self.batch_checkbox)
        batch_layout.addStretch()
        
        # 批量参数输入区域
        index_layout = QHBoxLayout()
        start_label = QLabel("起始索引:")
        self.start_index_input = QLineEdit()
        self.start_index_input.setPlaceholderText("1")
        self.start_index_input.setText("1")
        self.start_index_input.setEnabled(False)
        
        end_label = QLabel("结束索引:")
        self.end_index_input = QLineEdit()
        self.end_index_input.setPlaceholderText("50")
        self.end_index_input.setText("50")
        self.end_index_input.setEnabled(False)
        
        index_layout.addWidget(start_label)
        index_layout.addWidget(self.start_index_input)
        index_layout.addWidget(end_label)
        index_layout.addWidget(self.end_index_input)
        index_layout.addStretch()
        
        # 并行设置区域
        parallel_layout = QHBoxLayout()
        parallel_label = QLabel("并行线程数:")
        self.parallel_input = QLineEdit()
        self.parallel_input.setPlaceholderText("2")
        self.parallel_input.setText("2")
        self.parallel_input.setEnabled(False)
        
        # 添加并行抓取复选框
        self.parallel_checkbox = QPushButton("启用并行抓取")
        self.parallel_checkbox.setCheckable(True)
        self.parallel_checkbox.setChecked(False)
        self.parallel_checkbox.setEnabled(False)  # 只有在批量模式下才可启用
        
        parallel_layout.addWidget(parallel_label)
        parallel_layout.addWidget(self.parallel_input)
        parallel_layout.addWidget(self.parallel_checkbox)
        parallel_layout.addStretch()
        
        # 连接信号
        self.batch_checkbox.clicked.connect(self.toggle_batch_mode)
        self.parallel_checkbox.clicked.connect(self.toggle_parallel_mode)
        
        # 进度条区域
        self.progress_label = QLabel("总体进度: 0%")
        self.total_progress = QLabel("完成: 0/0")
        progress_info_layout = QHBoxLayout()
        progress_info_layout.addWidget(self.progress_label)
        progress_info_layout.addStretch()
        progress_info_layout.addWidget(self.total_progress)
        
        # 日志显示区域
        log_label = QLabel("操作日志:")
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        
        # 将布局添加到主布局
        main_layout.addLayout(url_layout)
        main_layout.addLayout(batch_layout)
        main_layout.addLayout(index_layout)
        main_layout.addLayout(parallel_layout)
        main_layout.addLayout(progress_info_layout)
        main_layout.addWidget(log_label)
        main_layout.addWidget(self.log_text)
        
        # 初始化线程管理变量
        self.threads = []
        self.active_threads = 0
        self.total_urls = 0
        self.completed_urls = 0
        
        # 重定向标准输出到日志文本框
        self.redirector = ConsoleOutputRedirector(self.log_text)
        sys.stdout = self.redirector
    
    def toggle_batch_mode(self):
        """切换批量抓取模式的启用状态"""
        batch_enabled = self.batch_checkbox.isChecked()
        self.start_index_input.setEnabled(batch_enabled)
        self.end_index_input.setEnabled(batch_enabled)
        self.parallel_checkbox.setEnabled(batch_enabled)
        
        # 如果关闭批量模式，同时关闭并行模式
        if not batch_enabled and self.parallel_checkbox.isChecked():
            self.parallel_checkbox.setChecked(False)
            self.toggle_parallel_mode()
        
        if batch_enabled:
            self.batch_checkbox.setText("禁用批量抓取")
        else:
            self.batch_checkbox.setText("启用批量抓取")
    
    def toggle_parallel_mode(self):
        """切换并行抓取模式的启用状态"""
        parallel_enabled = self.parallel_checkbox.isChecked()
        self.parallel_input.setEnabled(parallel_enabled)
        
        if parallel_enabled:
            self.parallel_checkbox.setText("禁用并行抓取")
        else:
            self.parallel_checkbox.setText("启用并行抓取")
    
    def start_crawling(self, crawl_type="left"):
        """开始抓取任务
        
        Args:
            crawl_type: 抓取类型，"left"表示爬取左侧信号项，"right"表示爬取右侧表单标签
        """
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "警告", "请输入URL")
            return
        
        # 禁用相应的按钮，防止重复点击
        if crawl_type == "left":
            self.crawl_left_button.setEnabled(False)
            self.crawl_left_button.setText("抓取中...")
        else:
            self.crawl_right_button.setEnabled(False)
            self.crawl_right_button.setText("抓取中...")
        
        # 清空日志
        self.log_text.clear()
        
        # 重置进度
        self.progress_label.setText("总体进度: 0%")
        self.total_progress.setText("完成: 0/0")
        self.completed_urls = 0
        self.threads = []
        
        # 检查是否启用批量模式（左侧和右侧都支持）
        if self.batch_checkbox.isChecked():
            # 获取起始和结束索引
            try:
                start_index = int(self.start_index_input.text().strip())
                end_index = int(self.end_index_input.text().strip())
                
                if start_index <= 0 or end_index < start_index:
                    QMessageBox.warning(self, "警告", "请输入有效的索引范围")
                    if crawl_type == "left":
                        self.crawl_left_button.setEnabled(True)
                        self.crawl_left_button.setText("爬取信息（左侧信号项）")
                    else:
                        self.crawl_right_button.setEnabled(True)
                        self.crawl_right_button.setText("爬取任务类型（右侧表单标签）")
                    return
                
                self.total_urls = end_index - start_index + 1
                print(f"开始批量抓取URL，sessionIndex范围: {start_index}-{end_index}")
                print(f"基础URL: {url}")
                print(f"URL总数: {self.total_urls}")
                print(f"抓取类型: {'左侧信号项' if crawl_type == 'left' else '右侧表单标签'}")
                
                # 检查是否启用并行模式
                if self.parallel_checkbox.isChecked():
                    try:
                        thread_count = int(self.parallel_input.text().strip())
                        if thread_count <= 0:
                            thread_count = 2
                        # 限制最大线程数，避免资源过度消耗
                        thread_count = min(thread_count, 10)
                        
                        print(f"启用并行抓取，线程数: {thread_count}")
                        
                        # 计算每个线程处理的URL数量
                        urls_per_thread = self.total_urls // thread_count
                        remainder = self.total_urls % thread_count
                        
                        # 创建并启动多个线程
                        for i in range(thread_count):
                            # 计算每个线程的URL范围
                            thread_start = start_index + i * urls_per_thread
                            # 分配余数到前几个线程
                            if i < remainder:
                                thread_end = thread_start + urls_per_thread
                            else:
                                thread_end = thread_start + urls_per_thread - 1
                            
                            # 确保最后一个线程处理到结束索引
                            if i == thread_count - 1:
                                thread_end = end_index
                            
                            # 只在线程有工作时创建
                            if thread_start <= thread_end:
                                print(f"创建线程 {i+1}，处理范围: {thread_start}-{thread_end}")
                                thread = CrawlerThread(
                                    url=url,
                                    batch_mode=True,
                                    start_index=thread_start,
                                    end_index=thread_end,
                                    thread_id=i+1,
                                    crawl_type=crawl_type
                                )
                                thread.finished.connect(lambda success, ct=crawl_type: self.on_thread_finished(success, ct))
                                thread.progress.connect(lambda progress, tid=i+1: self.on_thread_progress(progress, tid))
                                thread.log_message.connect(self.log_thread_message)
                                self.threads.append(thread)
                        
                        # 启动所有线程
                        self.active_threads = len(self.threads)
                        for thread in self.threads:
                            thread.start()
                        
                    except ValueError:
                        QMessageBox.warning(self, "警告", "请输入有效的线程数")
                        if crawl_type == "left":
                            self.crawl_left_button.setEnabled(True)
                            self.crawl_left_button.setText("爬取信息（左侧信号项）")
                        else:
                            self.crawl_right_button.setEnabled(True)
                            self.crawl_right_button.setText("爬取任务类型（右侧表单标签）")
                        return
                else:
                    # 单线程批量模式
                    print("使用单线程批量抓取")
                    self.crawler_thread = CrawlerThread(
                        url=url,
                        batch_mode=True,
                        start_index=start_index,
                        end_index=end_index,
                        thread_id=1,
                        crawl_type=crawl_type
                    )
                    self.crawler_thread.finished.connect(lambda success: self.on_crawling_finished(success, crawl_type))
                    self.crawler_thread.progress.connect(lambda progress: self.on_thread_progress(progress, 1))
                    self.crawler_thread.log_message.connect(self.log_thread_message)
                    self.crawler_thread.start()
            except ValueError:
                QMessageBox.warning(self, "警告", "请输入有效的数字索引")
                if crawl_type == "left":
                    self.crawl_left_button.setEnabled(True)
                    self.crawl_left_button.setText("爬取信息（左侧信号项）")
                else:
                    self.crawl_right_button.setEnabled(True)
                    self.crawl_right_button.setText("爬取任务类型（右侧表单标签）")
                return
        else:
            # 单URL模式
            self.total_urls = 1
            print(f"开始抓取URL: {url}")
            print(f"抓取类型: {'左侧信号项' if crawl_type == 'left' else '右侧表单标签'}")
            
            # 创建并启动爬虫线程（单URL模式）
            self.crawler_thread = CrawlerThread(url, thread_id=1, crawl_type=crawl_type)
            self.crawler_thread.finished.connect(lambda success: self.on_crawling_finished(success, crawl_type))
            self.crawler_thread.progress.connect(lambda progress: self.on_thread_progress(progress, 1))
            self.crawler_thread.log_message.connect(self.log_thread_message)
            self.crawler_thread.start()
    
    def log_thread_message(self, message):
        """记录线程消息到日志"""
        print(message)
    
    def on_thread_progress(self, progress, thread_id):
        """处理线程进度更新，更新总进度显示
        
        Args:
            progress: 当前线程的进度百分比 (0-100)
            thread_id: 线程ID，用于识别不同的线程
        """
        # 基本进度更新逻辑：简单打印进度信息
        print(f"线程 {thread_id} 进度: {progress}%")
        # 如果需要更复杂的进度计算（如多线程进度汇总），可以在这里扩展
        # 例如：self.update_overall_progress()
    
    def on_thread_finished(self, success, crawl_type="left"):
        """处理单个线程完成"""
        self.active_threads -= 1
        
        # 检查所有线程是否都已完成
        if self.active_threads == 0:
            # 所有线程完成
            print("\n所有线程执行完成！")
            
            # 恢复按钮状态
            if crawl_type == "left":
                self.crawl_left_button.setEnabled(True)
                self.crawl_left_button.setText("爬取信息（左侧信号项）")
            else:
                self.crawl_right_button.setEnabled(True)
                self.crawl_right_button.setText("爬取任务类型（右侧表单标签）")
            
            # 显示结果消息
            if crawl_type == "left":
                QMessageBox.information(self, "成功", "左侧信号项批量抓取任务完成！")
            else:
                QMessageBox.information(self, "成功", "右侧表单标签抓取任务完成！")
    
    def update_overall_progress(self):
        """更新总体进度显示"""
        self.completed_urls += 1
        progress_percent = int((self.completed_urls / self.total_urls) * 100)
        self.progress_label.setText(f"总体进度: {progress_percent}%")
        self.total_progress.setText(f"完成: {self.completed_urls}/{self.total_urls}")
    
    def on_crawling_finished(self, success, crawl_type="left"):
        """抓取完成后的回调（单线程模式）"""
        # 恢复按钮状态
        if crawl_type == "left":
            self.crawl_left_button.setEnabled(True)
            self.crawl_left_button.setText("爬取信息（左侧信号项）")
        else:
            self.crawl_right_button.setEnabled(True)
            self.crawl_right_button.setText("爬取任务类型（右侧表单标签）")
        
        # 更新进度为100%
        self.progress_label.setText("总体进度: 100%")
        self.total_progress.setText(f"完成: {self.total_urls}/{self.total_urls}")
        
        # 显示结果消息
        if success:
            print("抓取完成！")
            if crawl_type == "left":
                QMessageBox.information(self, "成功", "左侧信号项抓取完成！")
            else:
                QMessageBox.information(self, "成功", "右侧表单标签抓取完成！")
        else:
            print("抓取失败！")
            QMessageBox.critical(self, "失败", "抓取过程中出现错误！")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 恢复标准输出
        sys.stdout = sys.__stdout__
        event.accept()

if __name__ == "__main__":
    # 创建PyQt应用程序
    app = QApplication(sys.argv)
    # 设置应用程序样式
    app.setStyle('Fusion')
    # 创建主窗口
    window = MainWindow()
    # 显示主窗口
    window.show()
    # 运行应用程序
    sys.exit(app.exec())