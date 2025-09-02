"""
GUI应用主类
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
        
        # 工作线程
        self.detection_worker: Optional[DetectionWorker] = None
        
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
        
        # 状态和控制栏
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 5, 0, 5)
        
        # 检测按钮
        self.detect_button = QPushButton("开始检测")
        self.detect_button.clicked.connect(self.start_detection)
        self.detect_button.setEnabled(False)
        status_layout.addWidget(self.detect_button)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # 保存按钮
        self.save_button = QPushButton("保存结果")
        self.save_button.clicked.connect(self.save_results)
        self.save_button.setEnabled(False)
        status_layout.addWidget(self.save_button)
        
        right_layout.addWidget(status_widget)
        main_layout.addWidget(right_widget, stretch=1)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        # 打开文件
        open_action = QAction('打开图片(&O)', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # 最近文件
        self.recent_menu = file_menu.addMenu('最近文件(&R)')
        self.update_recent_menu()
        
        file_menu.addSeparator()
        
        # 保存结果
        save_action = QAction('保存结果(&S)', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_results)
        file_menu.addAction(save_action)
        
        # 移除导出配置选项
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction('退出(&X)', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 视图菜单
        view_menu = menubar.addMenu('视图(&V)')
        
        # 添加显示检测区域的动作
        self.toggle_regions_action = QAction('显示检测区域(&R)', self)
        self.toggle_regions_action.setShortcut('Ctrl+R')
        self.toggle_regions_action.setCheckable(True)
        self.toggle_regions_action.setChecked(True)  # 默认显示
        self.toggle_regions_action.triggered.connect(self.toggle_detection_regions)
        view_menu.addAction(self.toggle_regions_action)

        # 在现有的 toggle_regions_action 后面添加
        self.toggle_lines_action = QAction('显示文本行(&L)', self)
        self.toggle_lines_action.setShortcut('Ctrl+L')
        self.toggle_lines_action.setCheckable(True)
        self.toggle_lines_action.setChecked(True)  # 默认显示
        self.toggle_lines_action.triggered.connect(self.toggle_text_lines)
        view_menu.addAction(self.toggle_lines_action)
        

        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        
        about_action = QAction('关于(&A)', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def toggle_text_lines(self):
        """切换文本行显示"""
        self.image_viewer.toggle_lines()
        # 更新动作文本
        if self.image_viewer.show_lines:
            self.toggle_lines_action.setText('隐藏文本行(&L)')
        else:
            self.toggle_lines_action.setText('显示文本行(&L)')
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar('主工具栏')
        
        # 打开文件
        open_action = QAction(QIcon(), '打开', self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        # 检测
        detect_action = QAction(QIcon(), '检测', self)
        detect_action.triggered.connect(self.start_detection)
        toolbar.addAction(detect_action)
        
        # 保存
        save_action = QAction(QIcon(), '保存', self)
        save_action.triggered.connect(self.save_results)
        toolbar.addAction(save_action)

    def toggle_detection_regions(self):
        """切换检测区域显示"""
        self.image_viewer.toggle_regions()
        # 更新动作文本
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
                    **params  # 这样会包含device参数
                )
                device_info = f"({self.detector.device})" if hasattr(self.detector, 'device') else ""
                self.status_label.setText(f"检测器已加载: {Path(model_path).name} {device_info}")
            else:
                self.status_label.setText("请选择模型文件")
        except Exception as e:
            QMessageBox.warning(self, "警告", f"检测器初始化失败: {e}")
            self.status_label.setText("检测器初始化失败")
    
    def open_file(self):
        """打开图片文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片文件", 
            str(self.config.examples_dir),
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        
        if file_path:
            self.load_image(file_path)
    
    def load_image(self, file_path: str):
        """加载图片"""
        try:
            # 显示图片
            self.image_viewer.load_image(file_path)
            self.current_image_path = file_path
            
            # 更新UI状态
            self.detect_button.setEnabled(self.detector is not None)
            self.save_button.setEnabled(False)
            
            # 更新最近文件
            self.add_recent_file(file_path)
            
            # 更新状态
            self.status_label.setText(f"已加载: {Path(file_path).name}")
            self.statusBar().showMessage(f"图片已加载: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载图片: {e}")
    
    def start_detection(self):
        """开始检测"""
        if not self.current_image_path or not self.detector:
            return
        
        # 更新检测器参数
        params = self.parameter_panel.get_parameters()
        self.detector.update_parameters(**params)
        
        # 禁用按钮，显示进度
        self.detect_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        
        # 启动检测线程
        self.detection_worker = DetectionWorker(self.detector, self.current_image_path)
        self.detection_worker.finished.connect(self.on_detection_finished)
        self.detection_worker.error.connect(self.on_detection_error)
        self.detection_worker.progress.connect(self.on_detection_progress)
        self.detection_worker.start()
    
    def on_detection_finished(self, results: DetectionResults):
        """检测完成回调"""
        self.current_results = results
        
        # 显示结果图片
        self.image_viewer.set_result_image(results.result_image)
        self.image_viewer.set_detection_regions(results.text_regions)
        
        # 更新UI状态
        self.detect_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # 更新状态信息
        region_count = len(results.text_regions)
        detection_time = results.detection_time
        self.status_label.setText(f"检测完成: {region_count} 个区域, {detection_time:.2f}s")
        self.statusBar().showMessage(f"检测完成: 找到 {region_count} 个文字区域")
        
        # 更新参数面板统计信息
        self.parameter_panel.update_stats(results.to_dict())
    
    def on_detection_error(self, error_msg: str):
        """检测错误回调"""
        self.detect_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("检测失败")
        
        QMessageBox.critical(self, "检测失败", f"检测过程中发生错误: {error_msg}")
    
    def on_detection_progress(self, message: str):
        """检测进度回调"""
        self.statusBar().showMessage(message)
    
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
                # 获取新参数
                params = self.parameter_panel.get_parameters()
                model_path = self.parameter_panel.get_model_path()
                
                # 如果模型路径或设备改变了，需要重新初始化检测器
                need_reinit = (model_path != self.detector.model_path or 
                            params.get('device') != self.detector.device)
                
                if need_reinit:
                    self.init_detector()
                else:
                    # 仅更新其他参数
                    self.detector.update_parameters(**params)
            except Exception as e:
                QMessageBox.warning(self, "警告", f"参数更新失败: {e}")
    
    def add_recent_file(self, file_path: str):
        """添加到最近文件"""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        
        self.recent_files.insert(0, file_path)
        
        # 限制最近文件数量
        max_recent = self.config.gui_params.get('recent_files_count', 10)
        if len(self.recent_files) > max_recent:
            self.recent_files = self.recent_files[:max_recent]
        
        self.update_recent_menu()
    
    def update_recent_menu(self):
        """更新最近文件菜单"""
        self.recent_menu.clear()
        
        for i, file_path in enumerate(self.recent_files):
            if Path(file_path).exists():
                action = QAction(f"{i+1}. {Path(file_path).name}", self)
                action.triggered.connect(lambda checked, path=file_path: self.load_image(path))
                self.recent_menu.addAction(action)
        
        if not self.recent_files:
            action = QAction("(空)", self)
            action.setEnabled(False)
            self.recent_menu.addAction(action)
    
    def export_config(self):
        """导出配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "config.yaml", "配置文件 (*.yaml *.json)"
        )
        
        if file_path:
            try:
                self.config.save(file_path)
                QMessageBox.information(self, "成功", f"配置已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")
    
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
        
        # 保存窗口几何
        settings.setValue("geometry", self.saveGeometry())
        
        # 保存最近文件
        settings.setValue("recent_files", self.recent_files)
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 停止检测线程
        if self.detection_worker and self.detection_worker.isRunning():
            reply = QMessageBox.question(
                self, "确认退出", "检测正在进行中，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            
            self.detection_worker.quit()
            self.detection_worker.wait()
        
        # 保存设置
        self.save_settings()
        
        # 清理资源
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