from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, 
                            QPushButton, QDialogButtonBox, QGridLayout, 
                            QGroupBox, QListWidget, QListWidgetItem, QSplitter,
                            QLabel, QComboBox, QLineEdit, QMessageBox, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal
import json
import os

class ScenarioFilterDialog(QDialog):
    """场景筛选对话框，支持全局和特定场景的键值筛选"""
    
    # 信号：当筛选设置改变时发出
    filter_changed = pyqtSignal(dict)
    
    def __init__(self, all_keys, current_selected_keys=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("场景筛选设置")
        self.all_keys = all_keys
        self.current_selected_keys = current_selected_keys if current_selected_keys is not None else []
        self.checkboxes = {}
        
        # 场景相关数据
        self.scenarios = {}  # 存储所有场景配置
        self.current_scenario = None  # 当前选中的场景
        self.global_selected_keys = list(all_keys)  # 全局选中的键值，默认全部选中
        
        # 场景配置文件路径
        self.scenario_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.cache', 'scenarios.json')
        
        self._init_ui()
        self._load_scenarios()
        
    def _init_ui(self):
        """初始化UI界面"""
        main_layout = QVBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：场景选择和管理
        left_widget = self._create_scenario_panel()
        splitter.addWidget(left_widget)
        
        # 右侧：键值筛选面板
        right_widget = self._create_filter_panel()
        splitter.addWidget(right_widget)
        
        # 设置分割器比例
        splitter.setSizes([200, 500])
        
        main_layout.addWidget(splitter)
        
        # 底部按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
    def _create_scenario_panel(self):
        """创建左侧场景选择和管理面板"""
        left_widget = QGroupBox("场景管理")
        left_layout = QVBoxLayout(left_widget)
        
        # 场景类型选择
        scenario_type_layout = QHBoxLayout()
        scenario_type_layout.addWidget(QLabel("场景类型:"))
        self.scenario_type_combo = QComboBox()
        self.scenario_type_combo.addItems(["全局场景", "特定场景"])
        self.scenario_type_combo.currentTextChanged.connect(self._on_scenario_type_changed)
        scenario_type_layout.addWidget(self.scenario_type_combo)
        left_layout.addLayout(scenario_type_layout)
        
        # 场景列表
        self.scenario_list = QListWidget()
        self.scenario_list.itemClicked.connect(self._on_scenario_selected)
        left_layout.addWidget(self.scenario_list)
        
        # 场景操作按钮
        scenario_btn_layout = QHBoxLayout()
        self.add_scenario_btn = QPushButton("添加场景")
        self.add_scenario_btn.clicked.connect(self._add_scenario)
        self.delete_scenario_btn = QPushButton("删除场景")
        self.delete_scenario_btn.clicked.connect(self._delete_scenario)
        self.save_scenario_btn = QPushButton("保存当前")
        self.save_scenario_btn.clicked.connect(self._save_current_scenario)
        
        scenario_btn_layout.addWidget(self.add_scenario_btn)
        scenario_btn_layout.addWidget(self.delete_scenario_btn)
        scenario_btn_layout.addWidget(self.save_scenario_btn)
        left_layout.addLayout(scenario_btn_layout)
        
        return left_widget
        
    def _create_filter_panel(self):
        """创建右侧键值筛选面板"""
        right_widget = QGroupBox("键值筛选")
        right_layout = QVBoxLayout(right_widget)
        
        # 当前场景标签
        self.current_scenario_label = QLabel("当前场景: 无")
        self.current_scenario_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(self.current_scenario_label)
        
        # 标签页：已显示/未显示
        self.tab_widget = QTabWidget()
        
        # 已显示标签页
        self.displayed_widget = QGroupBox()
        displayed_layout = QGridLayout()
        self.displayed_widget.setLayout(displayed_layout)
        self.tab_widget.addTab(self.displayed_widget, "已显示")
        
        # 未显示标签页
        self.not_displayed_widget = QGroupBox()
        not_displayed_layout = QGridLayout()
        self.not_displayed_widget.setLayout(not_displayed_layout)
        self.tab_widget.addTab(self.not_displayed_widget, "未显示")
        
        right_layout.addWidget(self.tab_widget)
        
        # 快速操作按钮
        quick_action_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self._select_all)
        self.deselect_all_btn = QPushButton("全不选")
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        self.reset_btn = QPushButton("重置为全局")
        self.reset_btn.clicked.connect(self._reset_to_global)
        
        quick_action_layout.addWidget(self.select_all_btn)
        quick_action_layout.addWidget(self.deselect_all_btn)
        quick_action_layout.addWidget(self.reset_btn)
        right_layout.addLayout(quick_action_layout)
        
        return right_widget
        
    def _on_scenario_type_changed(self, scenario_type):
        """场景类型改变时的处理"""
        self.scenario_list.clear()
        
        if scenario_type == "全局场景":
            # 添加默认的全局场景
            item = QListWidgetItem("默认全局")
            item.setData(Qt.ItemDataRole.UserRole, "global_default")
            self.scenario_list.addItem(item)
            
            # 添加其他自定义全局场景
            for name, config in self.scenarios.items():
                if config.get("type") == "global":
                    item = QListWidgetItem(name)
                    item.setData(Qt.ItemDataRole.UserRole, name)
                    self.scenario_list.addItem(item)
        else:
            # 添加特定场景
            for name, config in self.scenarios.items():
                if config.get("type") == "specific":
                    item = QListWidgetItem(name)
                    item.setData(Qt.ItemDataRole.UserRole, name)
                    self.scenario_list.addItem(item)
                    
    def _on_scenario_selected(self, item):
        """场景选择时的处理"""
        scenario_id = item.data(Qt.ItemDataRole.UserRole)
        if not scenario_id:
            return
            
        # 加载场景配置
        if scenario_id == "global_default":
            # 默认全局场景：显示所有键值
            self.current_scenario = {
                "id": "global_default",
                "name": "默认全局",
                "type": "global",
                "selected_keys": list(self.all_keys)
            }
            self.global_selected_keys = list(self.all_keys)
        else:
            self.current_scenario = self.scenarios.get(scenario_id, {})
            if self.current_scenario.get("type") == "global":
                self.global_selected_keys = self.current_scenario.get("selected_keys", list(self.all_keys))
        
        # 更新UI
        self._update_scenario_label()
        self._update_checkboxes()
        
    def _update_scenario_label(self):
        """更新当前场景标签"""
        if self.current_scenario:
            scenario_type = "全局" if self.current_scenario.get("type") == "global" else "特定"
            self.current_scenario_label.setText(f"当前场景: {self.current_scenario.get('name', '未知')} ({scenario_type})")
        else:
            self.current_scenario_label.setText("当前场景: 无")
            
    def _update_checkboxes(self):
        """更新复选框状态"""
        # 清除现有复选框
        for checkbox in self.checkboxes.values():
            checkbox.setParent(None)
        self.checkboxes.clear()
        
        # 确定当前可用的键值
        if self.current_scenario and self.current_scenario.get("type") == "specific":
            # 特定场景：基于全局选中的键值
            available_keys = self.global_selected_keys
        else:
            # 全局场景：所有键值
            available_keys = self.all_keys
            
        # 获取当前场景选中的键值
        selected_keys = self.current_scenario.get("selected_keys", []) if self.current_scenario else []
        
        # 创建复选框
        displayed_layout = self.displayed_widget.layout()
        not_displayed_layout = self.not_displayed_widget.layout()
        
        # 清除布局中的现有项
        while displayed_layout.count():
            item = displayed_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        while not_displayed_layout.count():
            item = not_displayed_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        row_displayed = 0
        col_displayed = 0
        row_not_displayed = 0
        col_not_displayed = 0
        num_columns = 3
        
        for key in available_keys:
            checkbox = QCheckBox(key)
            self.checkboxes[key] = checkbox
            
            if key in selected_keys:
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
                    
    def _select_all(self):
        """全选当前可用的键值"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)
            
    def _deselect_all(self):
        """全不选当前可用的键值"""
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)
            
    def _reset_to_global(self):
        """重置为全局选中的键值"""
        if self.current_scenario and self.current_scenario.get("type") == "specific":
            # 特定场景：重置为全局选中的键值
            for key, checkbox in self.checkboxes.items():
                checkbox.setChecked(key in self.global_selected_keys)
                
    def _add_scenario(self):
        """添加新场景"""
        from PyQt6.QtWidgets import QInputDialog
        
        scenario_type = self.scenario_type_combo.currentText()
        type_prefix = "global" if scenario_type == "全局场景" else "specific"
        
        name, ok = QInputDialog.getText(self, "添加场景", "请输入场景名称:")
        if ok and name:
            scenario_id = f"{type_prefix}_{name}"
            
            # 创建新场景
            if scenario_type == "全局场景":
                new_scenario = {
                    "id": scenario_id,
                    "name": name,
                    "type": "global",
                    "selected_keys": list(self.all_keys)  # 默认选中所有键值
                }
            else:
                new_scenario = {
                    "id": scenario_id,
                    "name": name,
                    "type": "specific",
                    "selected_keys": list(self.global_selected_keys)  # 默认使用全局选中的键值
                }
                
            self.scenarios[scenario_id] = new_scenario
            self._on_scenario_type_changed(scenario_type)  # 刷新场景列表
            
            # 选中新创建的场景
            for i in range(self.scenario_list.count()):
                item = self.scenario_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == scenario_id:
                    self.scenario_list.setCurrentItem(item)
                    self._on_scenario_selected(item)
                    break
                    
    def _delete_scenario(self):
        """删除当前选中的场景"""
        current_item = self.scenario_list.currentItem()
        if not current_item:
            return
            
        scenario_id = current_item.data(Qt.ItemDataRole.UserRole)
        if not scenario_id or scenario_id == "global_default":
            QMessageBox.warning(self, "警告", "不能删除默认全局场景!")
            return
            
        reply = QMessageBox.question(self, "确认删除", 
                                   f"确定要删除场景 '{current_item.text()}' 吗?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                                   
        if reply == QMessageBox.StandardButton.Yes:
            if scenario_id in self.scenarios:
                del self.scenarios[scenario_id]
                
            # 删除列表项
            row = self.scenario_list.row(current_item)
            self.scenario_list.takeItem(row)
            
            # 清除当前场景
            self.current_scenario = None
            self._update_scenario_label()
            self._update_checkboxes()
            
    def _save_current_scenario(self):
        """保存当前场景的配置"""
        if not self.current_scenario:
            QMessageBox.warning(self, "警告", "没有选中的场景!")
            return
            
        # 获取当前选中的键值
        selected_keys = [key for key, checkbox in self.checkboxes.items() if checkbox.isChecked()]
        
        # 更新场景配置
        self.current_scenario["selected_keys"] = selected_keys
        
        # 如果是全局场景，更新全局选中的键值
        if self.current_scenario.get("type") == "global":
            self.global_selected_keys = selected_keys
            
        # 保存到场景字典
        scenario_id = self.current_scenario["id"]
        if scenario_id != "global_default":  # 不保存默认全局场景
            self.scenarios[scenario_id] = self.current_scenario
            
        # 保存到文件
        self._save_scenarios()
        
        QMessageBox.information(self, "成功", f"场景 '{self.current_scenario['name']}' 已保存!")
        
    def _load_scenarios(self):
        """从文件加载场景配置"""
        try:
            if os.path.exists(self.scenario_config_path):
                with open(self.scenario_config_path, 'r', encoding='utf-8') as f:
                    self.scenarios = json.load(f)
            else:
                # 创建默认场景配置文件
                self.scenarios = {}
                self._save_scenarios()
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载场景配置失败: {e}")
            self.scenarios = {}
            
        # 刷新场景列表
        self._on_scenario_type_changed(self.scenario_type_combo.currentText())
        
        # 默认选中默认全局场景
        if self.scenario_list.count() > 0:
            self.scenario_list.setCurrentRow(0)
            self._on_scenario_selected(self.scenario_list.currentItem())
            
    def _save_scenarios(self):
        """保存场景配置到文件"""
        try:
            os.makedirs(os.path.dirname(self.scenario_config_path), exist_ok=True)
            with open(self.scenario_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.scenarios, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"保存场景配置失败: {e}")
            
    def get_selected_keys(self):
        """获取当前场景选中的键值"""
        if not self.current_scenario:
            return self.current_selected_keys
            
        # 获取当前选中的键值
        selected_keys = [key for key, checkbox in self.checkboxes.items() if checkbox.isChecked()]
        
        # 如果是特定场景，确保只返回全局选中的键值中的子集
        if self.current_scenario.get("type") == "specific":
            selected_keys = [key for key in selected_keys if key in self.global_selected_keys]
            
        return selected_keys
        
    def get_current_scenario(self):
        """获取当前场景信息"""
        return self.current_scenario