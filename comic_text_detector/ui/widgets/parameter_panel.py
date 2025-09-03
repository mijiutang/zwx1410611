"""
参数控制面板组件 - 优化OCR结果管理版本
"""
import json
from pathlib import Path
from utils.io_utils import NumpyEncoder
from typing import Dict, Any
import torch
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from config.config import Config


class ParameterPanel(QWidget):
    """参数控制面板"""
    
    parameters_changed = pyqtSignal()
    ocr_text_modified = pyqtSignal(int, str)
    refresh_requested = pyqtSignal()

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        
        # 控件引用
        self.model_path_edit = None
        self.device_combo = None
        self.input_size_combo = None
        self.conf_thresh_input = None
        self.mask_thresh_input = None
        self.containment_input = None
        self.min_box_width_spin = None
        self.min_box_height_spin = None
        self.enable_filter_checkbox = None
        self.lang_checkboxes = {}
        self.ocr_results_widgets = {}  # 存储OCR结果编辑控件
        self.current_detection_results = None  # 当前检测结果对象
        
        # 【新增】OCR结果管理相关
        self.current_project_dir = None
        self.current_image_name = None
        self.ocr_auto_save_timer = QTimer()  # 自动保存定时器
        self.ocr_auto_save_timer.setSingleShot(True)
        self.ocr_auto_save_timer.timeout.connect(self._auto_save_ocr_results)
        
        # 初始化UI
        self.init_ui()
        self.load_parameters()
    
    def init_ui(self):
        """初始化UI"""
        self.setFixedWidth(300)
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("检测参数")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        # 模型选择组
        model_group = self.create_model_group()
        layout.addWidget(model_group)
        
        # 设备和尺寸配置组
        config_group = self.create_config_group()
        layout.addWidget(config_group)
        
        # 检测参数组
        detection_group = self.create_detection_group()
        layout.addWidget(detection_group)
        
        # 语言选择组
        language_group = self.create_language_group()
        layout.addWidget(language_group)
        
        # OCR结果组
        ocr_group = self.create_ocr_group()
        layout.addWidget(ocr_group)
        
        # 弹簧，将控件推到顶部
        layout.addStretch()
        
        # 按钮区域
        button_layout = QVBoxLayout()
        
        # 重置参数按钮
        reset_button = QPushButton("重置参数")
        reset_button.clicked.connect(self.reset_parameters)
        button_layout.addWidget(reset_button)
        
        # 更新配置按钮
        self.update_config_button = QPushButton("更新默认配置")
        self.update_config_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.update_config_button.clicked.connect(self.update_default_config)
        button_layout.addWidget(self.update_config_button)
        
        layout.addLayout(button_layout)

    def create_model_group(self) -> QGroupBox:
        """创建模型选择组"""
        group = QGroupBox("模型设置")
        layout = QVBoxLayout(group)
        
        # 模型路径选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型文件:"))
        
        self.model_path_edit = QLineEdit()
        self.model_path_edit.setPlaceholderText("选择模型文件...")
        self.model_path_edit.textChanged.connect(self.parameters_changed.emit)
        model_layout.addWidget(self.model_path_edit, 1)
        
        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(self.browse_model)
        model_layout.addWidget(browse_button)
        
        layout.addLayout(model_layout)
        return group

    def create_config_group(self) -> QGroupBox:
        """创建配置参数组"""
        group = QGroupBox("运行配置")
        layout = QVBoxLayout(group)
        
        # 设备选择
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("计算设备:"))
        
        self.device_combo = QComboBox()
        
        # 检测可用设备
        devices = ["auto", "cpu"]
        if torch.cuda.is_available():
            devices.append("cuda")
            # 添加多GPU支持
            for i in range(torch.cuda.device_count()):
                devices.append(f"cuda:{i}")
        
        self.device_combo.addItems(devices)
        self.device_combo.setCurrentText("auto")
        self.device_combo.currentTextChanged.connect(self.parameters_changed.emit)
        
        device_layout.addWidget(self.device_combo)
        device_layout.addStretch()
        layout.addLayout(device_layout)

        # 输入尺寸选择
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("输入尺寸:"))
        
        self.input_size_combo = QComboBox()
        self.input_size_combo.addItems(["1024", "1280", "1536"])
        self.input_size_combo.setCurrentText("1280")
        self.input_size_combo.currentTextChanged.connect(self.parameters_changed.emit)
        
        size_layout.addWidget(self.input_size_combo)
        size_layout.addStretch()
        layout.addLayout(size_layout)
        
        return group

    def create_detection_group(self) -> QGroupBox:
        """创建检测参数组"""
        group = QGroupBox("检测参数")
        layout = QVBoxLayout(group)
        
        # 置信度阈值
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(QLabel("置信度阈值:"))
        
        self.conf_thresh_input = QDoubleSpinBox()
        self.conf_thresh_input.setRange(0.01, 0.99)
        self.conf_thresh_input.setSingleStep(0.01)
        self.conf_thresh_input.setDecimals(2)
        self.conf_thresh_input.setValue(0.40)
        self.conf_thresh_input.valueChanged.connect(self.parameters_changed.emit)
        
        conf_layout.addWidget(self.conf_thresh_input)
        conf_layout.addStretch()
        layout.addLayout(conf_layout)
        
        # 掩码阈值
        mask_layout = QHBoxLayout()
        mask_layout.addWidget(QLabel("掩码阈值:"))
        
        self.mask_thresh_input = QDoubleSpinBox()
        self.mask_thresh_input.setRange(0.01, 0.80)
        self.mask_thresh_input.setSingleStep(0.01)
        self.mask_thresh_input.setDecimals(2)
        self.mask_thresh_input.setValue(0.30)
        self.mask_thresh_input.valueChanged.connect(self.parameters_changed.emit)
        
        mask_layout.addWidget(self.mask_thresh_input)
        mask_layout.addStretch()
        layout.addLayout(mask_layout)
        
        # 包含关系阈值
        contain_layout = QHBoxLayout()
        contain_layout.addWidget(QLabel("包含关系阈值:"))
        
        self.containment_input = QDoubleSpinBox()
        self.containment_input.setRange(0.50, 1.00)
        self.containment_input.setSingleStep(0.01)
        self.containment_input.setDecimals(2)
        self.containment_input.setValue(0.80)
        self.containment_input.valueChanged.connect(self.parameters_changed.emit)
        
        contain_layout.addWidget(self.containment_input)
        contain_layout.addStretch()
        layout.addLayout(contain_layout)
        
        # 最小框尺寸
        min_size_layout = QHBoxLayout()
        min_size_layout.addWidget(QLabel("最小框尺寸:"))

        self.min_box_width_spin = QSpinBox()
        self.min_box_width_spin.setRange(1, 500)
        self.min_box_width_spin.setValue(10)
        self.min_box_width_spin.setSuffix(" px")
        self.min_box_width_spin.valueChanged.connect(self.parameters_changed.emit)

        self.min_box_height_spin = QSpinBox()
        self.min_box_height_spin.setRange(1, 500)
        self.min_box_height_spin.setValue(10)
        self.min_box_height_spin.setSuffix(" px")
        self.min_box_height_spin.valueChanged.connect(self.parameters_changed.emit)

        min_size_layout.addWidget(QLabel("宽:"))
        min_size_layout.addWidget(self.min_box_width_spin)
        min_size_layout.addWidget(QLabel("高:"))
        min_size_layout.addWidget(self.min_box_height_spin)
        min_size_layout.addStretch()
        layout.addLayout(min_size_layout)
        
        # 启用框过滤
        self.enable_filter_checkbox = QCheckBox("启用框过滤")
        self.enable_filter_checkbox.setChecked(True)
        self.enable_filter_checkbox.stateChanged.connect(self.parameters_changed.emit)
        layout.addWidget(self.enable_filter_checkbox)

        return group
      
    def create_language_group(self) -> QGroupBox:
        """创建语言选择组"""
        group = QGroupBox("支持语言")
        layout = QVBoxLayout(group)
        
        languages = [
            ("zh", "中文"),
            ("ja", "日文"), 
            ("eng", "英文"),
            ("unknown", "未知")
        ]
        
        for lang_code, lang_name in languages:
            checkbox = QCheckBox(lang_name)
            if lang_code in ["zh", "ja"]:  # 默认选中中文和日文
                checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.parameters_changed.emit)
            self.lang_checkboxes[lang_code] = checkbox
            layout.addWidget(checkbox)
        
        return group
    
    def browse_model(self):
        """浏览模型文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择模型文件",
            str(self.config.models_dir),
            "模型文件 (*.pt *.pth *.onnx)"
        )
        
        if file_path:
            self.model_path_edit.setText(file_path)
    
    def get_model_path(self) -> str:
        """获取模型路径"""
        return self.model_path_edit.text().strip()
    
    def get_parameters(self) -> Dict[str, Any]:
        """获取参数"""
        # 获取选中的语言
        allowed_languages = []
        for lang_code, checkbox in self.lang_checkboxes.items():
            if checkbox.isChecked():
                allowed_languages.append(lang_code)
        
        params = {
            "input_size": int(self.input_size_combo.currentText()),
            "conf_thresh": self.conf_thresh_input.value(),
            "mask_thresh": self.mask_thresh_input.value(),
            "allowed_languages": allowed_languages,
            "device": self.device_combo.currentText(),
            "containment_thresh": self.containment_input.value(),
            "enable_box_filter": self.enable_filter_checkbox.isChecked(),
            "min_box_width": self.min_box_width_spin.value(),
            "min_box_height": self.min_box_height_spin.value()
        }
        
        return params

    def set_parameters(self, params: Dict[str, Any]):
        """设置参数"""
        # 阻止信号发射
        self.blockSignals(True)
        
        try:
            # 设置输入尺寸
            if "input_size" in params:
                self.input_size_combo.setCurrentText(str(params["input_size"]))
            
            # 设置设备
            if "device" in params:
                self.device_combo.setCurrentText(params["device"])
            
            # 设置置信度阈值
            if "conf_thresh" in params:
                self.conf_thresh_input.setValue(params["conf_thresh"])
            
            # 设置掩码阈值
            if "mask_thresh" in params:
                self.mask_thresh_input.setValue(params["mask_thresh"])
            
            # 设置包含关系阈值
            if "containment_thresh" in params:
                self.containment_input.setValue(params["containment_thresh"])
            
            # 设置语言选择
            if "allowed_languages" in params:
                allowed_langs = params["allowed_languages"]
                for lang_code, checkbox in self.lang_checkboxes.items():
                    checkbox.setChecked(lang_code in allowed_langs)
            
            # 设置最小框尺寸
            if "min_box_width" in params:
                self.min_box_width_spin.setValue(params["min_box_width"])
            
            if "min_box_height" in params:
                self.min_box_height_spin.setValue(params["min_box_height"])
            
            # 设置启用框过滤
            if "enable_box_filter" in params:
                self.enable_filter_checkbox.setChecked(params["enable_box_filter"])
                
        finally:
            self.blockSignals(False)

    def load_parameters(self):
        """从配置加载参数"""
        # 设置默认模型路径
        if self.config.model_path.exists():
            self.model_path_edit.setText(str(self.config.model_path))
        
        # 设置检测参数
        params = self.config.detector_params
        self.set_parameters(params)
        
        print(f"已从配置加载参数: {params}")
    
    def reset_parameters(self):
        """重置为默认参数"""
        default_params = {
            "input_size": 1280,
            "conf_thresh": 0.4,
            "mask_thresh": 0.3,
            "containment_thresh": 0.8,
            "min_box_width": 10,
            "min_box_height": 10,
            "enable_box_filter": True,
            "allowed_languages": ["zh", "ja"],
            "device": "auto"
        }
        self.set_parameters(default_params)
        self.parameters_changed.emit()
    
    def update_default_config(self):
        """更新默认配置"""
        try:
            # 获取当前参数
            current_params = self.get_parameters()
            model_path = self.get_model_path()
            
            # 更新配置对象
            if model_path:
                try:
                    relative_path = str(Path(model_path).relative_to(self.config.project_root))
                    self.config.set('paths.default_model', relative_path)
                except ValueError:
                    # 如果无法获取相对路径，保存绝对路径
                    self.config.set('paths.default_model', model_path)
            
            for key, value in current_params.items():
                if key != 'device':  # device 不保存到默认配置
                    self.config.set(f'detector.{key}', value)
            
            # 保存为默认配置
            if self.config.save_as_default():
                QMessageBox.information(
                    self, 
                    "成功", 
                    "默认配置已更新！\n下次启动应用时将使用当前参数作为默认值。"
                )
            else:
                QMessageBox.warning(self, "警告", "默认配置更新失败！")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新默认配置时发生错误：{e}")

    def create_ocr_group(self) -> QGroupBox:
        """创建OCR结果显示组"""
        group = QGroupBox("OCR结果")
        self.ocr_layout = QVBoxLayout(group)
        
        # 【优化】刷新和状态栏
        control_layout = QHBoxLayout()
        refresh_button = QPushButton("刷新")
        refresh_button.setToolTip("从JSON文件重新加载OCR结果")
        refresh_button.clicked.connect(self.refresh_ocr_from_json)
        control_layout.addWidget(refresh_button)
        
        # 【新增】保存状态标签
        self.ocr_status_label = QLabel("就绪")
        self.ocr_status_label.setStyleSheet("color: #666666; font-size: 10px;")
        control_layout.addWidget(self.ocr_status_label)
        control_layout.addStretch()
        self.ocr_layout.addLayout(control_layout)
        
        # 滚动区域用于显示多个OCR结果
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)
        scroll_area.setMaximumHeight(400)
        
        # 创建OCR结果容器
        self.ocr_container = QWidget()
        self.ocr_container_layout = QVBoxLayout(self.ocr_container)
        self.ocr_container_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll_area.setWidget(self.ocr_container)
        self.ocr_layout.addWidget(scroll_area)
        
        # 提示标签
        self.ocr_hint_label = QLabel("请先完成检测和OCR识别")
        self.ocr_hint_label.setAlignment(Qt.AlignCenter)
        self.ocr_hint_label.setStyleSheet("color: #888888; font-style: italic;")
        self.ocr_container_layout.addWidget(self.ocr_hint_label)
        
        return group

    def refresh_ocr_from_json(self):
        """手动刷新OCR结果"""
        self.refresh_requested.emit()

    def update_ocr_results(self, detection_results):
        """更新OCR结果显示"""
        from core.detector import DetectionResults
        
        self.current_detection_results = detection_results
        
        # 【新增】更新当前图片信息用于保存
        if hasattr(detection_results, 'image_name'):
            self.current_image_name = detection_results.image_name
        
        # 清空现有的OCR控件
        self.clear_ocr_results()
        
        if not isinstance(detection_results, DetectionResults) or not detection_results.has_ocr_results:
            self.ocr_hint_label.setText("暂无OCR结果")
            self.ocr_hint_label.setVisible(True)
            self.ocr_status_label.setText("无OCR结果")
            return
        
        self.ocr_hint_label.setVisible(False)
        
        # 根据text_regions创建OCR结果编辑控件
        for i, region in enumerate(detection_results.text_regions):
            ocr_text = region.get('ocr_text', '')
            
            # 创建每个OCR结果的控件组
            result_widget = QWidget()
            result_layout = QVBoxLayout(result_widget)
            result_layout.setContentsMargins(5, 5, 5, 5)
            
            # 次序标签（从1开始，不显示置信度）
            sequence_label = QLabel(f"区域 {i+1}")
            sequence_label.setFont(QFont("Arial", 10, QFont.Bold))
            sequence_label.setStyleSheet("color: #333333; padding: 2px 0px;")
            result_layout.addWidget(sequence_label)
            
            # 文本编辑框
            text_edit = QTextEdit()
            text_edit.setPlainText(ocr_text)
            text_edit.setMaximumHeight(80)
            text_edit.setMinimumHeight(50)
            
            # 【优化】连接文本变化信号到延迟保存
            text_edit.textChanged.connect(
                lambda region_idx=i: self.on_ocr_text_changed(region_idx)
            )
            
            result_layout.addWidget(text_edit)
            
            # 分隔线
            if i < len(detection_results.text_regions) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                line.setStyleSheet("color: #cccccc;")
                result_layout.addWidget(line)
            
            # 保存控件引用
            self.ocr_results_widgets[i] = text_edit
            
            # 添加到容器
            self.ocr_container_layout.addWidget(result_widget)
        
        self.ocr_status_label.setText(f"已加载 {len(detection_results.text_regions)} 个区域")

    def on_ocr_text_changed(self, region_idx: int):
        """OCR文本变化时的回调 - 【优化】延迟自动保存"""
        if (self.current_detection_results and 
            region_idx < len(self.current_detection_results.text_regions)):
            
            # 获取修改后的文本
            if region_idx in self.ocr_results_widgets:
                new_text = self.ocr_results_widgets[region_idx].toPlainText()
                
                # 更新检测结果中的OCR文本
                self.current_detection_results.text_regions[region_idx]['ocr_text'] = new_text
                
                # 更新OCR结果字典
                region_key = f"region_{region_idx}"
                self.current_detection_results.ocr_results[region_key] = new_text
                
                # 发射信号通知主窗口保存更改
                self.ocr_text_modified.emit(region_idx, new_text)
                
                # 【新增】启动延迟自动保存
                self.ocr_status_label.setText("编辑中...")
                self.ocr_auto_save_timer.stop()
                self.ocr_auto_save_timer.start(2000)  # 2秒后自动保存

    def _auto_save_ocr_results(self):
        """【新增】自动保存OCR结果到JSON"""
        if self.current_project_dir and self.current_image_name:
            try:
                self._save_current_ocr_to_json()
                self.ocr_status_label.setText("已自动保存")
            except Exception as e:
                self.ocr_status_label.setText("保存失败")
                print(f"自动保存OCR结果失败: {e}")

    def clear_ocr_results(self):
        """清空OCR结果显示"""
        # 清空控件引用
        self.ocr_results_widgets.clear()
        
        # 清空布局中的所有控件
        while self.ocr_container_layout.count():
            child = self.ocr_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 重新添加提示标签
        self.ocr_hint_label = QLabel("请先完成检测和OCR识别")
        self.ocr_hint_label.setAlignment(Qt.AlignCenter)
        self.ocr_hint_label.setStyleSheet("color: #888888; font-style: italic;")
        self.ocr_container_layout.addWidget(self.ocr_hint_label)
     
    def validate_parameters(self) -> tuple[bool, str]:
        """验证参数有效性"""
        # 检查模型文件
        model_path = self.get_model_path()
        if not model_path:
            return False, "请选择模型文件"
        
        if not Path(model_path).exists():
            return False, f"模型文件不存在: {model_path}"
        
        # 检查语言选择
        params = self.get_parameters()
        if not params["allowed_languages"]:
            return False, "请至少选择一种支持的语言"
        
        return True, ""
    
    def get_parameter_summary(self) -> str:
        """获取参数摘要"""
        params = self.get_parameters()
        model_name = Path(self.get_model_path()).name if self.get_model_path() else "未选择"
        
        summary = f"""参数摘要:
