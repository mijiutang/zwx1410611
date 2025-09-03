"""
GUI应用主类 - 分离版本（检测和OCR独立）- 适配新的项目结构
"""

import sys
import json
import os
import time
from pathlib import Path
from typing import Optional, List

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
except ImportError:
    raise ImportError("PyQt5未安装，请运行：pip install PyQt5")

from src.core.detector import ComicTextDetector, DetectionResults, ProjectResults
from src.ui.widgets.image_viewer import ImageViewer
from src.ui.widgets.parameter_panel import ParameterPanel
from config.config import Config


class DetectionWorker(QThread):
    """仅检测工作线程"""
    
    finished = pyqtSignal(object)  # DetectionResults
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, detector: ComicTextDetector, image_path: str):
        super().__init__()
        self.detector = detector
        self.image_path = image_path
    
    def run(self):
        try:
            self.progress.emit("正在执行文字检测...")
            results = self.detector.detect_only(self.image_path)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class OCRWorker(QThread):
    """OCR工作线程"""
    
    finished = pyqtSignal(object)  # DetectionResults with OCR
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, detector: ComicTextDetector, detection_results: DetectionResults):
        super().__init__()
        self.detector = detector
        self.detection_results = detection_results
    
    def run(self):
        try:
            self.progress.emit("正在进行OCR识别...")
            results = self.detector.run_ocr_on_results(self.detection_results)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class BatchProcessWorker(QThread):
    """批量处理工作线程 - 使用新的项目结构"""
    
    finished = pyqtSignal(object)  # ProjectResults
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int, str)  # current, total, message
    
    def __init__(self, detector: ComicTextDetector, image_files: List[str], 
                 project_name: str, output_dir: str, include_ocr: bool = True):
        super().__init__()
        self.detector = detector
        self.image_files = image_files
        self.project_name = project_name
        self.output_dir = output_dir
        self.include_ocr = include_ocr
    
    def run(self):
        try:
            def progress_callback(current, total, message):
                """进度回调函数"""
                self.progress.emit(current, total, message)
            
            # 使用新的批量处理方法
            project_results = self.detector.batch_process_project(
                image_files=self.image_files,
                project_name=self.project_name,
                output_dir=self.output_dir,
                include_ocr=self.include_ocr,
                progress_callback=progress_callback
            )
            
            self.finished.emit(project_results)
            
        except Exception as e:
            self.error.emit(str(e))


