"""
事件处理器 - 处理所有UI事件和业务逻辑
"""

import os
import time
from pathlib import Path
from typing import List, Optional
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QObject, QSettings

from core.detector import ComicTextDetector, DetectionResults, ProjectResults
from config.config import Config


class EventHandlers(QObject):
    """事件处理器类"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
    
    def handle_open_folder(self):
        """处理打开项目文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self.main_window, "选择项目文件夹", 
            str(self.main_window.config.examples_dir)
        )
        
        if folder_path:
            self.load_project_folder(folder_path)

    def load_project_folder(self, folder_path: str):
        """加载项目文件夹"""
        try:
            from utils.io_utils import find_all_imgs
            
            # 检查文件夹中的图片
            image_files = find_all_imgs(folder_path, abs_path=True)
            if not image_files:
                QMessageBox.warning(self.main_window, "警告", f"文件夹中没有找到图片文件: {folder_path}")
                return
            
            # 保存当前项目信息
            self.main_window.current_project_folder = folder_path
            self.main_window.current_image_files = image_files
            self.main_window.current_image_index = 0
            
            # 显示第一张图片
            self.main_window.image_viewer.load_image(image_files[0])
            self.main_window.current_image_path = image_files[0]
            
            # 更新按钮状态
            self.main_window.prev_button.setEnabled(False)
            self.main_window.next_button.setEnabled(len(image_files) > 1)
            self.main_window.detect_button.setEnabled(True)
            
            # 清空之前的结果
            self.main_window.current_results = None
            self.main_window.ocr_button.setEnabled(False)
            self.main_window.save_button.setEnabled(False)
            
            # 更新最近文件夹
            self.add_recent_folder(folder_path)
            
            # 更新状态
            self.main_window.statusBar().showMessage(f"项目已加载: {folder_path} ({len(image_files)} 个文件)")
            self.main_window.status_label.setText(f"已加载 {len(image_files)} 个文件")
            
        except Exception as e:
            QMessageBox.critical(self.main_window, "错误", f"无法加载项目文件夹: {e}")

    def handle_prev_image(self):
        """切换到上一张图片"""
        if (self.main_window.current_image_files and 
            self.main_window.current_image_index > 0):
            self.main_window.current_image_index -= 1
            self.load_current_image()

    def handle_next_image(self):
        """切换到下一张图片"""
        if (self.main_window.current_image_files and 
            self.main_window.current_image_index < len(self.main_window.current_image_files) - 1):
            self.main_window.current_image_index += 1
            self.load_current_image()

    def load_current_image(self):
        """加载当前索引的图片"""
        if not self.main_window.current_image_files:
            return
            
        current_image = self.main_window.current_image_files[self.main_window.current_image_index]
        self.main_window.image_viewer.load_image(current_image)
        self.main_window.current_image_path = current_image
        
        # 清空之前的结果
        self.main_window.current_results = None
        self.main_window.ocr_button.setEnabled(False)
        self.main_window.save_button.setEnabled(False)
        
        # 更新按钮状态
        self.main_window.prev_button.setEnabled(self.main_window.current_image_index > 0)
        self.main_window.next_button.setEnabled(
            self.main_window.current_image_index < len(self.main_window.current_image_files) - 1)
        
        # 更新状态显示
        image_name = Path(current_image).name
        total_count = len(self.main_window.current_image_files)
        self.main_window.statusBar().showMessage(
            f"图片: {image_name} ({self.main_window.current_image_index + 1}/{total_count})")
        self.main_window.status_label.setText(
            f"图片 {self.main_window.current_image_index + 1}/{total_count}: {image_name}")

    def handle_start_detection(self):
        """开始文字检测"""
        if not self.main_window.current_image_path or not self.main_window.detector:
            QMessageBox.information(self.main_window, "提示", "请先选择图片并确保检测器已加载")
            return
        
        # 更新检测器参数
        params = self.main_window.parameter_panel.get_parameters()
        self.main_window.detector.update_parameters(**params)
        
        # 禁用按钮
        self.main_window.detect_button.setEnabled(False)
        self.main_window.ocr_button.setEnabled(False)
        self.main_window.save_button.setEnabled(False)
        
        # 显示进度
        self.main_window.progress_bar.setVisible(True)
        self.main_window.progress_bar.setRange(0, 0)  # 不确定进度
        self.main_window.status_label.setText("正在检测...")
        
        # 启动检测线程
        from ui.workers import DetectionWorker
        self.main_window.detection_worker = DetectionWorker(
            self.main_window.detector, self.main_window.current_image_path)
        self.main_window.detection_worker.finished.connect(self.on_detection_finished)
        self.main_window.detection_worker.error.connect(self.on_detection_error)
        self.main_window.detection_worker.progress.connect(self.on_detection_progress)
        self.main_window.detection_worker.start()

    def handle_start_ocr(self):
        """开始OCR识别"""
        if not self.main_window.current_results or not self.main_window.detector:
            QMessageBox.information(self.main_window, "提示", "请先完成文字检测")
            return
        
        if self.main_window.current_results.has_ocr_results:
            reply = QMessageBox.question(
                self.main_window, "确认", "该图片已有OCR结果，是否重新识别？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # 禁用按钮
        self.main_window.detect_button.setEnabled(False)
        self.main_window.ocr_button.setEnabled(False)
        self.main_window.save_button.setEnabled(False)
        
        # 显示进度
        self.main_window.progress_bar.setVisible(True)
        self.main_window.progress_bar.setRange(0, 0)
        self.main_window.status_label.setText("正在OCR识别...")
        
        # 启动OCR线程
        from ui.workers import OCRWorker
        self.main_window.ocr_worker = OCRWorker(
            self.main_window.detector, self.main_window.current_results)
        self.main_window.ocr_worker.finished.connect(self.on_ocr_finished)
        self.main_window.ocr_worker.error.connect(self.on_ocr_error)
        self.main_window.ocr_worker.progress.connect(self.on_ocr_progress)
        self.main_window.ocr_worker.start()

    def handle_save_results(self):
        """保存检测结果"""
        if not self.main_window.current_results:
            QMessageBox.information(self.main_window, "提示", "没有检测结果可保存")
            return
        
        # 选择保存目录
        output_dir = QFileDialog.getExistingDirectory(
            self.main_window, "选择保存目录", str(self.main_window.config.results_dir)
        )
        
        if output_dir:
            try:
                saved_dir = self.main_window.detector.save_results(
                    self.main_window.current_results, output_dir)
                
                # 构建保存信息
                save_info = f"结果已保存到: {saved_dir}\n\n包含内容:\n"
                save_info += f"- 检测结果图片\n"
                save_info += f"- 文字掩码\n" 
                save_info += f"- JSON格式结果\n"
                if self.main_window.current_results.has_ocr_results:
                    save_info += f"- OCR识别结果"
                
                QMessageBox.information(self.main_window, "成功", save_info)
                self.main_window.statusBar().showMessage(f"结果已保存: {saved_dir}")
                
            except Exception as e:
                QMessageBox.critical(self.main_window, "错误", f"保存失败: {e}")

    def handle_batch_detection(self):
        """开始批量检测（不含OCR）"""
        self._start_batch_processing(include_ocr=False)

    def handle_batch_ocr(self):
        """开始批量处理（含OCR）"""
        self._start_batch_processing(include_ocr=True)

    def _start_batch_processing(self, include_ocr: bool = True):
        """开始批量处理 - 使用新的项目结构"""
        if (not self.main_window.current_image_files or 
            not self.main_window.detector):
            QMessageBox.information(
                self.main_window, "提示", "请先选择项目文件夹并确保检测器已加载")
            return
        
        if not self.main_window.current_project_folder:
            QMessageBox.warning(self.main_window, "错误", "当前没有选择项目文件夹")
            return
        
        # 自动生成项目名称和输出路径
        input_folder = Path(self.main_window.current_project_folder)
        project_name = f"{input_folder.name}_out"
        output_dir = str(input_folder.parent)  # 输出到输入文件夹的父目录
        
        # 检查输出目录是否可写
        if not os.access(output_dir, os.W_OK):
            QMessageBox.warning(
                self.main_window, "错误", f"输出目录没有写入权限：{output_dir}")
            return
        
        # 更新检测器参数
        params = self.main_window.parameter_panel.get_parameters()
        self.main_window.detector.update_parameters(**params)
        
        # 显示进度
        self.main_window.progress_bar.setVisible(True)
        self.main_window.progress_bar.setRange(0, len(self.main_window.current_image_files))
        
        # 禁用控件
        self.main_window.detect_button.setEnabled(False)
        self.main_window.ocr_button.setEnabled(False)
        self.main_window.save_button.setEnabled(False)
        
        operation_name = "批量处理（含OCR）" if include_ocr else "批量检测"
        self.main_window.status_label.setText(f"正在{operation_name}...")
        
        # 显示自动生成的路径信息
        self.main_window.statusBar().showMessage(
            f"开始{operation_name} -> 输出到: {Path(output_dir) / project_name}")
        
        # 启动批量处理线程
        from ui.workers import BatchProcessWorker
        self.main_window.batch_worker = BatchProcessWorker(
            self.main_window.detector, 
            self.main_window.current_image_files, 
            project_name,
            output_dir,
            include_ocr=include_ocr
        )
        self.main_window.batch_worker.finished.connect(self.on_batch_finished)
        self.main_window.batch_worker.error.connect(self.on_batch_error)
        self.main_window.batch_worker.progress.connect(self.on_batch_progress)
        self.main_window.batch_worker.start()

    # 工作线程回调方法
    def on_detection_progress(self, message: str):
        """检测进度更新"""
        self.main_window.status_label.setText(message)

    def on_detection_finished(self, results: DetectionResults):
        """检测完成回调"""
        self.main_window.current_results = results
        
        # 显示结果图片
        self.main_window.image_viewer.set_result_image(results.result_image)
        self.main_window.image_viewer.set_detection_regions(results.text_regions)
        
        # 更新状态信息
        region_count = len(results.text_regions)
        detection_time = results.detection_time
        self.main_window.statusBar().showMessage(
            f"检测完成: 找到 {region_count} 个文字区域, 耗时 {detection_time:.2f}s")
        self.main_window.status_label.setText(f"检测完成: {region_count} 个区域")
        
        self.main_window.parameter_panel.update_ocr_results(results)
        
        # 恢复按钮状态
        self.main_window.detect_button.setEnabled(True)
        self.main_window.ocr_button.setEnabled(True)
        self.main_window.save_button.setEnabled(True)
        self.main_window.progress_bar.setVisible(False)

    def on_detection_error(self, error_msg: str):
        """检测错误回调"""
        self.main_window.statusBar().showMessage("检测失败")
        self.main_window.status_label.setText("检测失败")
        QMessageBox.critical(
            self.main_window, "检测失败", f"检测过程中发生错误: {error_msg}")
        
        # 恢复按钮状态
        self.main_window.detect_button.setEnabled(True)
        self.main_window.progress_bar.setVisible(False)

    def on_ocr_progress(self, message: str):
        """OCR进度更新"""
        self.main_window.status_label.setText(message)

    def on_ocr_finished(self, results: DetectionResults):
        """OCR完成回调"""
        self.main_window.current_results = results
        
        # 更新显示（现在包含OCR文本）
        self.main_window.image_viewer.set_result_image(results.result_image)
        self.main_window.image_viewer.set_detection_regions(results.text_regions)
        
        # 更新状态信息
        ocr_time = results.ocr_time
        total_text_length = sum(len(text) for text in results.ocr_results.values())
        self.main_window.statusBar().showMessage(
            f"OCR完成: 识别了 {total_text_length} 个字符, 耗时 {ocr_time:.2f}s")
        self.main_window.status_label.setText(f"OCR完成: {total_text_length} 个字符")
        
        self.main_window.parameter_panel.update_ocr_results(results)
        
        # 恢复按钮状态
        self.main_window.detect_button.setEnabled(True)
        self.main_window.ocr_button.setEnabled(True)
        self.main_window.save_button.setEnabled(True)
        self.main_window.progress_bar.setVisible(False)

    def on_ocr_error(self, error_msg: str):
        """OCR错误回调"""
        self.main_window.statusBar().showMessage("OCR识别失败")
        self.main_window.status_label.setText("OCR失败")
        QMessageBox.critical(
            self.main_window, "OCR失败", f"OCR过程中发生错误: {error_msg}")
        
        # 恢复按钮状态
        self.main_window.detect_button.setEnabled(True)
        self.main_window.ocr_button.setEnabled(True)
        self.main_window.save_button.setEnabled(True)
        self.main_window.progress_bar.setVisible(False)

    def on_batch_progress(self, current, total, message):
        """批量处理进度回调"""
        self.main_window.progress_bar.setValue(current)
        self.main_window.statusBar().showMessage(
            f"批量处理进度: {current}/{total} - {message}")
        self.main_window.status_label.setText(f"处理中: {current}/{total}")

    def on_batch_finished(self, project_results: ProjectResults):
        """批量处理完成回调 - 适配新的ProjectResults"""
        total_files = len(project_results.detection_results)
        successful = sum(1 for result in project_results.detection_results if len(result.text_regions) > 0)
        
        self.main_window.statusBar().showMessage(f"批量处理完成: {successful}/{total_files} 成功")
        self.main_window.status_label.setText(f"批量完成: {successful}/{total_files}")
        
        # 获取项目统计信息
        project_stats = project_results.get_project_detection_results()['stats']
        
        # 计算输出路径（用于显示）
        if self.main_window.current_project_folder:
            input_folder = Path(self.main_window.current_project_folder)
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
        
        QMessageBox.information(self.main_window, "批量处理完成", completion_msg)
        
        # 恢复控件状态
        self.main_window.detect_button.setEnabled(True)
        self.main_window.ocr_button.setEnabled(self.main_window.current_results is not None)
        self.main_window.save_button.setEnabled(self.main_window.current_results is not None)
        self.main_window.progress_bar.setVisible(False)

    def on_batch_error(self, error_msg: str):
        """批量处理错误回调"""
        self.main_window.statusBar().showMessage("批量处理失败")
        self.main_window.status_label.setText("批量处理失败")
        QMessageBox.critical(
            self.main_window, "批量处理失败", f"处理过程中发生错误: {error_msg}")
        
        # 恢复控件状态
        self.main_window.detect_button.setEnabled(True)
        self.main_window.ocr_button.setEnabled(self.main_window.current_results is not None)
        self.main_window.save_button.setEnabled(self.main_window.current_results is not None)
        self.main_window.progress_bar.setVisible(False)

    # 视图切换处理
    def handle_toggle_regions(self):
        """切换检测区域显示"""
        self.main_window.image_viewer.toggle_regions()
        self.main_window.menu_manager.update_toggle_actions_text(
            self.main_window.image_viewer.show_regions,
            self.main_window.image_viewer.show_lines,
            self.main_window.image_viewer.show_blocks
        )

    def handle_toggle_lines(self):
        """切换文本行显示"""
        self.main_window.image_viewer.toggle_lines()
        self.main_window.menu_manager.update_toggle_actions_text(
            self.main_window.image_viewer.show_regions,
            self.main_window.image_viewer.show_lines,
            self.main_window.image_viewer.show_blocks
        )

    def handle_toggle_blocks(self):
        """切换文本块显示"""
        self.main_window.image_viewer.toggle_blocks()
        self.main_window.menu_manager.update_toggle_actions_text(
            self.main_window.image_viewer.show_regions,
            self.main_window.image_viewer.show_lines,
            self.main_window.image_viewer.show_blocks
        )

    def handle_show_about(self):
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
        QMessageBox.about(self.main_window, "关于", about_text)

    # 辅助方法
    def add_recent_folder(self, folder_path: str):
        """添加到最近项目文件夹"""
        if folder_path in self.main_window.recent_files:
            self.main_window.recent_files.remove(folder_path)
        
        self.main_window.recent_files.insert(0, folder_path)
        
        # 限制最近文件数量
        max_recent = self.main_window.config.gui_params.get('recent_files_count', 10)
        if len(self.main_window.recent_files) > max_recent:
            self.main_window.recent_files = self.main_window.recent_files[:max_recent]
        
        # 更新菜单
        self.main_window.menu_manager.update_recent_menu(
            self.main_window.recent_files, self.load_project_folder)

    def load_settings(self):
        """加载设置"""
        settings = QSettings("ComicTextDetector", "MainWindow")
        
        # 恢复窗口几何
        geometry = settings.value("geometry")
        if geometry:
            self.main_window.restoreGeometry(geometry)
        
        # 恢复最近文件
        recent_files = settings.value("recent_files", [])
        if isinstance(recent_files, list):
            self.main_window.recent_files = recent_files
            self.main_window.menu_manager.update_recent_menu(
                self.main_window.recent_files, self.load_project_folder)
    
    def save_settings(self):
        """保存设置"""
        settings = QSettings("ComicTextDetector", "MainWindow")
        settings.setValue("geometry", self.main_window.saveGeometry())
        settings.setValue("recent_files", self.main_window.recent_files)