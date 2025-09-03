"""
工作线程类 - 处理检测、OCR和批量处理
"""

from typing import List
from PyQt5.QtCore import QThread, pyqtSignal

from core.detector import ComicTextDetector, DetectionResults, ProjectResults


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