class ComicTextDetectorGUI(QMainWindow):
    """漫画文本检测器GUI主窗口 - 分离版本"""
    
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
        
        # 工作线程
        self.detection_worker: Optional[DetectionWorker] = None
        self.ocr_worker: Optional[OCRWorker] = None
        self.batch_worker: Optional[BatchProcessWorker] = None
        
        # 初始化UI
        self.init_ui()
        self.init_detector()
        self.load_settings()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("漫画文本检测器 v1.0 (项目结构优化版)")
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
        self.parameter_panel.parameters_changed.connect(self.on_parameters_changed)
        main_layout.addWidget(self.parameter_panel, stretch=0)
        
        # 右侧面板 - 图像显示和控制
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 控制按钮区域
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(5, 5, 5, 5)
        
        # 检测按钮
        self.detect_button = QPushButton("🔍 开始检测")
        self.detect_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.detect_button.clicked.connect(self.start_detection)
        self.detect_button.setEnabled(False)
        control_layout.addWidget(self.detect_button)
        
        # OCR按钮
        self.ocr_button = QPushButton("📝 OCR识别")
        self.ocr_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.ocr_button.clicked.connect(self.start_ocr)
        self.ocr_button.setEnabled(False)
        control_layout.addWidget(self.ocr_button)
        
        # 保存按钮
        self.save_button = QPushButton("💾 保存结果")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.save_button.clicked.connect(self.save_results)
        self.save_button.setEnabled(False)
        control_layout.addWidget(self.save_button)
        
        control_layout.addStretch()
        right_layout.addWidget(control_widget)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)
        
        # 图像查看器
        self.image_viewer = ImageViewer()
        right_layout.addWidget(self.image_viewer, stretch=1)
        
        # 导航和状态栏
        nav_status_widget = QWidget()
        nav_status_layout = QHBoxLayout(nav_status_widget)
        nav_status_layout.setContentsMargins(0, 5, 0, 5)

        # 导航按钮
        self.prev_button = QPushButton("⬅️ 上一张")
        self.prev_button.clicked.connect(self.prev_image)
        self.prev_button.setEnabled(False)
        nav_status_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("下一张 ➡️")
        self.next_button.clicked.connect(self.next_image)
        self.next_button.setEnabled(False)
        nav_status_layout.addWidget(self.next_button)
        
        nav_status_layout.addStretch()
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666666; font-size: 12px;")
        nav_status_layout.addWidget(self.status_label)

        right_layout.addWidget(nav_status_widget)
        
        main_layout.addWidget(right_widget, stretch=1)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        # 打开项目文件夹
        open_action = QAction('打开项目文件夹(&O)', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_project_folder)
        file_menu.addAction(open_action)
        
        # 最近项目菜单
        self.recent_menu = file_menu.addMenu('最近项目(&R)')
        self.update_recent_menu()
        
        file_menu.addSeparator()
        
        # 批量处理
        batch_action = QAction('批量处理（仅检测）- 自动输出(&B)', self)
        batch_action.triggered.connect(self.start_batch_detection)
        file_menu.addAction(batch_action)

        # 批量处理（包含OCR）
        batch_ocr_action = QAction('批量处理（含OCR）- 自动输出(&M)', self)
        batch_ocr_action.triggered.connect(self.start_batch_with_ocr)
        file_menu.addAction(batch_ocr_action)
        
        # 保存结果
        save_action = QAction('保存结果(&S)', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_results)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction('退出(&X)', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 视图菜单
        view_menu = menubar.addMenu('视图(&V)')
        
        # 显示检测区域
        self.toggle_regions_action = QAction('显示检测区域(&R)', self)
        self.toggle_regions_action.setShortcut('Ctrl+R')
        self.toggle_regions_action.setCheckable(True)
        self.toggle_regions_action.setChecked(True)
        self.toggle_regions_action.triggered.connect(self.toggle_detection_regions)
        view_menu.addAction(self.toggle_regions_action)

        # 显示文本行
        self.toggle_lines_action = QAction('显示文本行(&L)', self)
        self.toggle_lines_action.setShortcut('Ctrl+L')
        self.toggle_lines_action.setCheckable(True)
        self.toggle_lines_action.setChecked(True)
        self.toggle_lines_action.triggered.connect(self.toggle_text_lines)
        view_menu.addAction(self.toggle_lines_action)

        # 显示文本块
        self.toggle_blocks_action = QAction('显示文本块(&B)', self)
        self.toggle_blocks_action.setShortcut('Ctrl+Shift+B')
        self.toggle_blocks_action.setCheckable(True)
        self.toggle_blocks_action.setChecked(True)
        self.toggle_blocks_action.triggered.connect(self.toggle_text_blocks)
        view_menu.addAction(self.toggle_blocks_action)

        # 处理菜单
        process_menu = menubar.addMenu('处理(&P)')
        
        # 开始检测
        detect_action = QAction('开始检测(&D)', self)
        detect_action.setShortcut('F5')
        detect_action.triggered.connect(self.start_detection)
        process_menu.addAction(detect_action)
        
        # OCR识别
        ocr_action = QAction('OCR识别(&O)', self)
        ocr_action.setShortcut('F6')
        ocr_action.triggered.connect(self.start_ocr)
        process_menu.addAction(ocr_action)

        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        
        about_action = QAction('关于(&A)', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def open_project_folder(self):
        """打开项目文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "选择项目文件夹", 
            str(self.config.examples_dir)
        )
        
        if folder_path:
            self.load_project_folder(folder_path)

    def load_project_folder(self, folder_path: str):
        """加载项目文件夹"""
        try:
            from src.utils.io_utils import find_all_imgs
            
            # 检查文件夹中的图片
            image_files = find_all_imgs(folder_path, abs_path=True)
            if not image_files:
                QMessageBox.warning(self, "警告", f"文件夹中没有找到图片文件: {folder_path}")
                return
            
            # 保存当前项目信息
            self.current_project_folder = folder_path
            self.current_image_files = image_files
            self.current_image_index = 0
            
            # 显示第一张图片
            self.image_viewer.load_image(image_files[0])
            self.current_image_path = image_files[0]
            
            # 更新按钮状态
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(len(image_files) > 1)
            self.detect_button.setEnabled(True)
            
            # 清空之前的结果
            self.current_results = None
            self.ocr_button.setEnabled(False)
            self.save_button.setEnabled(False)
            
            # 更新最近文件夹
            self.add_recent_folder(folder_path)
            
            # 更新状态
            self.statusBar().showMessage(f"项目已加载: {folder_path} ({len(image_files)} 个文件)")
            self.status_label.setText(f"已加载 {len(image_files)} 个文件")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载项目文件夹: {e}")

    def prev_image(self):
        """切换到上一张图片"""
        if self.current_image_files and self.current_image_index > 0:
            self.current_image_index -= 1
            self.load_current_image()

    def next_image(self):
        """切换到下一张图片"""
        if self.current_image_files and self.current_image_index < len(self.current_image_files) - 1:
            self.current_image_index += 1
            self.load_current_image()

    def load_current_image(self):
        """加载当前索引的图片"""
        if not self.current_image_files:
            return
            
        current_image = self.current_image_files[self.current_image_index]
        self.image_viewer.load_image(current_image)
        self.current_image_path = current_image
        
        # 清空之前的结果
        self.current_results = None
        self.ocr_button.setEnabled(False)
        self.save_button.setEnabled(False)
        
        # 更新按钮状态
        self.prev_button.setEnabled(self.current_image_index > 0)
        self.next_button.setEnabled(self.current_image_index < len(self.current_image_files) - 1)
        
        # 更新状态显示
        image_name = Path(current_image).name
        total_count = len(self.current_image_files)
        self.statusBar().showMessage(f"图片: {image_name} ({self.current_image_index + 1}/{total_count})")
        self.status_label.setText(f"图片 {self.current_image_index + 1}/{total_count}: {image_name}")

    def start_detection(self):
        """开始文字检测"""
        if not self.current_image_path or not self.detector:
            QMessageBox.information(self, "提示", "请先选择图片并确保检测器已加载")
            return
        
        # 更新检测器参数
        params = self.parameter_panel.get_parameters()
        self.detector.update_parameters(**params)
        
        # 禁用按钮
        self.detect_button.setEnabled(False)
        self.ocr_button.setEnabled(False)
        self.save_button.setEnabled(False)
        
        # 显示进度
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.status_label.setText("正在检测...")
        
        # 启动检测线程
        self.detection_worker = DetectionWorker(self.detector, self.current_image_path)
        self.detection_worker.finished.connect(self.on_detection_finished)
        self.detection_worker.error.connect(self.on_detection_error)
        self.detection_worker.progress.connect(self.on_detection_progress)
        self.detection_worker.start()

    def start_ocr(self):
        """开始OCR识别"""
        if not self.current_results or not self.detector:
            QMessageBox.information(self, "提示", "请先完成文字检测")
            return
        
        if self.current_results.has_ocr_results:
            reply = QMessageBox.question(
                self, "确认", "该图片已有OCR结果，是否重新识别？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # 禁用按钮
        self.detect_button.setEnabled(False)
        self.ocr_button.setEnabled(False)
        self.save_button.setEnabled(False)
        
        # 显示进度
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("正在OCR识别...")
        
        # 启动OCR线程
        self.ocr_worker = OCRWorker(self.detector, self.current_results)
        self.ocr_worker.finished.connect(self.on_ocr_finished)
        self.ocr_worker.error.connect(self.on_ocr_error)
        self.ocr_worker.progress.connect(self.on_ocr_progress)
        self.ocr_worker.start()

    def on_detection_progress(self, message: str):
        """检测进度更新"""
        self.status_label.setText(message)

    def on_detection_finished(self, results: DetectionResults):
        """检测完成回调"""
        self.current_results = results
        
        # 显示结果图片
        self.image_viewer.set_result_image(results.result_image)
        self.image_viewer.set_detection_regions(results.text_regions)
        
        # 更新状态信息
        region_count = len(results.text_regions)
        detection_time = results.detection_time
        self.statusBar().showMessage(f"检测完成: 找到 {region_count} 个文字区域, 耗时 {detection_time:.2f}s")
        self.status_label.setText(f"检测完成: {region_count} 个区域")
        
        # 更新参数面板统计信息
        self.parameter_panel.update_stats(results.to_dict())
        
        # 恢复按钮状态
        self.detect_button.setEnabled(True)
        self.ocr_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.progress_bar.setVisible(False)

    def on_detection_error(self, error_msg: str):
        """检测错误回调"""
        self.statusBar().showMessage("检测失败")
        self.status_label.setText("检测失败")
        QMessageBox.critical(self, "检测失败", f"检测过程中发生错误: {error_msg}")
        
        # 恢复按钮状态
        self.detect_button.setEnabled(True)
        self.progress_bar.setVisible(False)

    def on_ocr_progress(self, message: str):
        """OCR进度更新"""
        self.status_label.setText(message)

    def on_ocr_finished(self, results: DetectionResults):
        """OCR完成回调"""
        self.current_results = results
        
        # 更新显示（现在包含OCR文本）
        self.image_viewer.set_result_image(results.result_image)
        self.image_viewer.set_detection_regions(results.text_regions)
        
        # 更新状态信息
        ocr_time = results.ocr_time
        total_text_length = sum(len(text) for text in results.ocr_results.values())
        self.statusBar().showMessage(f"OCR完成: 识别了 {total_text_length} 个字符, 耗时 {ocr_time:.2f}s")
        self.status_label.setText(f"OCR完成: {total_text_length} 个字符")
        
        # 更新参数面板统计信息
        self.parameter_panel.update_stats(results.to_dict())
        
        # 恢复按钮状态
        self.detect_button.setEnabled(True)
        self.ocr_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.progress_bar.setVisible(False)

    def on_ocr_error(self, error_msg: str):
        """OCR错误回调"""
        self.statusBar().showMessage("OCR识别失败")
        self.status_label.setText("OCR失败")
        QMessageBox.critical(self, "OCR失败", f"OCR过程中发生错误: {error_msg}")
        
        # 恢复按钮状态
        self.detect_button.setEnabled(True)
        self.ocr_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def save_results(self):
        """保存检测结果"""
        if not self.current_results:
            QMessageBox.information(self, "提示", "没有检测结果可保存")
            return
        
        # 选择保存目录
        output_dir = QFileDialog.getExistingDirectory(
            self, "选择保存目录", str(self.config.results_dir)
        )
        
        if output_dir:
            try:
                saved_dir = self.detector.save_results(self.current_results, output_dir)
                
                # 构建保存信息
                save_info = f"结果已保存到: {saved_dir}\n\n包含内容:\n"
                save_info += f"- 检测结果图片\n"
                save_info += f"- 文字掩码\n" 
                save_info += f"- JSON格式结果\n"
                if self.current_results.has_ocr_results:
                    save_info += f"- OCR识别结果"
                
                QMessageBox.information(self, "成功", save_info)
                self.statusBar().showMessage(f"结果已保存: {saved_dir}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def toggle_text_lines(self):
        """切换文本行显示"""
        self.image_viewer.toggle_lines()
        if self.image_viewer.show_lines:
            self.toggle_lines_action.setText('隐藏文本行(&L)')
        else:
            self.toggle_lines_action.setText('显示文本行(&L)')

    def toggle_text_blocks(self):
        """切换文本块显示"""
        self.image_viewer.toggle_blocks()
        if self.image_viewer.show_blocks:
            self.toggle_blocks_action.setText('隐藏文本块(&B)')
        else:
            self.toggle_blocks_action.setText('显示文本块(&B)')

    def toggle_detection_regions(self):
        """切换检测区域显示"""
        self.image_viewer.toggle_regions()
        if self.image_viewer.show_regions:
            self.toggle_regions_action.setText('隐藏检测区域(&R)')
        else:
            self.toggle_regions_action.setText('显示检测区域(&R)')
    
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
    
    def add_recent_folder(self, folder_path: str):
        """添加到最近项目文件夹"""
        if folder_path in self.recent_files:
            self.recent_files.remove(folder_path)
        
        self.recent_files.insert(0, folder_path)
        
        # 限制最近文件数量
        max_recent = self.config.gui_params.get('recent_files_count', 10)
        if len(self.recent_files) > max_recent:
            self.recent_files = self.recent_files[:max_recent]
        
        self.update_recent_menu()
    
    def update_recent_menu(self):
        """更新最近项目文件夹菜单"""
        self.recent_menu.clear()
        
        for i, folder_path in enumerate(self.recent_files):
            if Path(folder_path).exists():
                # 显示文件夹名 + 上级目录，避免路径过长
                folder_name = Path(folder_path).name
                parent_name = Path(folder_path).parent.name
                display_name = f"{parent_name}/{folder_name}" if parent_name != folder_name else folder_name
                
                action = QAction(f"{i+1}. {display_name}", self)
                # 设置工具提示显示完整路径
                action.setToolTip(folder_path)
                action.triggered.connect(lambda checked, path=folder_path: self.load_project_folder(path))
                self.recent_menu.addAction(action)
        
        if not self.recent_files:
            action = QAction("(空)", self)
            action.setEnabled(False)
            self.recent_menu.addAction(action)

    def start_batch_detection(self):
        """开始批量检测（不含OCR）"""
        self._start_batch_processing(include_ocr=False)

    def start_batch_with_ocr(self):
        """开始批量处理（含OCR）"""
        self._start_batch_processing(include_ocr=True)

    def _start_batch_processing(self, include_ocr: bool = True):
        """开始批量处理 - 使用新的项目结构"""
        if not self.current_image_files or not self.detector:
            QMessageBox.information(self, "提示", "请先选择项目文件夹并确保检测器已加载")
            return
        
        if not self.current_project_folder:
            QMessageBox.warning(self, "错误", "当前没有选择项目文件夹")
            return
        
        # 自动生成项目名称和输出路径
        input_folder = Path(self.current_project_folder)
        project_name = f"{input_folder.name}_out"
        output_dir = str(input_folder.parent)  # 输出到输入文件夹的父目录
        
        # 检查输出目录是否可写
        if not os.access(output_dir, os.W_OK):
            QMessageBox.warning(self, "错误", f"输出目录没有写入权限：{output_dir}")
            return
        
        # 更新检测器参数
        params = self.parameter_panel.get_parameters()
        self.detector.update_parameters(**params)
        
        # 显示进度
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.current_image_files))
        
        # 禁用控件
        self.detect_button.setEnabled(False)
        self.ocr_button.setEnabled(False)
        self.save_button.setEnabled(False)
        
        operation_name = "批量处理（含OCR）" if include_ocr else "批量检测"
        self.status_label.setText(f"正在{operation_name}...")
        
        # 显示自动生成的路径信息
        self.statusBar().showMessage(f"开始{operation_name} -> 输出到: {Path(output_dir) / project_name}")
        
        # 启动批量处理线程
        self.batch_worker = BatchProcessWorker(
            self.detector, 
            self.current_image_files, 
            project_name,
            output_dir,
            include_ocr=include_ocr
        )
        self.batch_worker.finished.connect(self.on_batch_finished)
        self.batch_worker.error.connect(self.on_batch_error)
        self.batch_worker.progress.connect(self.on_batch_progress)
        self.batch_worker.start()

    def on_batch_progress(self, current, total, message):
        """批量处理进度回调"""
        self.progress_bar.setValue(current)
        self.statusBar().showMessage(f"批量处理进度: {current}/{total} - {message}")
        self.status_label.setText(f"处理中: {current}/{total}")

    def on_batch_finished(self, project_results: ProjectResults):
        """批量处理完成回调 - 适配新的ProjectResults"""
        total_files = len(project_results.detection_results)
        successful = sum(1 for result in project_results.detection_results if len(result.text_regions) > 0)
        
        self.statusBar().showMessage(f"批量处理完成: {successful}/{total_files} 成功")
        self.status_label.setText(f"批量完成: {successful}/{total_files}")
        
        # 获取项目统计信息
        project_stats = project_results.get_project_detection_results()['stats']
        
        # 计算输出路径（用于显示）
        if self.current_project_folder:
            input_folder = Path(self.current_project_folder)
            expected_output_path = input_folder.parent / f"{input_folder.name}_out"
        else:
            expected_output_path = "未知路径"
        
        completion_msg = f"项目 '{project_results.project_name}' 批量处理完成！\n\n"
        completion_msg += f"输出路径: {expected_output_path}\n\n"
        completion_msg += f"处理统计:\n"
        completion_msg += f"• 总文件数: {total_files}\n"
        completion_msg += f"• 检测成功: {successful}\n"
        completion_msg += f"• 总文字区域: {project_stats['total_regions']}\n"
        completion_msg += f"• OCR处理: {project_stats['images_with_ocr']}/{total_files}\n"
        completion_msg += f"• 总处理时间: {project_stats['total_detection_time']:.1f}s\n"
        
        if project_stats['total_ocr_time'] > 0:
            completion_msg += f"• OCR总时间: {project_stats['total_ocr_time']:.1f}s\n"
        
        completion_msg += f"\n结果已自动保存到输入文件夹同级目录！"
        
        QMessageBox.information(self, "批量处理完成", completion_msg)
        
        # 恢复控件状态
        self.detect_button.setEnabled(True)
        self.ocr_button.setEnabled(self.current_results is not None)
        self.save_button.setEnabled(self.current_results is not None)
        self.progress_bar.setVisible(False)

    def on_batch_error(self, error_msg: str):
        """批量处理错误回调"""
        self.statusBar().showMessage("批量处理失败")
        self.status_label.setText("批量处理失败")
        QMessageBox.critical(self, "批量处理失败", f"处理过程中发生错误: {error_msg}")
        
        # 恢复控件状态
        self.detect_button.setEnabled(True)
        self.ocr_button.setEnabled(self.current_results is not None)
        self.save_button.setEnabled(self.current_results is not None)
        self.progress_bar.setVisible(False)

    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h3>漫画文本检测器 v1.0 (项目结构优化版)</h3>
        <p>基于深度学习的漫画文本检测工具</p>
        <p><b>特性:</b></p>
        <ul>
        <li>支持中文和日文文本检测</li>
        <li>高精度的文本区域定位</li>
        <li>分离的检测和OCR流程</li>
        <li>可视化文本块和文本行预览</li>
        <li>友好的图形用户界面</li>
        <li>可配置的检测参数</li>
        <li>优化的项目结构输出</li>
        </ul>
        <p><b>项目输出结构:</b></p>
        <p>• 按项目名称创建输出文件夹<br>
        • result_images/ - 检测结果图片<br>
        • masks/ - 文字掩码<br>
        • detection_results.json - 检测结果摘要<br>
        • ocr_results.json - OCR识别结果</p>
        <p><b>使用流程:</b></p>
        <p>1. 打开项目文件夹<br>
        2. 点击"开始检测"预览文本区域<br>
        3. 点击"OCR识别"进行文字识别<br>
        4. 批量处理整个项目</p>
        <p><b>技术支持:</b> PyQt5, PyTorch, OpenCV, PaddleX</p>
        """
        QMessageBox.about(self, "关于", about_text)
    
    def load_settings(self):
        """加载设置"""
        settings = QSettings("ComicTextDetector", "MainWindow")
        
        # 恢复窗口几何
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # 恢复最近文件
        recent_files = settings.value("recent_files", [])
        if isinstance(recent_files, list):
            self.recent_files = recent_files
            self.update_recent_menu()
    
    def save_settings(self):
        """保存设置"""
        settings = QSettings("ComicTextDetector", "MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("recent_files", self.recent_files)
    
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
        self.save_settings()
        
        if self.detector:
            del self.detector
        
        event.accept()


if __name__ == "__main__":
    import time  # 添加import
    
    app = QApplication(sys.argv)
    app.setApplicationName("漫画文本检测器")
    app.setApplicationVersion("1.0")
    
    window = ComicTextDetectorGUI()
    window.show()
    
    sys.exit(app.exec_())