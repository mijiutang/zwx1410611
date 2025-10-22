from PyQt5.QtWidgets import QMainWindow, QLabel, QAction, QDialog, QMessageBox, QFileDialog, QMenu
from PyQt5.QtCore import Qt, QSettings
import json
import os
import re
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
from ui.filter_dialog import FilterDialog
from ui.crawler_dialog import CrawlerDialog
from core.crawler import get_signal_data, parse_signal_content
from core.crawler_info import open_chrome_browser, SignalExtractor
from ui.dock.file_browser_dock import FileBrowserDock
from ui.key_value_editor_widget import KeyValueEditorWidget

# 使用相对路径设置缓存目录，避免权限问题
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, ".cache")
KEYS_CACHE_FILE = os.path.join(CACHE_DIR, "keys.json")
# FILE_SAVE_DIR is now dynamic, removed global constant

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 App")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize parsed_data as empty, data will be loaded on file double-click
        self.parsed_data = {}

        # Load cached keys and selected state
        os.makedirs(CACHE_DIR, exist_ok=True)
        cached_data = {"all_keys": [], "selected_keys": []}
        if os.path.exists(KEYS_CACHE_FILE):
            try:
                with open(KEYS_CACHE_FILE, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    if isinstance(loaded_data, dict) and "all_keys" in loaded_data and "selected_keys" in loaded_data:
                        cached_data = loaded_data
            except json.JSONDecodeError:
                pass # Handle corrupted cache file

        # Initialize all_keys and current_selected_keys
        self.all_keys = cached_data["all_keys"]
        self.current_selected_keys = cached_data["selected_keys"]

        self.current_task_type_file = self._get_default_task_type_file() # New method to determine default
        self.key_value_editor = KeyValueEditorWidget(initial_data={}, task_items_file_path=self.current_task_type_file)
        self.key_value_editor.data_changed.connect(self._update_parsed_data_from_editor)
        self.setCentralWidget(self.key_value_editor)

        # Create a menu bar
        menubar = self.menuBar()

        # Import and create the custom dock widget
        from ui.dock.info_dock import InfoDock
        self.my_dock_widget = InfoDock("信号", self.parsed_data, self) # Pass empty parsed_data initially
        self.my_dock_widget.setObjectName("MyDockWidget") # Set a unique object name
        self.addDockWidget(Qt.LeftDockWidgetArea, self.my_dock_widget)

        # Create and add the FileBrowserDock with the specified directory
        target_file_dir = r"C:\Users\1\Desktop\workfast\zwx1410611\flowchart\file"
        self.file_browser_dock = FileBrowserDock("文件浏览器", target_file_dir, self)
        self.file_browser_dock.setObjectName("FileBrowserDock")
        self.addDockWidget(Qt.RightDockWidgetArea, self.file_browser_dock)
        # Connect the file_double_clicked signal
        self.file_browser_dock.file_double_clicked.connect(self._on_file_double_clicked_in_browser)

        # Add menus
        file_menu = menubar.addMenu("文件")
        view_menu = menubar.addMenu("视图")
        settings_menu = menubar.addMenu("设置") # New Settings menu

        filter_action = QAction("筛选", self)
        filter_action.triggered.connect(self.show_filter_dialog)
        settings_menu.addAction(filter_action)

        task_type_submenu = settings_menu.addMenu("任务类型")
        self._populate_task_type_menu(task_type_submenu)

        # Actions for controlling dock visibility
        info_dock_toggle_action = QAction("显示/隐藏 信号面板", self)
        info_dock_toggle_action.setCheckable(True)
        info_dock_toggle_action.setChecked(True) # Initially visible
        info_dock_toggle_action.toggled.connect(self.my_dock_widget.setVisible)
        view_menu.addAction(info_dock_toggle_action)

        file_browser_dock_toggle_action = QAction("显示/隐藏 文件浏览器", self)
        file_browser_dock_toggle_action.setCheckable(True)
        file_browser_dock_toggle_action.setChecked(True) # Initially visible
        file_browser_dock_toggle_action.toggled.connect(self.file_browser_dock.setVisible)
        view_menu.addAction(file_browser_dock_toggle_action)

        tools_menu = menubar.addMenu("工具")
        crawler_action = QAction("爬虫", self)
        crawler_action.triggered.connect(self.show_crawler_dialog)
        tools_menu.addAction(crawler_action)

        convert_txt_to_json_action = QAction("转换文本到JSON", self)
        convert_txt_to_json_action.triggered.connect(self._batch_convert_txt_to_json)
        tools_menu.addAction(convert_txt_to_json_action)

        self.settings = QSettings("MyOrganization", "PyQtFlowchartApp")
        self.read_settings()

    def _update_parsed_data_from_editor(self, updated_data):
        # This method is triggered by changes in KeyValueEditorWidget (i.e., _result.json data).
        # It should NOT update the MainWindow's main parsed_data or affect the InfoDock's display
        # of the original JSON file. The KeyValueEditorWidget manages its own data.
        pass # No action needed here for the MainWindow's main data or InfoDock.

    def _on_file_double_clicked_in_browser(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.parsed_data = data
                self.all_keys = list(data.keys())
                self.current_selected_keys = list(data.keys()) # Select all keys by default for the new file
                self.my_dock_widget.parsed_data = self.parsed_data
                self.my_dock_widget.update_content(self.current_selected_keys)

            # --- New logic for _result.json and KeyValueEditorWidget ---
            result_json_path = os.path.splitext(file_path)[0] + "_result.json"
            editor_initial_data = {}
            
            should_create_result_json = False

            if os.path.exists(result_json_path):
                try:
                    with open(result_json_path, 'r', encoding='utf-8') as f_result:
                        editor_initial_data = json.load(f_result)
                except json.JSONDecodeError:
                    QMessageBox.warning(self, "警告", f"无法解析 {os.path.basename(result_json_path)} 为JSON，将使用原始JSON的键并重新创建。")
                    editor_initial_data = {key: "" for key in self.key_value_editor.task_item_options.keys()} # Initialize with keys from task_item_options
                    should_create_result_json = True
                except Exception as e:
                    QMessageBox.warning(self, "警告", f"读取 {os.path.basename(result_json_path)} 时发生错误: {e}，将使用任务项的键并重新创建。")
                    editor_initial_data = {key: "" for key in self.key_value_editor.task_item_options.keys()} # Initialize with keys from task_item_options
                    should_create_result_json = True
            else:
                # If _result.json does not exist, initialize with keys from task_item_options and mark for creation
                editor_initial_data = {key: "" for key in self.key_value_editor.task_item_options.keys()}
            
            # If _result.json needs to be created or recreated, save it now
            if should_create_result_json:
                try:
                    with open(result_json_path, 'w', encoding='utf-8') as f_result:
                        json.dump(editor_initial_data, f_result, ensure_ascii=False, indent=4)
                except Exception as e:
                    QMessageBox.warning(self, "错误", f"创建/更新 {os.path.basename(result_json_path)} 失败: {e}")

            self.key_value_editor.load_data(editor_initial_data)
            self.key_value_editor.set_save_target(result_json_path)
            self.key_value_editor.show_table() # Show the table after loading data
            # --- End new logic ---

        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "错误", f"无法解析文件 {os.path.basename(file_path)} 为JSON: {e}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"读取文件 {os.path.basename(file_path)} 时发生错误: {e}")

    def closeEvent(self, event):
        self.write_settings()
        # Save current all_keys and current_selected_keys to cache
        os.makedirs(CACHE_DIR, exist_ok=True)
        data_to_save = {
            "all_keys": self.all_keys,
            "selected_keys": self.current_selected_keys
        }
        with open(KEYS_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        event.accept()

    def read_settings(self):
        self.restoreGeometry(self.settings.value("geometry", self.saveGeometry()))
        self.restoreState(self.settings.value("windowState", self.saveState()))

    def write_settings(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())

    def _get_default_task_type_file(self):
        # Find all task type files and return the first one, or None
        task_type_files = self._find_task_type_files()
        if task_type_files:
            return task_type_files[0]
        return None

    def _find_task_type_files(self):
        # Find all files matching "任务类型_*.json" in CACHE_DIR
        files = []
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR) # Ensure CACHE_DIR exists
        for f in os.listdir(CACHE_DIR):
            if f.startswith("任务类型_") and f.endswith(".json"):
                files.append(os.path.join(CACHE_DIR, f))
        files.sort() # Sort to ensure consistent order
        return files

    def _populate_task_type_menu(self, menu: QMenu):
        menu.clear() # Clear existing actions
        task_type_files = self._find_task_type_files()

        if not task_type_files:
            menu.addAction("无可用任务类型文件").setEnabled(False)
        else:
            for file_path in task_type_files:
                # Extract "1", "2" from "任务类型_1.json"
                file_name = os.path.basename(file_path)
                match = re.match(r"任务类型_(\d+)\.json", file_name)
                if match:
                    display_name = match.group(1)
                else:
                    display_name = file_name # Fallback if naming convention is not followed

                action = menu.addAction(display_name)
                action.setCheckable(True)
                action.setChecked(file_path == self.current_task_type_file)
                action.triggered.connect(lambda checked, path=file_path: self._set_current_task_type_file(path))

    def _set_current_task_type_file(self, file_path):
        if self.current_task_type_file != file_path:
            self.current_task_type_file = file_path
            self.key_value_editor.set_task_items_file(file_path) # New method in KeyValueEditorWidget
            QMessageBox.information(self, "任务类型", f"已切换到任务类型: {os.path.basename(file_path)}")

    def show_filter_dialog(self):
        dialog = FilterDialog(self.all_keys, self.current_selected_keys, self)
        if dialog.exec_() == QDialog.Accepted:
            self.current_selected_keys = dialog.get_selected_keys()
            self.my_dock_widget.update_content(self.current_selected_keys)

    def show_crawler_dialog(self):
        self.crawler_dialog = CrawlerDialog(self) # Store dialog as an attribute
        self.crawler_dialog.scrape_url_signal.connect(self.perform_scraping)
        self.crawler_dialog.exec_()

    def perform_scraping(self, base_url, start_index, end_index, cookie_string, output_folder, log_callback):
        log_callback(f"开始爬取，范围从 sessionIndex={start_index} 到 {end_index}。")
        all_scraped_data = {}
        browser, p = None, None

        # Extract URL prefix for subfolder name
        # Remove query parameters and fragment to get a cleaner base for folder name
        parsed_base_url = urlparse(base_url)
        # Remove the last part if it's a file name or just take the path
        path_segments = parsed_base_url.path.split('/')
        # Try to find a meaningful segment, otherwise use hostname
        if len(path_segments) > 1 and path_segments[-1]:
            url_prefix_raw = path_segments[-1]
        elif len(path_segments) > 2 and path_segments[-2]:
            url_prefix_raw = path_segments[-2]
        else:
            url_prefix_raw = parsed_base_url.hostname or "scraped_data"
        
        # Sanitize the prefix for a valid folder name
        sanitized_prefix = re.sub(r'[^a-zA-Z0-9_.-]', '_', url_prefix_raw)
        if not sanitized_prefix: # Fallback if sanitization results in empty string
            sanitized_prefix = "generic_scraped_data"

        target_save_dir = os.path.join(output_folder, sanitized_prefix)
        os.makedirs(target_save_dir, exist_ok=True)
        log_callback(f"抓取结果将保存到子文件夹: {target_save_dir}")

        try:
            for i in range(start_index, end_index + 1):
                current_url = f"{base_url}{i}"
                log_callback(f"正在打开浏览器并爬取: {current_url}\n请在浏览器中完成登录或等待页面加载。")
                
                page, browser, p = open_chrome_browser(current_url, log_callback=log_callback, cookie_string=cookie_string)
                if page:
                    extractor = SignalExtractor(page)
                    scraped_content = extractor.extract_signal_data()
                    
                    if scraped_content:
                        new_parsed_data = parse_signal_content(scraped_content)
                        all_scraped_data.update(new_parsed_data) # Merge data

                        # Extract sessionIndex from URL and save to file
                        parsed_current_url = urlparse(current_url)
                        query_params = parse_qs(parsed_current_url.query)
                        session_index = query_params.get('sessionIndex', [None])[0]

                        if session_index:
                            file_path = os.path.join(target_save_dir, f"{session_index}.json")
                            with open(file_path, 'w', encoding='utf-8') as f:
                                json.dump(new_parsed_data, f, ensure_ascii=False, indent=4)
                            log_callback(f"抓取结果已保存到: {file_path}")
                        else:
                            log_callback("警告: URL中未找到sessionIndex参数，无法保存到指定文件。")

                        log_callback(f"成功爬取 sessionIndex={i} 的数据。")
                    else:
                        log_callback(f"未能从 sessionIndex={i} 的指定元素中提取到信号数据。")
                else:
                    log_callback(f"未能成功打开浏览器或获取 sessionIndex={i} 的页面。")
                
                # Close browser and playwright after each iteration to ensure fresh state
                if browser:
                    browser.close()
                    browser = None # Reset browser to ensure new instance in next iteration
                if p:
                    p.stop()
                    p = None # Reset p to ensure new instance in next iteration

            # After all scraping is done, update main window's data
            if all_scraped_data:
                self.parsed_data.update(all_scraped_data) # Update main data with all new scraped data

                new_keys = list(self.parsed_data.keys())
                for key in new_keys:
                    if key not in self.all_keys:
                        self.all_keys.append(key)
                self.current_selected_keys = list(self.parsed_data.keys()) 

                self.my_dock_widget.parsed_data = self.parsed_data 
                self.my_dock_widget.update_content(self.current_selected_keys) 
                log_callback("所有信号数据已成功爬取并更新。")
                self.crawler_dialog.accept() # Close dialog on success
            else:
                log_callback("没有成功爬取到任何数据。")

        except Exception as e:
            log_callback(f"爬取过程中发生错误: {e}")
        finally:
            # Ensure browser and playwright are closed if an error occurred mid-loop
            if browser:
                browser.close()
            if p:
                p.stop()

    def _load_initial_data_from_files(self, directory):
        combined_data = {}
        os.makedirs(directory, exist_ok=True)
        for root, _, files in os.walk(directory):
            for filename in files:
                if filename.endswith(".json"):
                    file_path = os.path.join(root, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            combined_data.update(data) # Merge data, last one wins for duplicate keys
                    except json.JSONDecodeError as e:
                        print(f"警告: 无法解析文件 {filename} 为JSON: {e}")
                    except Exception as e:
                        print(f"读取文件 {filename} 时发生错误: {e}")
        return combined_data

    def _batch_convert_txt_to_json(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择包含TXT文件的文件夹")
        if not folder_path:
            return

        success_count = 0
        fail_count = 0
        failed_files = []

        for filename in os.listdir(folder_path):
            if filename.endswith(".txt"):
                txt_file_path = os.path.join(folder_path, filename)
                json_file_path = os.path.join(folder_path, os.path.splitext(filename)[0] + ".json")

                try:
                    with open(txt_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    parsed_data = parse_signal_content(content) # Use the existing parser
                    
                    with open(json_file_path, 'w', encoding='utf-8') as f:
                        json.dump(parsed_data, f, ensure_ascii=False, indent=4)
                    
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    failed_files.append(f"{filename}: {e}")
        
        result_message = f"转换完成！\n成功转换：{success_count} 个文件\n失败：{fail_count} 个文件"
        if failed_files:
            result_message += "\n\n失败文件详情：\n" + "\n".join(failed_files)
        
        QMessageBox.information(self, "批量转换结果", result_message)


