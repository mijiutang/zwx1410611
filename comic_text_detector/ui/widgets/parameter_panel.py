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