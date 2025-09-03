"""
事件处理器 - 优化版，支持自动加载已有结果
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
    """事件处理器类 - 优化版"""
    
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
        """【优化】加载项目文件夹 - 支持自动检测和加载已有结果"""
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

            project_name = "results"
            
            # 【新增】尝试从已有results.json加载项目结果
            existing_project_results = ProjectResults.load_from_existing_json(folder_path, image_files)
            self.main_window.current_project_results = existing_project_results
            
            # 【新增】检查处理状态并显示信息
            status = existing_project_results.get_processing_status(image_files)
            
            if status['is_loaded_from_existing']:
                # 显示加载状态信息
                status_msg = (
                    f"已加载现有结果！\n"
                    f"总图片: {status['total_images']}\n"
                    f"已处理: {status['processed_images']}\n"
                    f"含OCR: {status['images_with_ocr']}\n"
                    f"完成度: {status['completion_rate']:.1%}"
                )
                
                if status['is_fully_processed']:
                    status_msg += "\n\n✅ 所有图片都已处理完成！"
                    QMessageBox.information(self.main_window, "项目状态", status_msg)
                else:
                    unprocessed_count = len(status['unprocessed_images'])
                    status_msg += f"\n\n⚠️ 还有 {unprocessed_count} 个图片未处理"
                    reply = QMessageBox.question(
                        self.main_window, "项目状态", 
                        status_msg + "\n\n是否继续处理未完成的图片？",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    # 用户选择取消时也会继续显示项目，只是不自动开始处理
            
            # 显示第一张图片
            self.main_window.image_viewer.load_image(image_files[0])
            self.main_window.current_image_path = image_files[0]
            
            # 【修改】加载OCR结果 - 使用项目内部路径
            input_folder = Path(folder_path)
            project_results_dir = input_folder / "results"
            first_image_name = Path(image_files[0]).stem
            
            self.main_window.parameter_panel.load_ocr_from_json(
                str(project_results_dir), first_image_name)
            
            # 【新增】如果有已有结果，尝试加载第一张图片的检测结果到显示
            self._load_existing_detection_for_current_image()
            
            # 更新按钮状态
            self.main_window.prev_button.setEnabled(False)
            self.main_window.next_button.setEnabled(len(image_files) > 1)
            self.main_window.detect_button.setEnabled(True)
            
            # 清空之前的结果（如果没有从现有数据加载）
            if not status['is_loaded_from_existing']:
                self.main_window.current_results = None
                self.main_window.ocr_button.setEnabled(False)
            
            # 更新最近文件夹
            self.add_recent_folder(folder_path)
            
            # 【优化】更新状态显示
            if status['is_loaded_from_existing']:
                status_text = f"项目已加载: {status['processed_images']}/{status['total_images']} 已处理"
                if status['is_fully_processed']:
                    status_text += " ✅"
                self.main_window.statusBar().showMessage(
                    f"项目已加载: {folder_path} ({status['processed_images']}/{status['total_images']} 已处理)")
                self.main_window.status_label.setText(status_text)
            else:
                self.main_window.statusBar().showMessage(f"项目已加载: {folder_path} ({len(image_files)} 个文件)")
                self.main_window.status_label.setText(f"已加载 {len(image_files)} 个文件")
            
        except Exception as e:
            QMessageBox.critical(self.main_window, "错误", f"无法加载项目文件夹: {e}")

    def _load_existing_detection_for_current_image(self):
        """【新增】为当前图片加载已有的检测结果（如果存在）"""
        if not self.main_window.current_project_results.is_loaded_from_existing:
            return
        
        current_image_name = Path(self.main_window.current_image_path).stem
        
        # 查找当前图片的检测结果
        for result in self.main_window.current_project_results.detection_results:
            if result.image_name == current_image_name:
                # 创建虚拟的检测结果对象用于显示
                from utils.io_utils import imread
                try:
                    original_image = imread(self.main_window.current_image_path)
                    if original_image is not None:
                        result.original_image = original_image
                        
                        # 生成可视化结果
                        if result.text_regions:
                            result_image = self._generate_visualization_for_loaded_result(original_image, result.text_regions)
                            result.result_image = result_image
                        
                        # 设置为当前结果
                        self.main_window.current_results = result
                        
                        # 更新显示
                        if result.result_image is not None:
                            self.main_window.image_viewer.set_result_image(result.result_image)
                        self.main_window.image_viewer.set_detection_regions(result.text_regions)
                        
                        # 更新OCR按钮状态
                        self.main_window.ocr_button.setEnabled(not result.has_ocr_results)
                        
                        print(f"已加载图片 {current_image_name} 的检测结果: {len(result.text_regions)} 个区域")
                        break
                except Exception as e:
                    print(f"加载图片检测结果时出错: {e}")

    def _generate_visualization_for_loaded_result(self, image, text_regions):
        """【新增】为加载的结果生成可视化图片"""
        import cv2
        import numpy as np
        
        result = image.copy()
        
        for region in text_regions:
            x1, y1, x2, y2 = region['bbox']
            
            # 根据置信度调整颜色
            confidence = region.get('confidence', 1.0)
            color_intensity = int(255 * min(confidence, 1.0))
            color = (0, color_intensity, 0)
            
            # 绘制边界框
            cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)
            
            # 标签包含OCR结果
            label = f"{region['id']}_{region.get('language', 'unknown')}"
            if region.get('vertical', False):
                label += "_V"
            label += f"_{confidence:.3f}"
            
            # 如果有OCR结果，显示部分文字
            if 'ocr_text' in region and region['ocr_text']:
                ocr_preview = region['ocr_text'][:10] + "..." if len(region['ocr_text']) > 10 else region['ocr_text']
                label += f"\n{ocr_preview}"
            
            # 绘制标签
            label_lines = label.split('\n')
            for i, line in enumerate(label_lines):
                label_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                y_offset = y1 - 25 + i * 20
                cv2.rectangle(result, (x1, y_offset-15), (x1+label_size[0], y_offset), color, -1)
                cv2.putText(result, line, (x1, y_offset-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return result

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
        """【优化】加载当前索引的图片 - 支持加载已有结果"""
        if not self.main_window.current_image_files:
            return
            
        current_image = self.main_window.current_image_files[self.main_window.current_image_index]
        self.main_window.image_viewer.load_image(current_image)
        self.main_window.current_image_path = current_image
        
        # 清空之前的结果
        self.main_window.current_results = None
        self.main_window.ocr_button.setEnabled(False)
        
        # 加载OCR结果到面板
        if self.main_window.current_project_folder:
            input_folder = Path(self.main_window.current_project_folder)
            project_results_dir = input_folder / "results"
            image_name = Path(current_image).stem
            
            self.main_window.parameter_panel.load_ocr_from_json(
                str(project_results_dir), image_name)
        else:
            self.main_window.parameter_panel.clear_ocr_results()
        
        # 【新增】尝试加载已有的检测结果
        self._load_existing_detection_for_current_image()
        
        # 更新按钮状态
        self.main_window.prev_button.setEnabled(self.main_window.current_image_index > 0)
        self.main_window.next_button.setEnabled(
            self.main_window.current_image_index < len(self.main_window.current_image_files) - 1)
        
        # 更新状态显示
        image_name = Path(current_image).name
        total_count = len(self.main_window.current_image_files)
        
        # 【新增】显示处理状态
        status_suffix = ""
        if (self.main_window.current_project_results and 
            self.main_window.current_project_results.is_loaded_from_existing):
            current_name = Path(current_image).stem
            if current_name in self.main_window.current_project_results.loaded_image_names:
                status_suffix = " ✅"
        
        self.main_window.statusBar().showMessage(
            f"图片: {image_name} ({self.main_window.current_image_index + 1}/{total_count}){status_suffix}")
        self.main_window.status_label.setText(
            f"图片 {self.main_window.current_image_index + 1}/{total_count}: {image_name}{status_suffix}")

    def handle_start_detection(self):
        """开始文字检测"""
        if not self.main_window.current_image_path or not self.main_window.detector:
            QMessageBox.information(self.main_window, "提示", "请先选择图片并确保检测器已加载")
            return
        
        # 【新增】检查是否已经处理过
        if (self.main_window.current_project_results and 
            self.main_window.current_project_results.is_loaded_from_existing):
            current_name = Path(self.main_window.current_image_path).stem
            if current_name in self.main_window.current_project_results.loaded_image_names:
                reply = QMessageBox.question(
                    self.main_window, "确认重新检测", 
                    "该图片已有检测结果，是否重新检测？\n（这将覆盖现有结果）",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
        
        # 更新检测器参数
        params = self.main_window.parameter_panel.get_parameters()
        self.main_window.detector.update_parameters(**params)
        
        # 禁用按钮
        self.main_window.detect_button.setEnabled(False)
        self.main_window.ocr_button.setEnabled(False)
        
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

    def handle_batch_detection(self):
        """开始批量检测（不含OCR）"""
        self._start_batch_processing(include_ocr=False)

    def handle_batch_ocr(self):
        """开始批量处理（含OCR）"""
        self._start_batch_processing(include_ocr=True)

    def _start_batch_processing(self, include_ocr: bool = True):
        """【优化】开始批量处理 - 支持跳过已处理的图片"""
        if (not self.main_window.current_image_files or 
            not self.main_window.detector):
            QMessageBox.information(
                self.main_window, "提示", "请先选择项目文件夹并确保检测器已加载")
            return
        
        if not self.main_window.current_project_folder:
            QMessageBox.warning(self.main_window, "错误", "当前没有选择项目文件夹")
            return
        
        # 【新增】智能处理：只处理未完成的图片
        if (self.main_window.current_project_results and 
            self.main_window.current_project_results.is_loaded_from_existing):
            
            unprocessed_files = self.main_window.current_project_results.get_unprocessed_image_files(
                self.main_window.current_image_files)
            
            # 如果需要OCR，还要检查哪些图片没有OCR结果
            if include_ocr:
                files_needing_ocr = []
                for img_file in self.main_window.current_image_files:
                    img_name = Path(img_file).stem
                    
                    # 查找对应的检测结果
                    found_result = None
                    for result in self.main_window.current_project_results.detection_results:
                        if result.image_name == img_name:
                            found_result = result
                            break
                    
                    # 如果没有检测结果或没有OCR结果，需要处理
                    if found_result is None or not found_result.has_ocr_results:
                        files_needing_ocr.append(img_file)
                
                processing_files = files_needing_ocr
                operation_description = "批量处理（含OCR）"
            else:
                processing_files = unprocessed_files
                operation_description = "批量检测"
            
            if not processing_files:
                QMessageBox.information(
                    self.main_window, "处理完成", 
                    f"所有图片都已完成{operation_description}！")
                return
            
            # 确认处理
            reply = QMessageBox.question(
                self.main_window, "确认批量处理",
                f"找到 {len(processing_files)} 个图片需要{operation_description}\n"
                f"（跳过 {len(self.main_window.current_image_files) - len(processing_files)} 个已处理的图片）\n\n"
                f"是否开始处理？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        else:
            processing_files = self.main_window.current_image_files
        
        # 输出路径
        input_folder = Path(self.main_window.current_project_folder)
        project_name = "results"
        output_dir = str(input_folder)
        
        # 创建或使用现有的项目结果对象
        if not self.main_window.current_project_results:
            self.main_window.current_project_results = ProjectResults(project_name)
        
        try:
            self.main_window.current_project_results.create_project_structure(
                output_dir, self.main_window.config.output_params)
        except Exception as e:
            QMessageBox.warning(self.main_window, "错误", f"创建项目结构失败：{e}")
            return
        
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
        self.main_window.progress_bar.setRange(0, len(processing_files))
        
        # 禁用控件
        self.main_window.detect_button.setEnabled(False)
        self.main_window.ocr_button.setEnabled(False)
        
        operation_name = "批量处理（含OCR）" if include_ocr else "批量检测"
        self.main_window.status_label.setText(f"正在{operation_name}...")
        
        # 显示处理信息
        if len(processing_files) < len(self.main_window.current_image_files):
            skip_count = len(self.main_window.current_image_files) - len(processing_files)
            self.main_window.statusBar().showMessage(
                f"开始{operation_name} -> 处理 {len(processing_files)} 个图片（跳过 {skip_count} 个已处理）")
        else:
            self.main_window.statusBar().showMessage(
                f"开始{operation_name} -> 输出到: {Path(output_dir) / project_name}")
        
        # 启动批量处理线程
        from ui.workers import BatchProcessWorker
        self.main_window.batch_worker = BatchProcessWorker(
            self.main_window.detector, 
            processing_files,  # 【修改】只处理需要处理的文件
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
        
        # 如果在项目模式下，立即保存检测结果
        if (self.main_window.current_project_folder and 
            self.main_window.current_project_results is not None):
            self.main_window.current_project_results.update_image_detection_result(
                results, self.main_window.config.output_params)
            
            # 【新增】更新已处理图片集合
            self.main_window.current_project_results.loaded_image_names.add(results.image_name)
        
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
        
        # 如果在项目模式下，立即保存OCR结果
        if (self.main_window.current_project_folder and 
            self.main_window.current_project_results is not None):
            self.main_window.current_project_results.update_image_ocr_result(results)
        
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
        
        self.main_window.progress_bar.setVisible(False)

    def on_batch_progress(self, current, total, message):
        """批量处理进度回调"""
        self.main_window.progress_bar.setValue(current)
        self.main_window.statusBar().showMessage(
            f"批量处理进度: {current}/{total} - {message}")
        self.main_window.status_label.setText(f"处理中: {current}/{total}")

    def on_batch_finished(self, project_results: ProjectResults):
        """【优化】批量处理完成回调 - 显示增量处理信息"""
        total_files = len(project_results.detection_results)
        successful = sum(1 for result in project_results.detection_results if len(result.text_regions) > 0)
        
        self.main_window.statusBar().showMessage(f"批量处理完成: {successful}/{total_files} 成功")
        self.main_window.status_label.setText(f"批量完成: {successful}/{total_files}")
        
        # 【新增】合并结果到主项目结果中
        if self.main_window.current_project_results:
            # 将新处理的结果合并到现有项目中
            for new_result in project_results.detection_results:
                # 检查是否已存在，如果存在则更新，否则添加
                existing_found = False
                for i, existing_result in enumerate(self.main_window.current_project_results.detection_results):
                    if existing_result.image_name == new_result.image_name:
                        # 更新现有结果
                        self.main_window.current_project_results.detection_results[i] = new_result
                        existing_found = True
                        break
                
                if not existing_found:
                    # 添加新结果
                    self.main_window.current_project_results.add_result(new_result)
                
                # 更新已处理集合
                self.main_window.current_project_results.loaded_image_names.add(new_result.image_name)
        
        # 获取完整项目统计信息
        if self.main_window.current_project_results:
            all_status = self.main_window.current_project_results.get_processing_status(
                self.main_window.current_image_files)
            project_stats = self.main_window.current_project_results.get_project_detection_results()['stats']
        else:
            project_stats = project_results.get_project_detection_results()['stats']
            all_status = {'processed_images': total_files, 'images_with_ocr': project_stats['images_with_ocr']}
        
        # 计算输出路径
        if self.main_window.current_project_folder:
            input_folder = Path(self.main_window.current_project_folder)
            expected_output_path = input_folder / "results"
        else:
            expected_output_path = "未知路径"
        
        completion_msg = f"批量处理完成！\n\n"
        completion_msg += f"本次处理: {successful}/{total_files} 成功\n"
        completion_msg += f"项目总计: {all_status['processed_images']}/{len(self.main_window.current_image_files)} 已处理\n"
        completion_msg += f"OCR总计: {all_status['images_with_ocr']} 个图片\n"
        completion_msg += f"输出路径: {expected_output_path}\n\n"
        completion_msg += f"处理统计:\n"
        completion_msg += f"• 总文字区域: {project_stats['total_regions']}\n"
        completion_msg += f"• 总处理时间: {project_stats['total_detection_time']:.1f}s\n"
        
        if project_stats['total_ocr_time'] > 0:
            completion_msg += f"• OCR总时间: {project_stats['total_ocr_time']:.1f}s\n"
        
        completion_msg += f"\n✅ 结果已保存到项目文件夹内部！"
        
        QMessageBox.information(self.main_window, "批量处理完成", completion_msg)
        
        # 恢复控件状态
        self.main_window.detect_button.setEnabled(True)
        self.main_window.ocr_button.setEnabled(self.main_window.current_results is not None)
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
        <h3>漫画文本检测器 v1.0 (智能加载优化版)</h3>
        <p>基于深度学习的漫画文本检测工具</p>
        <p><b>特性:</b></p>
        <ul>
        <li>支持中文和日文文本检测</li>
        <li>高精度的文本区域定位</li>
        <li>分离的检测和OCR流程</li>
        <li>可视化文本块和文本行预览</li>
        <li>友好的图形用户界面</li>
        <li>可配置的检测参数</li>
        <li>智能加载已有结果，避免重复处理</li>
        <li>增量批量处理，只处理未完成的图片</li>
        </ul>
        <p><b>智能处理特性:</b></p>
        <p>• 自动检测项目文件夹中的results.json<br>
        • 加载已有的检测和OCR结果<br>
        • 显示处理进度和完成状态<br>
        • 批量处理时跳过已完成的图片<br>
        • 支持增量更新和部分重新处理</p>
        <p><b>项目输出结构:</b></p>
        <p>• 输出到项目文件夹内部/results/<br>
        • result_images/ - 检测结果图片<br>
        • masks/ - 文字掩码<br>
        • results.json - 检测和OCR结果</p>
        <p><b>使用流程:</b></p>
        <p>1. 打开项目文件夹（自动加载已有结果）<br>
        2. 查看处理状态和完成度<br>
        3. 对单个图片：检测 → OCR识别<br>
        4. 批量处理：自动跳过已完成的图片</p>
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