模型: {model_name}
设备: {params['device']}
输入尺寸: {params['input_size']}
置信度阈值: {params['conf_thresh']:.2f}
掩码阈值: {params['mask_thresh']:.2f}
支持语言: {', '.join(params['allowed_languages'])}
框过滤: {'启用' if params['enable_box_filter'] else '禁用'}"""
        
        return summary
    
    def load_ocr_from_json(self, project_results_dir: str, image_name: str):
        """【优化】从JSON文件加载OCR结果到面板"""
        # 【新增】更新当前项目信息
        self.current_project_dir = project_results_dir
        self.current_image_name = image_name
        
        if not project_results_dir or not image_name:
            self.clear_ocr_results()
            self.ocr_status_label.setText("无项目信息")
            return
            
        json_path = Path(project_results_dir) / "results.json"
        if not json_path.exists():
            self.clear_ocr_results()
            self.ocr_status_label.setText("无JSON文件")
            return
            
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 查找对应图片的OCR结果
            image_data = None
            for img in data.get("images", []):
                if img["image_name"] == image_name:
                    image_data = img
                    break
            
            if not image_data or not image_data.get("ocr_results") or not image_data["ocr_results"]["has_ocr"]:
                self.clear_ocr_results()
                self.ocr_status_label.setText("无OCR数据")
                return
            
            # 重建DetectionResults对象用于面板显示
            fake_results = type('FakeResults', (), {})()
            fake_results.has_ocr_results = True
            fake_results.text_regions = []
            fake_results.ocr_results = {}
            fake_results.image_name = image_name  # 【新增】设置图片名
            
            # 从JSON重建text_regions
            if image_data.get("detection_results") and image_data["detection_results"].get("text_regions"):
                for i, region in enumerate(image_data["detection_results"]["text_regions"]):
                    # 添加OCR文本到区域
                    region_key = f"区域{i+1}"
                    if region_key in image_data["ocr_results"]["regions"]:
                        region["ocr_text"] = image_data["ocr_results"]["regions"][region_key]
                        fake_results.ocr_results[f"region_{i}"] = region["ocr_text"]
                    fake_results.text_regions.append(region)
            
            # 更新面板显示
            self.update_ocr_results(fake_results)
            self.ocr_status_label.setText(f"已加载来自JSON")
            
        except Exception as e:
            print(f"从JSON加载OCR结果失败: {e}")
            self.clear_ocr_results()
            self.ocr_status_label.setText("加载失败")

    def sync_ocr_to_json(self, project_results_dir: str, image_name: str, region_idx: int, new_text: str):
        """【优化】将OCR文本更改同步到JSON文件"""
        if not project_results_dir or not image_name:
            return
            
        json_path = Path(project_results_dir) / "results.json"
        if not json_path.exists():
            return
        
        try:
            # 读取现有JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 查找并更新对应图片的OCR结果
            for img in data.get("images", []):
                if img["image_name"] == image_name:
                    if img.get("ocr_results") and img["ocr_results"]["has_ocr"]:
                        region_key = f"区域{region_idx+1}"
                        img["ocr_results"]["regions"][region_key] = new_text
                        
                        # 写回文件
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
                        
                        print(f"OCR文本已同步到JSON: {region_key} -> {new_text[:20]}...")
                    break
                    
        except Exception as e:
            print(f"同步OCR到JSON失败: {e}")

    def _save_current_ocr_to_json(self):
        """【新增】保存当前所有OCR结果到JSON"""
        if not self.current_project_dir or not self.current_image_name:
            return
        
        json_path = Path(self.current_project_dir) / "results.json"
        if not json_path.exists():
            return
            
        try:
            # 读取现有JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 查找并更新对应图片的所有OCR结果
            for img in data.get("images", []):
                if img["image_name"] == self.current_image_name:
                    if img.get("ocr_results") and img["ocr_results"]["has_ocr"]:
                        # 更新所有区域的OCR结果
                        for region_idx, text_edit in self.ocr_results_widgets.items():
                            region_key = f"区域{region_idx+1}"
                            current_text = text_edit.toPlainText()
                            img["ocr_results"]["regions"][region_key] = current_text
                        
                        # 写回文件
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
                        
                        print(f"已保存所有OCR结果到JSON: {self.current_image_name}")
                    break
                    
        except Exception as e:
            print(f"保存OCR结果到JSON失败: {e}")
            raise

    def set_project_context(self, project_dir: str, image_name: str):
        """【新增】设置项目上下文信息"""
        self.current_project_dir = project_dir
        self.current_image_name = image_name

    def clear_ocr_results(self):
        """清空OCR结果显示并重置状态"""
        # 清空控件引用
        self.ocr_results_widgets.clear()
        self.current_detection_results = None
        
        # 清空布局中的所有控件
        while self.ocr_container_layout.count():
            child = self.ocr_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 重新添加提示标签
        self.ocr_hint_label = QLabel("请先完成检测和OCR识别")
        self.ocr_hint_label.setAlignment(Qt.AlignCenter)
        self.ocr_hint_label.setStyleSheet("color: #888888; font-style: italic;")
        self.ocr_container_layout.addWidget(self.ocr_hint_label)


if __name__ == "__main__":
    # 测试参数面板
    import sys
    
    app = QApplication(sys.argv)
    
    config = Config()
    panel = ParameterPanel(config)
    
    # 创建测试窗口
    window = QWidget()
    layout = QHBoxLayout(window)
    layout.addWidget(panel)
    
    window.show()
    
    sys.exit(app.exec_())