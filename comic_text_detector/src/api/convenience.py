"""
便捷函数和API接口
"""

from typing import List, Optional, Union
from pathlib import Path

from src.core.detector import ComicTextDetector
from src.core.results import DetectionResults, ProjectResults


def quick_detect_only(image_path: Union[str, Path], 
                     model_path: Optional[str] = None,
                     output_dir: Optional[str] = None,
                     **kwargs) -> DetectionResults:
    """
    快速检测函数（仅检测，不OCR）
    
    Args:
        image_path: 图片路径
        model_path: 模型路径
        output_dir: 输出目录
        **kwargs: 检测参数
        
    Returns:
        DetectionResults: 检测结果
    """
    detector = ComicTextDetector(model_path=model_path, enable_ocr=False, **kwargs)
    results = detector.detect_only(image_path)
    
    if output_dir:
        detector.save_results(results, output_dir)
    
    return results


def batch_process_project(image_files: List[str], 
                         project_name: str,
                         output_dir: str,
                         model_path: Optional[str] = None,
                         include_ocr: bool = True,
                         **kwargs) -> ProjectResults:
    """
    批量处理项目的便捷函数
    
    Args:
        image_files: 图片文件列表
        project_name: 项目名称
        output_dir: 输出目录
        model_path: 模型路径
        include_ocr: 是否包含OCR
        **kwargs: 其他检测参数
        
    Returns:
        ProjectResults: 项目结果对象
    """
    detector = ComicTextDetector(model_path=model_path, enable_ocr=include_ocr, **kwargs)
    return detector.batch_process_project(image_files, project_name, output_dir, include_ocr)