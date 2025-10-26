from PyQt6.QtWidgets import QMainWindow, QLabel, QDialog, QMessageBox, QMenu, QVBoxLayout, QHBoxLayout, QPushButton, QRadioButton, QButtonGroup, QSpinBox, QFontDialog, QApplication
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QSettings
import json
import os
import re
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
from .scenario_filter_dialog import ScenarioFilterDialog
from .dock.file_browser_dock import FileBrowserDock
from .key_value_editor_widget import KeyValueEditorWidget

class MainWindow(QMainWindow):
    def __init__(self, root_dir):
        super().__init__()
        self.highlight_enabled = False # Initialize highlight state
        self.root_dir = root_dir
        self.setWindowTitle("PyQt6 App")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize parsed_data as empty, data will be loaded on file double-click
        self.parsed_data = {}

        # Setup cache directory
        self.CACHE_DIR = os.path.join(self.root_dir, '.cache')
        self.KEYS_CACHE_FILE = os.path.join(self.CACHE_DIR, "keys.json")
        os.makedirs(self.CACHE_DIR, exist_ok=True)

        # Load cached keys and selected state
        cached_data = {"all_keys": [], "selected_keys": []}
        if os.path.exists(self.KEYS_CACHE_FILE):
            try:
                with open(self.KEYS_CACHE_FILE, 'r', encoding='utf-8') as f:
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
        # 不再需要连接data_changed信号，因为KeyValueEditorWidget自行管理数据
        self.setCentralWidget(self.key_value_editor)

        # Create a menu bar
        menubar = self.menuBar()

        # Import and create the custom dock widget
        from .dock.info_dock import InfoDock
        self.my_dock_widget = InfoDock("信号", self.parsed_data, self) # Pass empty parsed_data initially
        self.my_dock_widget.setObjectName("MyDockWidget") # Set a unique object name
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.my_dock_widget)
        
        # Create the上文信号dock widget
        self.previous_context_dock_widget = InfoDock("上文信号", {}, self) # Pass empty data initially
        self.previous_context_dock_widget.setObjectName("PreviousContextDockWidget")
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.previous_context_dock_widget)
        
        # Create the对话记录dock widget
        self.conversation_dock_widget = InfoDock("对话记录", {}, self) # Pass empty data initially
        self.conversation_dock_widget.setObjectName("ConversationDockWidget")
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.conversation_dock_widget)

        # Create and add the FileBrowserDock with the specified directory pointing to out folder
        target_file_dir = os.path.join(self.root_dir, 'out')
        self.file_browser_dock = FileBrowserDock("文件浏览器", target_file_dir, self)
        self.file_browser_dock.setObjectName("FileBrowserDock")
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.file_browser_dock)
        # Connect the file_double_clicked signal
        self.file_browser_dock.file_double_clicked.connect(self._on_file_double_clicked_in_browser)
        # Connect the batch generate signal
        self.file_browser_dock.batch_generate_result_json.connect(self._on_batch_generate_result_json)

        # Add menus
        file_menu = menubar.addMenu("文件")
        
        # Add refresh action to file menu
        refresh_action = QAction("刷新文件浏览器", self)
        refresh_action.triggered.connect(self._refresh_file_browser)
        file_menu.addAction(refresh_action)
        
        view_menu = menubar.addMenu("视图")
        settings_menu = menubar.addMenu("设置")

        # 添加字体设置动作
        font_action = QAction("字体", self)
        font_action.triggered.connect(self.show_font_settings_dialog)
        settings_menu.addAction(font_action)

        # 添加筛选动作，直接打开场景筛选对话框
        filter_action = QAction("筛选", self)
        filter_action.triggered.connect(self.show_scenario_filter_dialog)
        settings_menu.addAction(filter_action)

        highlight_action = QAction("高亮", self)
        highlight_action.setCheckable(True)
        highlight_action.setChecked(self.highlight_enabled)
        highlight_action.triggered.connect(self._toggle_highlighting)
        settings_menu.addAction(highlight_action)

        task_type_submenu = settings_menu.addMenu("任务类型")
        self._populate_task_type_menu(task_type_submenu)

        # Actions for controlling dock visibility
        info_dock_toggle_action = QAction("显示/隐藏 信号面板", self)
        info_dock_toggle_action.setCheckable(True)
        info_dock_toggle_action.setChecked(False) # Initially hidden as requested
        info_dock_toggle_action.toggled.connect(self.my_dock_widget.setVisible)
        view_menu.addAction(info_dock_toggle_action)
        self.my_dock_widget.setVisible(False)
        
        # Action for上文信号dock visibility
        previous_context_dock_toggle_action = QAction("显示/隐藏 上文信号面板", self)
        previous_context_dock_toggle_action.setCheckable(True)
        previous_context_dock_toggle_action.setChecked(True) # Initially visible
        previous_context_dock_toggle_action.toggled.connect(self.previous_context_dock_widget.setVisible)
        view_menu.addAction(previous_context_dock_toggle_action)
        
        # Action for对话记录dock visibility
        conversation_dock_toggle_action = QAction("显示/隐藏 对话记录面板", self)
        conversation_dock_toggle_action.setCheckable(True)
        conversation_dock_toggle_action.setChecked(True) # Initially visible
        conversation_dock_toggle_action.toggled.connect(self.conversation_dock_widget.setVisible)
        view_menu.addAction(conversation_dock_toggle_action)

        file_browser_dock_toggle_action = QAction("显示/隐藏 文件浏览器", self)
        file_browser_dock_toggle_action.setCheckable(True)
        file_browser_dock_toggle_action.setChecked(True) # Initially visible
        file_browser_dock_toggle_action.toggled.connect(self.file_browser_dock.setVisible)
        view_menu.addAction(file_browser_dock_toggle_action)

        tools_menu = menubar.addMenu("工具")
        # 添加爬虫菜单项
        crawler_action = QAction("爬虫", self)
        crawler_action.triggered.connect(self.run_crawler)
        tools_menu.addAction(crawler_action)

        self.settings = QSettings("MyOrganization", "PyQtFlowchartApp")
        self.read_settings()

        # 注意：_update_parsed_data_from_editor方法已移除
    # 该方法原本只是接收来自KeyValueEditorWidget的通知但不执行任何操作
    # KeyValueEditorWidget管理自己的数据，不需要MainWindow进行额外处理

    def _on_file_double_clicked_in_browser(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.parsed_data = data
                
                # 检查是否包含"系统信号"字段，如果有则解析其内容
                if "系统信号" in data and isinstance(data["系统信号"], str):
                    system_signal_content = data["系统信号"]
                    parsed_system_signals = {}
                    
                    # 解析系统信号内容，将 {key:value} 格式的字符串转换为键值对
                    # 匹配 {key:value} 格式的内容，但排除聊天记录和通话记录
                    matches = re.finditer(r'\{([^}:]+):([^}]+)\}', system_signal_content)
                    for match in matches:
                        key = match.group(1).strip()
                        # 排除聊天记录和通话记录
                        if "聊天记录" not in key and "通话记录" not in key:
                            value = match.group(2).strip()
                            parsed_system_signals[key] = value
                    
                    # 使用解析后的系统信号作为dock窗口的数据
                    self.my_dock_widget.parsed_data = parsed_system_signals
                    self.all_keys = list(parsed_system_signals.keys())
                    self.current_selected_keys = list(parsed_system_signals.keys())
                else:
                    # 如果没有系统信号字段，则使用整个JSON数据
                    self.all_keys = list(data.keys())
                    self.current_selected_keys = list(data.keys()) # Select all keys by default for the new file
                    self.my_dock_widget.parsed_data = self.parsed_data
                
                # 更新dock窗口内容
                self.my_dock_widget.update_content(self.current_selected_keys)
                
                # 更新上文信号dock窗口
                previous_context_data = {}
                if "上文" in data:
                    previous_context_data["上文"] = data["上文"]
                    # 如果上文是字符串且包含{key:value}格式，尝试解析
                    if isinstance(data["上文"], str):
                        # 尝试解析{key:value}格式
                        matches = re.finditer(r'\{([^}:]+):([^}]+)\}', data["上文"])
                        for match in matches:
                            key = match.group(1).strip()
                            value = match.group(2).strip()
                            previous_context_data[key] = value
                
                self.previous_context_dock_widget.parsed_data = previous_context_data
                self.previous_context_dock_widget.update_content()
                
                # 更新对话记录dock窗口
                conversation_data = {}
                if "系统信号" in data and isinstance(data["系统信号"], str):
                    system_signal_content = data["系统信号"]
                    
                    # 提取聊天记录，保持原始键名
                    chat_pattern = r'\{(用户和商家或者骑手的聊天记录):\s*([^}]*)\}'
                    chat_match = re.search(chat_pattern, system_signal_content)
                    if chat_match:
                        # 为了确保显示时格式正确，我们先存储原始数据
                        conversation_data[chat_match.group(1)] = chat_match.group(2).strip()
                    
                    # 提取通话记录，保持原始键名
                    call_pattern = r'\{(用户和商家或者骑手的通话记录):\s*([^}]*)\}'
                    call_match = re.search(call_pattern, system_signal_content)
                    if call_match:
                        # 为了确保显示时格式正确，我们先存储原始数据
                        conversation_data[call_match.group(1)] = call_match.group(2).strip()
                    
                    # 为对话记录窗口创建一个自定义格式化的显示文本
                    if conversation_data:
                        formatted_lines = []
                        for key, value in conversation_data.items():
                            formatted_lines.append(f"{key}: {value}")
                            # 在每个键值对后添加两个空行（除了最后一个）
                            if key != list(conversation_data.keys())[-1]:
                                formatted_lines.append("")
                        
                        # 使用特殊的键来存储格式化后的文本
                        self.conversation_dock_widget.custom_formatted_text = "\n".join(formatted_lines)
                
                self.conversation_dock_widget.parsed_data = conversation_data
                self.conversation_dock_widget.update_content()

            # --- New logic for _result.json and KeyValueEditorWidget ---
            # Create result directory if it doesn't exist
            result_dir = os.path.join(os.path.dirname(file_path), "result")
            os.makedirs(result_dir, exist_ok=True)
            
            # Generate _result.json path in result directory
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            result_json_path = os.path.join(result_dir, base_name + "_result.json")
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
                should_create_result_json = True  # 修改这里，确保在文件不存在时也创建
            
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

    def _on_batch_generate_result_json(self, directory_path, task_type_file):
        """Handle batch generation of _result.json files for a directory"""
        # Create task type selection dialog
        task_type_file = self._show_task_type_selection_dialog()
        if not task_type_file:
            return  # User cancelled the dialog
            
        # Find all JSON files in the directory
        json_files = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.json') and not file.endswith('_result.json'):
                    json_files.append(os.path.join(root, file))
        
        if not json_files:
            QMessageBox.information(self, "信息", "在选定的目录中未找到JSON文件。")
            return
            
        # Process each JSON file
        generated_count = 0
        for file_path in json_files:
            try:
                # Create result directory if it doesn't exist
                result_dir = os.path.join(os.path.dirname(file_path), "result")
                os.makedirs(result_dir, exist_ok=True)
                
                # Generate _result.json path in result directory
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                result_json_path = os.path.join(result_dir, base_name + "_result.json")
                
                # Skip if _result.json already exists
                if os.path.exists(result_json_path):
                    continue
                
                # Load task items from selected task type file
                task_item_options = self._load_task_items_from_file(task_type_file)
                
                # Create initial data with keys from task items
                editor_initial_data = {key: "" for key in task_item_options.keys()}
                
                # Save _result.json file
                with open(result_json_path, 'w', encoding='utf-8') as f_result:
                    json.dump(editor_initial_data, f_result, ensure_ascii=False, indent=4)
                generated_count += 1
            except Exception as e:
                QMessageBox.warning(self, "警告", f"创建 {os.path.basename(result_json_path)} 时发生错误: {e}")
        
        QMessageBox.information(self, "完成", f"批量生成完成，共创建了 {generated_count} 个 _result.json 文件。")

    def _show_task_type_selection_dialog(self):
        """Show dialog to select task type file"""
        task_type_files = self._find_task_type_files()
        if not task_type_files:
            QMessageBox.warning(self, "错误", "未找到任何任务类型文件。")
            return None
            
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("选择任务类型")
        layout = QVBoxLayout()
        
        # Create radio buttons for each task type file
        button_group = QButtonGroup()
        radio_buttons = []
        
        for i, file_path in enumerate(task_type_files):
            file_name = os.path.basename(file_path)
            match = re.match(r"任务类型_(\d+)\.json", file_name)
            if match:
                display_name = match.group(1)
            else:
                display_name = file_name
                
            radio_button = QRadioButton(display_name)
            if file_path == self.current_task_type_file:
                radio_button.setChecked(True)
            button_group.addButton(radio_button, i)
            radio_buttons.append((radio_button, file_path))
            layout.addWidget(radio_button)
        
        # Add buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        # Connect buttons
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        # Show dialog and get result
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_button = button_group.checkedButton()
            if selected_button:
                for radio_button, file_path in radio_buttons:
                    if radio_button == selected_button:
                        return file_path
        return None

    def _load_task_items_from_file(self, file_path):
        """Load task items from a task type file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                if isinstance(json_data, dict):
                    return json_data
                else:
                    QMessageBox.warning(self, "错误", "任务项文件格式不正确，应为JSON对象。")
                    return {}
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "错误", f"解析任务项JSON文件失败: {e}")
            return {}
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载任务项文件失败: {e}")
            return {}

    def closeEvent(self, event):
        self.write_settings()
        # Save current all_keys and current_selected_keys to cache
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        data_to_save = {
            "all_keys": self.all_keys,
            "selected_keys": self.current_selected_keys
        }
        with open(self.KEYS_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        event.accept()

    def read_settings(self):
        self.restoreGeometry(self.settings.value("geometry", self.saveGeometry()))
        self.restoreState(self.settings.value("windowState", self.saveState()))
        
        # 读取字体设置
        font_size = self.settings.value("fontSize", defaultValue=10, type=int)
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)

        # 读取高亮设置
        self.highlight_enabled = self.settings.value("highlightEnabled", defaultValue=False, type=bool)

    def write_settings(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        
        # 保存字体设置
        current_font = self.font()
        self.settings.setValue("fontSize", current_font.pointSize())

        # 保存高亮设置
        self.settings.setValue("highlightEnabled", self.highlight_enabled)

    def _get_default_task_type_file(self):
        # Find all task type files and return the first one, or None
        task_type_files = self._find_task_type_files()
        if task_type_files:
            return task_type_files[0]
        return None

    def _find_task_type_files(self):
        # Find all files matching "任务类型_*.json" in CACHE_DIR
        files = []
        if not os.path.exists(self.CACHE_DIR):
            os.makedirs(self.CACHE_DIR) # Ensure CACHE_DIR exists
        for f in os.listdir(self.CACHE_DIR):
            if f.startswith("任务类型_") and f.endswith(".json"):
                files.append(os.path.join(self.CACHE_DIR, f))
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
    
    def _toggle_highlighting(self, checked):
        self.highlight_enabled = checked
        self.my_dock_widget.set_highlight_enabled(checked)
        self.previous_context_dock_widget.set_highlight_enabled(checked)
        self.conversation_dock_widget.set_highlight_enabled(checked)
        self.write_settings() # Save the new state immediately
        self.my_dock_widget.update_content(self.current_selected_keys)
        self.previous_context_dock_widget.update_content()
        self.conversation_dock_widget.update_content()

    def _refresh_file_browser(self):
        """刷新文件浏览器视图"""
        if hasattr(self, 'file_browser_dock'):
            self.file_browser_dock._refresh_view()

    def show_scenario_filter_dialog(self):
        dialog = ScenarioFilterDialog(self.all_keys, self.current_selected_keys, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.current_selected_keys = dialog.get_selected_keys()
            self.my_dock_widget.update_content(self.current_selected_keys)
    
    def show_font_settings_dialog(self):
        """显示字体设置对话框"""
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("字体设置")
        dialog.setFixedSize(300, 150)
        layout = QVBoxLayout()
        
        # 获取当前字体
        current_font = self.font()
        current_size = current_font.pointSize()
        
        # 添加标签和微调框
        size_layout = QHBoxLayout()
        size_label = QLabel("当前字体大小：")
        size_layout.addWidget(size_label)
        
        size_spinbox = QSpinBox()
        size_spinbox.setRange(6, 36)
        size_spinbox.setValue(current_size)
        size_spinbox.setSuffix(" px")
        size_layout.addWidget(size_spinbox)
        
        layout.addLayout(size_layout)
        
        # 添加当前字体信息
        font_info_label = QLabel(f"当前字体：{current_font.family()} - {current_size}px")
        font_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(font_info_label)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        # 连接信号
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        # 显示对话框
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 应用新的字体大小
            new_size = size_spinbox.value()
            new_font = current_font
            new_font.setPointSize(new_size)
            self.setFont(new_font)
            
            # 更新应用程序中的所有部件字体
            app = QApplication.instance()
            if app:
                font = app.font()
                font.setPointSize(new_size)
                app.setFont(font)
            
            # 保存设置
            self.write_settings()
            QMessageBox.information(self, "成功", f"字体大小已更改为 {new_size}px")



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

    def convert_txt_to_json(self):
        """转换TXT文件为JSON文件"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import subprocess
        import sys
        import os
        
        # 默认目录为out文件夹
        default_dir = os.path.join(self.root_dir, 'out')
        
        # 弹窗选择要处理的文件夹
        directory = QFileDialog.getExistingDirectory(self, "选择要处理的文件夹", default_dir)
        
        if directory:  # 如果用户选择了目录
            try:
                # 获取Python解释器路径
                python_exe = sys.executable
                converter_script = os.path.join(self.root_dir, 'tools', 'txt_to_json_converter.py')
                
                # 检查脚本文件是否存在
                if not os.path.exists(converter_script):
                    QMessageBox.critical(self, "错误", f"转换脚本不存在：{converter_script}")
                    return
                    
                # 构建命令
                cmd = [python_exe, converter_script, directory]
                
                # 执行转换脚本
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
                
                # 获取输出信息
                output_info = result.stdout if result.stdout else "转换完成"
                if result.stderr:
                    output_info += f"\n错误信息：{result.stderr}"
                
                if result.returncode == 0:
                    QMessageBox.information(self, "成功", f"转换完成！\n{output_info}")
                else:
                    QMessageBox.warning(self, "错误", f"转换失败！\n{output_info}")
                    
            except Exception as e:
                QMessageBox.critical(self, "错误", f"执行转换时发生错误：{str(e)}")

    def run_crawler(self):
        """运行爬虫脚本"""
        try:
            # 导入必要的模块
            import subprocess
            import sys
            import os
            
            # 获取Python解释器路径
            python_exe = sys.executable
            crawler_script = os.path.join(self.root_dir, 'tools', 'crawler.py')
            
            # 检查脚本文件是否存在
            if not os.path.exists(crawler_script):
                QMessageBox.critical(self, "错误", f"爬虫脚本不存在：{crawler_script}")
                return
                
            # 构建命令
            cmd = [python_exe, crawler_script]
            
            # 在新进程中运行爬虫脚本
            subprocess.Popen(cmd, shell=True)
            
            QMessageBox.information(self, "提示", "爬虫程序已启动，请查看新打开的窗口。")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动爬虫程序时发生错误：{str(e)}")
