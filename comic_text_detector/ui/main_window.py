"""
GUI应用主类 - 优化OCR结果管理版本
"""

import sys
from pathlib import Path
from typing import Optional, List

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
except ImportError:
    raise ImportError("PyQt5未安装，请运行：pip install PyQt5")

from core.detector import ComicTextDetector, DetectionResults
from core.results import ProjectResults
from ui.widgets.image_viewer import ImageViewer
from ui.widgets.parameter_panel import ParameterPanel
from ui.menu_manager import MenuManager
from ui.event_handlers import EventHandlers
from config.config import Config


class ComicTextDetectorGUI(QMainWindow):
    """漫画文本检测器GUI主窗口 - 优化OCR管理版本"""
    
    def __init__(self):
        super().__init__()
        
        # 配置
        self.config = Config()
        
        # 应用状态
        self.detector: Optional[ComicTextDetector] = None
        self.current_results: Optional[DetectionResults] = None
        self.current_image_path: Optional[str] = None
        self.recent_files: List[str] = []
        
        # 项目管理
        self.current_project_folder: Optional[str] = None
        self.current_image_files: List[str] = []
        self.current_image_index: int = 0
        self.current_project_results: Optional[ProjectResults] = None

        # 工作线程（由事件处理器管理）
        self.detection_worker = None
        self.ocr_worker = None
        self.batch_worker = None
        
        # 管理器和处理器
        self.menu_manager: Optional[MenuManager] = None
        self.event_handlers: Optional[EventHandlers] = None
        
        # 初始化UI和管理器
        self.init_ui()
        self.init_managers()
        self.init_detector()
        self.event_handlers.load_settings()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("漫画文本检测器 v1.0 (OCR优化版)")
        self.setMinimumSize(1000, 700)
        
        # 设置窗口大小
        gui_config = self.config.gui_params
        if 'window_size' in gui_config:
            self.resize(*gui_config['window_size'])
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧面板 - 参数控制
        self.parameter_panel = ParameterPanel(self.config)
        main_layout.addWidget(self.parameter_panel, stretch=0)
        
        # 右侧面板 - 图像显示和控制
        right_widget = self.create_right_panel()
        main_layout.addWidget(right_widget, stretch=1)
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
    
    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 控制按钮区域
        control_widget = self.create_control_buttons()
        right_layout.addWidget(control_widget)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)
        
        # 图像查看器
        self.image_viewer = ImageViewer()
        right_layout.addWidget(self.image_viewer, stretch=1)
        
        # 导航和状态栏
        nav_status_widget = self.create_navigation_bar()
        right_layout.addWidget(nav_status_widget)
        
        return right_widget
    
    def create_control_buttons(self) -> QWidget:
        """创建控制按钮"""
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(5, 5, 5, 5)
        
        # 检测按钮
        self.detect_button = QPushButton("🔍 开始检测")
        self.detect_button.setStyleSheet(self.get_button_style("#2196F3", "#1976D2"))
        self.detect_button.setEnabled(False)
        control_layout.addWidget(self.detect_button)
        
        # OCR按钮
        self.ocr_button = QPushButton("📝 OCR识别")
        self.ocr_button.setStyleSheet(self.get_button_style("#4CAF50", "#45a049"))
        self.ocr_button.setEnabled(False)
        control_layout.addWidget(self.ocr_button)
        
        control_layout.addStretch()
        return control_widget
    
    def create_navigation_bar(self) -> QWidget:
        """创建导航栏"""
        nav_status_widget = QWidget()
        nav_status_layout = QHBoxLayout(nav_status_widget)
        nav_status_layout.setContentsMargins(0, 5, 0, 5)

        # 导航按钮
        self.prev_button = QPushButton("⬅️ 上一张")
        self.prev_button.setEnabled(False)
        nav_status_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("下一张 ➡️")
        self.next_button.setEnabled(False)
        nav_status_layout.addWidget(self.next_button)
        
        nav_status_layout.addStretch()
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666666; font-size: 12px;")
        nav_status_layout.addWidget(self.status_label)

        return nav_status_widget
    
    def get_button_style(self, bg_color: str, hover_color: str) -> str:
        """获取按钮样式"""
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
        """
    
    def init_managers(self):
        """初始化管理器和处理器"""
        # 创建菜单管理器
        self.menu_manager = MenuManager(self)
        self.menu_manager.create_menu_bar()
        
        # 创建事件处理器
        self.event_handlers = EventHandlers(self)
        
        # 连接信号
        self.connect_signals()
    
    def connect_signals(self):
        """连接所有信号"""
        # 菜单信号
        self.menu_manager.open_folder_requested.connect(
            self.event_handlers.handle_open_folder)
        self.menu_manager.batch_detection_requested.connect(
            self.event_handlers.handle_batch_detection)
        self.menu_manager.batch_ocr_requested.connect(
            self.event_handlers.handle_batch_ocr)
        self.menu_manager.exit_requested.connect(self.close)
        
        self.menu_manager.toggle_regions_requested.connect(
            self.event_handlers.handle_toggle_regions)
        self.menu_manager.toggle_lines_requested.connect(
            self.event_handlers.handle_toggle_lines)
        self.menu_manager.toggle_blocks_requested.connect(
            self.event_handlers.handle_toggle_blocks)
        
        self.menu_manager.start_detection_requested.connect(
            self.event_handlers.handle_start_detection)
        self.menu_manager.start_ocr_requested.connect(
            self.event_handlers.handle_start_ocr)
        
        self.menu_manager.about_requested.connect(
            self.event_handlers.handle_show_about)
        
        # 按钮信号
        self.detect_button.clicked.connect(
            self.event_handlers.handle_start_detection)
        self.ocr_button.clicked.connect(
            self.event_handlers.handle_start_ocr)
        
        # 导航按钮信号
        self.prev_button.clicked.connect(
            self.event_handlers.handle_prev_image)
        self.next_button.clicked.connect(
            self.event_handlers.handle_next_image)
        
        # 参数面板信号
        self.parameter_panel.parameters_changed.connect(self.on_parameters_changed)
        self.parameter_panel.ocr_text_modified.connect(self.on_ocr_text_modified)
        self.parameter_panel.refresh_requested.connect(self.on_refresh_ocr_requested) 
    
    def on_refresh_ocr_requested(self):
        """处理刷新OCR请求"""
        if self.current_image_path and self.current_project_folder:
            input_folder = Path(self.current_project_folder)
            project_results_dir = input_folder / "results"  # 【修改】输出到项目内部
            image_name = Path(self.current_image_path).stem
            
            self.parameter_panel.load_ocr_from_json(str(project_results_dir), image_name)
            self.statusBar().showMessage("OCR结果已刷新")

    def init_detector(self):
        """初始化检测器"""
        try:
            model_path = self.parameter_panel.get_model_path()
            if model_path and Path(model_path).exists():
                params = self.parameter_panel.get_parameters()
                self.detector = ComicTextDetector(
                    model_path=model_path,
                    config=self.config,
                    enable_ocr=True,  # 总是启用OCR，但分离执行
                    **params
                )
                device_info = f"({self.detector.device})" if hasattr(self.detector, 'device') else ""
                self.statusBar().showMessage(f"检测器已加载: {Path(model_path).name} {device_info}")
            else:
                self.statusBar().showMessage("请选择模型文件")
        except Exception as e:
            QMessageBox.warning(self, "警告", f"检测器初始化失败: {e}")
            self.statusBar().showMessage("检测器初始化失败")
    
    def on_parameters_changed(self):
        """参数变化回调"""
        if hasattr(self, 'detector') and self.detector:
            try:
                params = self.parameter_panel.get_parameters()
                model_path = self.parameter_panel.get_model_path()
                
                # 检查是否需要重新初始化检测器
                need_reinit = (model_path != self.detector.model_path or 
                             params.get('device') != self.detector.device)
                
                if need_reinit:
                    self.init_detector()
                else:
                    self.detector.update_parameters(**params)
            except Exception as e:
                QMessageBox.warning(self, "警告", f"参数更新失败: {e}")

    def on_ocr_text_modified(self, region_idx: int, new_text: str):
        """【优化】OCR文本修改回调 - 使用项目内部路径"""
        if self.current_results:
            try:
                # 更新可视化（如果需要重新生成带OCR文本的结果图）
                self.image_viewer.set_detection_regions(self.current_results.text_regions)
                
                # 【修改】如果在项目模式下，同步到JSON文件 - 使用项目内部路径
                if (self.current_project_folder and 
                    self.current_project_results):
                    
                    input_folder = Path(self.current_project_folder)
                    project_results_dir = input_folder / "results"  # 【修改】输出到项目内部
                    image_name = self.current_results.image_name
                    
                    # 同步到JSON
                    self.parameter_panel.sync_ocr_to_json(
                        str(project_results_dir), image_name, region_idx, new_text)
                
                # 更新状态栏
                self.statusBar().showMessage(f"区域{region_idx+1}的OCR文本已修改并保存")
                
            except Exception as e:
                print(f"保存OCR修改时出错: {e}")
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 停止所有工作线程
        workers = [
            ('detection_worker', "检测"),
            ('ocr_worker', "OCR识别"), 
            ('batch_worker', "批量处理")
        ]
        
        running_workers = []
        for worker_name, worker_desc in workers:
            if hasattr(self, worker_name):
                worker = getattr(self, worker_name)
                if worker and worker.isRunning():
                    running_workers.append(worker_desc)
        
        if running_workers:
            reply = QMessageBox.question(
                self, "确认退出", 
                f"以下任务正在进行中：{', '.join(running_workers)}\n确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            
            # 停止所有线程
            for worker_name, _ in workers:
                if hasattr(self, worker_name):
                    worker = getattr(self, worker_name)
                    if worker and worker.isRunning():
                        worker.quit()
                        worker.wait()
        
        # 保存设置并清理资源
        if self.event_handlers:
            self.event_handlers.save_settings()
        
        if self.detector:
            del self.detector
        
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("漫画文本检测器")
    app.setApplicationVersion("1.0")
    
    window = ComicTextDetectorGUI()
    window.show()
    
    sys.exit(app.exec_())