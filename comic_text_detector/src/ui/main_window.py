"""
GUI应用主类 - 清理版本
"""

import sys
import json
from pathlib import Path
from typing import Optional, List

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
except ImportError:
    raise ImportError("PyQt5未安装，请运行：pip install PyQt5")

from src.core.detector import ComicTextDetector, DetectionResults
from src.ui.widgets.image_viewer import ImageViewer
from src.ui.widgets.parameter_panel import ParameterPanel
from config.config import Config


class DetectionWorker(QThread):
    """检测工作线程"""
    
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
            results = self.detector.detect(self.image_path)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class BatchProcessWorker(QThread):
    """批量处理工作线程"""
    
    finished = pyqtSignal(dict)  # 返回处理结果摘要
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int, str)  # current, total, message
    
    def __init__(self, detector: ComicTextDetector, image_files: List[str], output_dir: str):
        super().__init__()
        self.detector = detector
        self.image_files = image_files
        self.output_dir = output_dir
    
    def run(self):
        try:
            results_summary = {}
            total_files = len(self.image_files)
            
            for i, image_path in enumerate(self.image_files, 1):
                try:
                    file_name = Path(image_path).name
                    self.progress.emit(i, total_files, f"正在处理: {file_name}")
                    
                    # 执行检测和OCR
                    results = self.detector.detect(image_path, enable_ocr=True)
                    
                    # 保存结果
                    self.detector.save_results(results, self.output_dir)
                    
                    # 汇总OCR文本
                    all_texts = []
                    for region_key, text in results.ocr_results.items():
                        if text.strip():
                            all_texts.append(text.strip())
                    
                    combined_text = " ".join(all_texts)
                    results_summary[results.image_name] = combined_text
                    
                except Exception as e:
                    print(f"处理文件 {image_path} 时出错: {e}")
                    image_name = Path(image_path).stem
                    results_summary[image_name] = ""
            
            self.finished.emit(results_summary)
            
        except Exception as e:
            self.error.emit(str(e))


