from PyQt6.QtWidgets import QMainWindow, QLabel, QDialog, QMessageBox, QMenu, QVBoxLayout, QHBoxLayout, QPushButton, QRadioButton, QButtonGroup, QSpinBox, QFontDialog, QApplication
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QSettings
import json
import os
import re
import yaml
import collections
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
from .scenario_filter_dialog import ScenarioFilterDialog
from .dock.file_browser_dock import FileBrowserDock
from .key_value_editor_widget import KeyValueEditorWidget

class MainWindow(QMainWindow):
    def __init__(self, root_dir):
        super().__init__()
        self.highlight_enabled = True # Initialize highlight state as enabled by default
        self.root_dir = root_dir
        # 添加当前选中的约束文件路径属性
        self.current_constraint_file_path = None
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

        self.current_task_type_file = None # 不再使用任务类型文件
        self.key_value_editor = KeyValueEditorWidget(initial_data={})
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
        
        # 设置所有dock组件的高亮状态为默认开启
        self.my_dock_widget.set_highlight_enabled(self.highlight_enabled)
        self.previous_context_dock_widget.set_highlight_enabled(self.highlight_enabled)
        self.conversation_dock_widget.set_highlight_enabled(self.highlight_enabled)

        # Create and add the FileBrowserDock with the specified directory pointing to out folder
        target_file_dir = os.path.join(self.root_dir, 'out')
        self.file_browser_dock = FileBrowserDock("文件浏览器", target_file_dir, self)
        self.file_browser_dock.setObjectName("FileBrowserDock")
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.file_browser_dock)
        # Connect the file_double_clicked signal
        self.file_browser_dock.file_double_clicked.connect(self._on_file_double_clicked_in_browser)

        # Add menus
        file_menu = menubar.addMenu("文件")
        
        # Add refresh action to file menu
        refresh_action = QAction("刷新文件浏览器", self)
        refresh_action.triggered.connect(self._refresh_file_browser)
        file_menu.addAction(refresh_action)
        
        # 添加场景菜单
        self.scenario_menu = menubar.addMenu("场景")
        self._populate_scenario_menu(self.scenario_menu)
        
        view_menu = menubar.addMenu("视图")
        settings_menu = menubar.addMenu("设置")

        # 添加字体设置动作
        font_action = QAction("字体", self)
        font_action.triggered.connect(self.show_font_settings_dialog)
        settings_menu.addAction(font_action)

        highlight_action = QAction("高亮", self)
        highlight_action.setCheckable(True)
        highlight_action.setChecked(self.highlight_enabled)
        highlight_action.triggered.connect(self._toggle_highlighting)
        settings_menu.addAction(highlight_action)
        
        

        # 添加打开约束编辑器菜单项
        open_constraint_editor_action = QAction("打开约束编辑器", self)
        open_constraint_editor_action.triggered.connect(self.open_constraint_editor)
        settings_menu.addAction(open_constraint_editor_action)
        
          # 添加约束子菜单
        constraints_menu = menubar.addMenu("约束")
        self._populate_constraints_menu(constraints_menu)

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
        
        # 初始化场景菜单
        self._refresh_scenario_menu()

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
                            # 使用HTML格式，确保高亮能正确应用
                            formatted_lines.append(f"<p>{key}: {value}</p>")
                            # 在每个键值对后添加两个空行（除了最后一个）
                            if key != list(conversation_data.keys())[-1]:
                                formatted_lines.append("<p></p>")
                        
                        # 使用特殊的键来存储格式化后的文本
                        self.conversation_dock_widget.custom_formatted_text = "\n".join(formatted_lines)
                
                self.conversation_dock_widget.parsed_data = conversation_data
                self.conversation_dock_widget.update_content()

            # --- Logic for _result.json and KeyValueEditorWidget ---
            # Generate _result.json path in result directory
            result_dir = os.path.join(os.path.dirname(file_path), "result")
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            result_json_path = os.path.join(result_dir, base_name + "_result.json")
            editor_initial_data = {}
            
            # Only load data if the result file exists, don't create it automatically
            if os.path.exists(result_json_path):
                try:
                    with open(result_json_path, 'r', encoding='utf-8') as f_result:
                        editor_initial_data = json.load(f_result)
                except json.JSONDecodeError:
                    QMessageBox.warning(self, "警告", f"无法解析 {os.path.basename(result_json_path)} 为JSON，将显示空表格。")
                    editor_initial_data = {}
                except Exception as e:
                    QMessageBox.warning(self, "警告", f"读取 {os.path.basename(result_json_path)} 时发生错误: {e}，将显示空表格。")
                    editor_initial_data = {}
            # If _result.json does not exist, we don't create it automatically
            # The file will only be created when the user saves data

            self.key_value_editor.load_data(editor_initial_data)
            self.key_value_editor.set_save_target(result_json_path)
            self.key_value_editor.show_table() # Show the table after loading data
            # --- End logic ---

        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "错误", f"无法解析文件 {os.path.basename(file_path)} 为JSON: {e}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"读取文件 {os.path.basename(file_path)} 时发生错误: {e}")

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
        self.highlight_enabled = self.settings.value("highlightEnabled", defaultValue=True, type=bool)
        
        # 应用高亮设置到所有dock组件
        self.my_dock_widget.set_highlight_enabled(self.highlight_enabled)
        self.previous_context_dock_widget.set_highlight_enabled(self.highlight_enabled)
        self.conversation_dock_widget.set_highlight_enabled(self.highlight_enabled)

    def write_settings(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        
        # 保存字体设置
        current_font = self.font()
        self.settings.setValue("fontSize", current_font.pointSize())

        # 保存高亮设置
        self.settings.setValue("highlightEnabled", self.highlight_enabled)

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

    def _refresh_scenario_menu(self):
        """刷新场景菜单"""
        self._populate_scenario_menu(self.scenario_menu)
        
        # 确定当前选中的场景
        scenarios = self._load_scenarios()
        current_scenario_id = "global"  # 默认为全局场景
        
        # 检查当前选中的键值是否匹配某个特定场景
        for scenario_id, config in scenarios.items():
            if config.get("type") == "specific":
                selected_keys = set(config.get("selected_keys", []))
                current_keys = set(self.current_selected_keys)
                if selected_keys == current_keys:
                    current_scenario_id = scenario_id
                    break
        
        # 更新菜单项的选中状态
        actions = self.scenario_menu.actions()
        for action in actions:
            if action.isCheckable():
                action.setChecked(False)
        
        if current_scenario_id == "global":
            # 全局场景是第一个菜单项
            if actions and actions[0].isCheckable():
                actions[0].setChecked(True)
        else:
            # 查找对应的特定场景菜单项
            scenario_name = scenarios.get(current_scenario_id, {}).get("name", current_scenario_id.replace("specific_", ""))
            for action in actions:
                if action.isCheckable() and action.text() == scenario_name:
                    action.setChecked(True)
                    break
    
    def _populate_scenario_menu(self, menu):
        """填充场景菜单"""
        menu.clear()  # 清除现有菜单项
        
        # 加载场景配置
        scenarios = self._load_scenarios()
        
        # 添加全局场景
        global_action = menu.addAction("全局")
        global_action.setCheckable(True)
        global_action.triggered.connect(lambda: self._switch_to_scenario("global"))
        
        # 添加特定场景
        for scenario_id, config in scenarios.items():
            if config.get("type") == "specific":
                action = menu.addAction(config.get("name", scenario_id.replace("specific_", "")))
                action.setCheckable(True)
                action.triggered.connect(lambda checked, sid=scenario_id: self._switch_to_scenario(sid))
        
        # 添加分隔符
        menu.addSeparator()
        
        # 添加场景管理菜单项
        scenario_manage_action = QAction("场景管理", self)
        scenario_manage_action.triggered.connect(self.show_scenario_filter_dialog)
        menu.addAction(scenario_manage_action)
        
        # 默认选中全局场景
        global_action.setChecked(True)
    
    def _load_scenarios(self):
        """从文件加载场景配置"""
        scenario_config_path = os.path.join(self.CACHE_DIR, 'scenarios.json')
        try:
            if os.path.exists(scenario_config_path):
                with open(scenario_config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            print(f"加载场景配置失败: {e}")
            return {}
    
    def _switch_to_scenario(self, scenario_id):
        """切换到指定场景"""
        scenarios = self._load_scenarios()
        
        if scenario_id == "global":
            # 全局场景：显示所有键值
            selected_keys = list(self.all_keys)
        else:
            # 特定场景
            scenario = scenarios.get(scenario_id, {})
            selected_keys = scenario.get("selected_keys", list(self.all_keys))
        
        # 更新当前选中的键值
        self.current_selected_keys = selected_keys
        
        # 更新dock窗口内容
        self.my_dock_widget.update_content(self.current_selected_keys)
        
        # 更新菜单项的选中状态
        actions = self.scenario_menu.actions()
        for action in actions:
            if action.isCheckable():
                action.setChecked(False)
        
        if scenario_id == "global":
            # 全局场景是第一个菜单项
            if actions and actions[0].isCheckable():
                actions[0].setChecked(True)
        else:
            # 查找对应的特定场景菜单项
            scenario_name = scenarios.get(scenario_id, {}).get("name", scenario_id.replace("specific_", ""))
            for action in actions:
                if action.isCheckable() and action.text() == scenario_name:
                    action.setChecked(True)
                    break

    def show_scenario_filter_dialog(self):
        dialog = ScenarioFilterDialog(self.all_keys, self.current_selected_keys, self)
        # 连接场景变更信号
        dialog.scenarios_changed.connect(self._refresh_scenario_menu)
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
    
    def open_constraint_editor(self):
        """打开独立的约束编辑器"""
        import os
        import subprocess
        import sys
        from PyQt6.QtWidgets import QMessageBox
        
        try:
            # 获取约束编辑器路径
            tools_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tools")
            editor_script = os.path.join(tools_dir, "constraint_editor.py")
            
            # 检查约束编辑器文件是否存在
            if not os.path.exists(editor_script):
                QMessageBox.warning(self, "错误", f"约束编辑器文件不存在: {editor_script}")
                return
            
            # 使用当前Python解释器启动约束编辑器
            subprocess.Popen([sys.executable, editor_script], cwd=tools_dir)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动约束编辑器时发生错误: {str(e)}")
    
    def _populate_constraints_menu(self, constraints_menu):
        """填充约束菜单，列出可用的约束文件"""
        import os
        import glob
        from PyQt6.QtGui import QAction, QActionGroup
        
        # 清空现有菜单项
        constraints_menu.clear()
        
        # 添加"刷新"动作
        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(lambda: self._populate_constraints_menu(constraints_menu))
        constraints_menu.addAction(refresh_action)
        
        # 添加"重新加载约束配置"动作
        reload_action = QAction("重新加载约束配置", self)
        reload_action.triggered.connect(self._reload_constraint_config)
        constraints_menu.addAction(reload_action)
        
        # 添加"添加约束yml"动作
        add_constraint_action = QAction("添加约束yml", self)
        add_constraint_action.triggered.connect(self._add_new_constraint_file)
        constraints_menu.addAction(add_constraint_action)
        
        constraints_menu.addSeparator()
        
        # 获取约束文件目录
        cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        # 搜索所有yaml和yml文件
        constraint_files = glob.glob(os.path.join(cache_dir, "*.yaml")) + glob.glob(os.path.join(cache_dir, "*.yml"))
        
        # 如果没有找到约束文件，显示提示
        if not constraint_files:
            no_files_action = QAction("无可用约束文件", self)
            no_files_action.setEnabled(False)
            constraints_menu.addAction(no_files_action)
            return
        
        # 创建动作组，确保只能选择一个选项
        action_group = QActionGroup(self)
        action_group.setExclusive(True)
        
        # 获取当前实际使用的约束文件路径
        current_constraint_file = os.path.join(cache_dir, "field_constraints.yaml")
        
        # 如果还没有设置当前约束文件路径，则初始化为默认文件
        if self.current_constraint_file_path is None:
            self.current_constraint_file_path = current_constraint_file
        
        # 添加每个约束文件到菜单
        for file_path in constraint_files:
            file_name = os.path.basename(file_path)
            action = QAction(file_name, self)
            action.setCheckable(True)
            
            # 将动作添加到动作组
            action_group.addAction(action)
            
            # 检查是否是当前使用的约束文件（通过比较文件路径）
            if os.path.abspath(file_path) == os.path.abspath(self.current_constraint_file_path):
                action.setChecked(True)
            
            # 连接点击事件
            action.triggered.connect(lambda checked, path=file_path: self._apply_constraint_file(path))
            constraints_menu.addAction(action)
    
    def _add_new_constraint_file(self):
        """添加新的约束yml文件，通过弹窗输入文件路径"""
        import os
        import json
        import yaml
        from PyQt6.QtWidgets import QInputDialog, QMessageBox, QFileDialog
        
        try:
            # 弹窗选择JSON文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "选择JSON文件", 
                os.path.join(self.root_dir, "out"),
                "JSON文件 (*.json)"
            )
            
            if not file_path:
                return  # 用户取消选择
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "警告", f"文件不存在: {file_path}")
                return
            
            # 读取JSON文件，保持原始顺序
            with open(file_path, 'r', encoding='utf-8') as f:
                result_data = json.load(f, object_pairs_hook=collections.OrderedDict)
            
            # 获取结果数据中的所有键
            if not isinstance(result_data, dict):
                QMessageBox.warning(self, "警告", "文件格式不正确，无法获取字段信息。")
                return
            
            # 弹窗输入文件名
            file_name, ok = QInputDialog.getText(self, "新建约束文件", "请输入约束文件名(不含扩展名):")
            if not ok or not file_name.strip():
                return  # 用户取消或未输入文件名
            
            # 确保文件名以.yaml结尾
            if not file_name.endswith('.yaml') and not file_name.endswith('.yml'):
                file_name += '.yaml'
            
            # 创建约束文件内容，保持原始顺序
            from collections import OrderedDict
            constraint_content = OrderedDict()
            for key in result_data.keys():
                constraint_content[key] = {
                    "type": "string",
                    "required": True,
                    "description": f"约束字段: {key}"
                }
            
            # 保存约束文件到.cache目录
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            constraint_file_path = os.path.join(cache_dir, file_name)
            
            # 检查文件是否已存在
            if os.path.exists(constraint_file_path):
                reply = QMessageBox.question(self, "文件已存在", 
                                          f"文件 {file_name} 已存在，是否覆盖？",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # 写入YAML文件，保持原始顺序
            with open(constraint_file_path, 'w', encoding='utf-8') as f:
                # 转换为普通字典再写入，避免Python对象序列化问题
                normal_dict = dict(constraint_content)
                yaml.dump(normal_dict, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            # 显示成功消息
            QMessageBox.information(self, "成功", f"约束文件 {file_name} 已创建成功！")
            
            # 刷新约束菜单
            menubar = self.menuBar()
            constraints_menu = None
            for action in menubar.actions():
                if action.text() == "约束":
                    constraints_menu = action.menu()
                    break
            
            if constraints_menu:
                self._populate_constraints_menu(constraints_menu)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建约束文件时出错: {str(e)}")

    def _reload_constraint_config(self):
        """重新加载当前约束配置"""
        from .field_constraints import constraint_config
        import os
        from PyQt6.QtWidgets import QMessageBox
        
        try:
            # 获取缓存目录
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")
            current_constraint_file = os.path.join(cache_dir, "field_constraints.yaml")
            
            # 如果文件存在，则重新加载
            if os.path.exists(current_constraint_file):
                # 重新加载约束配置
                if constraint_config.load_from_file(current_constraint_file):
                    # 更新编辑器中的约束选项
                    if hasattr(self, 'key_value_editor'):
                        self.key_value_editor._load_fields_from_constraints()
                    
                    QMessageBox.information(self, "成功", "约束配置已重新加载！")
                else:
                    QMessageBox.warning(self, "错误", f"加载约束文件失败: {current_constraint_file}")
            else:
                QMessageBox.information(self, "提示", "约束文件不存在，无需重新加载")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"重新加载约束配置时发生错误: {str(e)}")
            
    def _apply_constraint_file(self, file_path):
        """应用指定的约束文件"""
        from .field_constraints import constraint_config
        import os
        from PyQt6.QtWidgets import QMessageBox
        
        try:
            # 获取缓存目录
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache")
            current_constraint_file = os.path.join(cache_dir, "field_constraints.yaml")
            
            # 如果不是默认文件，则复制为默认文件
            if os.path.abspath(file_path) != os.path.abspath(current_constraint_file):
                import shutil
                shutil.copy2(file_path, current_constraint_file)
            
            # 更新当前选中的约束文件路径
            self.current_constraint_file_path = file_path
            
            # 重新加载约束配置
            if constraint_config.load_from_file(current_constraint_file):
                # 更新编辑器中的约束选项
                if hasattr(self, 'key_value_editor'):
                    self.key_value_editor._load_fields_from_constraints()
                
                # 刷新约束菜单
                menubar = self.menuBar()
                constraints_menu = None
                for action in menubar.actions():
                    if action.text() == "约束":
                        constraints_menu = action.menu()
                        break
                
                if constraints_menu:
                    self._populate_constraints_menu(constraints_menu)
                
                # 成功应用约束文件时不显示提示信息
            else:
                # 使用规范化路径显示错误信息
                normalized_path = os.path.normpath(file_path)
                QMessageBox.warning(self, "错误", f"加载约束文件失败: {normalized_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用约束文件时发生错误: {str(e)}")