class ComicTextDetectorGUI(QMainWindow):
    """漫画文本检测器GUI主窗口"""
    
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
        self.batch_worker: Optional[BatchProcessWorker] = None
        
        # 初始化UI
        self.init_ui()
        self.init_detector()
        self.load_settings()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("漫画文本检测器 v1.0")
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
        
        # 右侧面板 - 图像显示
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 图像查看器
        self.image_viewer = ImageViewer()
        right_layout.addWidget(self.image_viewer, stretch=1)
        
        # 状态和控制栏 - 简化版，仅保留导航按钮
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 5, 0, 5)

        # 添加弹簧，让按钮居中显示
        status_layout.addStretch()

        self.prev_button = QPushButton("上一张")
        self.prev_button.clicked.connect(self.prev_image)
        self.prev_button.setEnabled(False)
        status_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("下一张")
        self.next_button.clicked.connect(self.next_image)
        self.next_button.setEnabled(False)
        status_layout.addWidget(self.next_button)

        # 添加弹簧，让按钮居中显示
        status_layout.addStretch()

        right_layout.addWidget(status_widget)
        
        # 为了避免代码错误，创建隐藏的占位组件
        self.batch_button = QPushButton()
        self.batch_button.hide()
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        self.status_label = QLabel()
        self.status_label.hide()
        self.save_button = QPushButton()
        self.save_button.hide()
        
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
        batch_action = QAction('开始批量处理(&B)', self)
        batch_action.setShortcut('Ctrl+B')
        batch_action.triggered.connect(self.start_batch_processing)
        file_menu.addAction(batch_action)
        
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
        self.toggle_blocks_action.setShortcut('Ctrl+B')
        self.toggle_blocks_action.setCheckable(True)
        self.toggle_blocks_action.setChecked(True)
        self.toggle_blocks_action.triggered.connect(self.toggle_text_blocks)
        view_menu.addAction(self.toggle_blocks_action)

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
            
            # 更新最近文件夹
            self.add_recent_folder(folder_path)
            
            # 更新状态
            self.statusBar().showMessage(f"项目已加载: {folder_path} ({len(image_files)} 个文件)")
            
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
        
        # 更新按钮状态
        self.prev_button.setEnabled(self.current_image_index > 0)
        self.next_button.setEnabled(self.current_image_index < len(self.current_image_files) - 1)
        
        # 更新状态显示
        image_name = Path(current_image).name
        total_count = len(self.current_image_files)
        self.statusBar().showMessage(f"图片: {image_name} ({self.current_image_index + 1}/{total_count})")

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
                    **params
                )
                device_info = f"({self.detector.device})" if hasattr(self.detector, 'device') else ""
                self.statusBar().showMessage(f"检测器已加载: {Path(model_path).name} {device_info}")
            else:
                self.statusBar().showMessage("请选择模型文件")
        except Exception as e:
            QMessageBox.warning(self, "警告", f"检测器初始化失败: {e}")
            self.statusBar().showMessage("检测器初始化失败")
    
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
        
        # 更新参数面板统计信息
        self.parameter_panel.update_stats(results.to_dict())
    
    def on_detection_error(self, error_msg: str):
        """检测错误回调"""
        self.statusBar().showMessage("检测失败")
        QMessageBox.critical(self, "检测失败", f"检测过程中发生错误: {error_msg}")
    
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
                QMessageBox.information(self, "成功", f"结果已保存到: {saved_dir}")
                self.statusBar().showMessage(f"结果已保存: {saved_dir}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
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

    def start_batch_processing(self):
        """开始批量处理"""
        if not self.current_image_files or not self.detector:
            QMessageBox.information(self, "提示", "请先选择项目文件夹并确保检测器已加载")
            return
        
        # 选择输出目录
        output_dir = QFileDialog.getExistingDirectory(
            self, "选择输出目录", str(self.config.results_dir)
        )
        
        if not output_dir:
            return
        
        # 更新检测器参数
        params = self.parameter_panel.get_parameters()
        self.detector.update_parameters(**params)
        
        # 启动批量处理线程
        self.batch_worker = BatchProcessWorker(self.detector, self.current_image_files, output_dir)
        self.batch_worker.finished.connect(self.on_batch_finished)
        self.batch_worker.error.connect(self.on_batch_error)
        self.batch_worker.progress.connect(self.on_batch_progress)
        self.batch_worker.start()

    def on_batch_progress(self, current, total, message):
        """批量处理进度回调"""
        self.statusBar().showMessage(f"批量处理进度: {current}/{total} - {message}")

    def on_batch_finished(self, results_summary):
        """批量处理完成回调"""
        total_files = len(results_summary)
        successful = sum(1 for text in results_summary.values() if text.strip())
        
        self.statusBar().showMessage(f"批量处理完成: {successful}/{total_files} 成功")
        
        QMessageBox.information(
            self, "完成", 
            f"批量处理完成！\n"
            f"总文件数: {total_files}\n"
            f"成功处理: {successful}\n"
            f"失败: {total_files - successful}"
        )

    def on_batch_error(self, error_msg: str):
        """批量处理错误回调"""
        self.statusBar().showMessage("批量处理失败")
        QMessageBox.critical(self, "批量处理失败", f"处理过程中发生错误: {error_msg}")

    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h3>漫画文本检测器 v1.0</h3>
        <p>基于深度学习的漫画文本检测工具</p>
        <p><b>特性:</b></p>
        <ul>
        <li>支持中文和日文文本检测</li>
        <li>高精度的文本区域定位</li>
        <li>友好的图形用户界面</li>
        <li>可配置的检测参数</li>
        </ul>
        <p><b>技术支持:</b> PyQt5, PyTorch, OpenCV</p>
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
        # 停止批量处理线程
        if hasattr(self, 'batch_worker') and self.batch_worker and self.batch_worker.isRunning():
            reply = QMessageBox.question(
                self, "确认退出", "批量处理正在进行中，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            
            self.batch_worker.quit()
            self.batch_worker.wait()
        
        # 保存设置并清理资源
        self.save_settings()
        
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