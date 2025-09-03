"""
检测结果管理模块
"""

import time
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Union

from src.utils.io_utils import imwrite, NumpyEncoder
from src.utils.textblock import TextBlock


class DetectionResults:
    """检测结果类"""
    
    def __init__(self, image_path: str, original_image: np.ndarray):
        self.image_path = image_path
        self.original_image = original_image
        self.image_name = Path(image_path).stem
        
        # 检测结果
        self.text_regions: List[Dict] = []
        self.text_blocks: List[TextBlock] = []
        self.text_mask: np.ndarray = None
        self.refined_mask: np.ndarray = None
        self.result_image: np.ndarray = None
        
        # OCR结果
        self.ocr_results: Dict[str, str] = {}
        self.has_ocr_results: bool = False
        
        # 元数据
        self.detection_time: float = 0.0
        self.ocr_time: float = 0.0
        self.model_info: Dict[str, Any] = {}
        self.parameters: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'image_path': self.image_path,
            'image_name': self.image_name,
            'text_regions': self.text_regions,
            'ocr_results': self.ocr_results,
            'has_ocr_results': self.has_ocr_results,
            'detection_time': self.detection_time,
            'ocr_time': self.ocr_time,
            'model_info': self.model_info,
            'parameters': self.parameters,
            'stats': {
                'total_regions': len(self.text_regions),
                'languages': list(set(r.get('language', 'unknown') for r in self.text_regions)),
                'avg_confidence': np.mean([r.get('confidence', 0) for r in self.text_regions]) if self.text_regions else 0,
                'avg_ocr_confidence': np.mean([r.get('ocr_confidence', 0) for r in self.text_regions if 'ocr_confidence' in r]) if self.text_regions else 0
            }
        }


class ProjectResults:
    """项目结果管理器"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.detection_results: List[DetectionResults] = []
        self.processing_start_time = time.time()
        self.total_processing_time = 0.0
    
    def add_result(self, result: DetectionResults):
        """添加单个检测结果"""
        self.detection_results.append(result)
    
    def get_project_ocr_results(self) -> Dict[str, Dict[str, str]]:
        """获取整个项目的OCR结果 - 按区域分组格式"""
        project_ocr = {}
        for result in self.detection_results:
            if result.has_ocr_results and result.ocr_results:
                # 保持区域分离的格式
                image_ocr = {}
                for region_key, text in result.ocr_results.items():
                    if text.strip():  # 只保存非空文本
                        # 将 region_0 格式转换为 区域0 格式
                        if region_key.startswith("region_"):
                            region_num = region_key.split("_")[1]
                            display_key = f"区域{region_num}"
                        else:
                            display_key = region_key
                        
                        image_ocr[display_key] = text.strip()
                
                project_ocr[result.image_name] = image_ocr
            else:
                # 没有OCR结果的图片设为空字典
                project_ocr[result.image_name] = {}
        
        return project_ocr

    def get_project_detection_results(self) -> Dict[str, Any]:
        """获取整个项目的检测结果摘要"""
        project_results = {
            'project_name': self.project_name,
            'total_images': len(self.detection_results),
            'processing_time': self.total_processing_time,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'images': []
        }
        
        for result in self.detection_results:
            image_summary = {
                'image_name': result.image_name,
                'image_path': result.image_path,
                'text_regions_count': len(result.text_regions),
                'detection_time': result.detection_time,
                'ocr_time': result.ocr_time,
                'has_ocr': result.has_ocr_results,
                'languages': list(set(r.get('language', 'unknown') for r in result.text_regions)),
                'avg_confidence': np.mean([r.get('confidence', 0) for r in result.text_regions]) if result.text_regions else 0
            }
            project_results['images'].append(image_summary)
        
        # 计算项目统计信息
        project_results['stats'] = {
            'total_regions': sum(len(r.text_regions) for r in self.detection_results),
            'images_with_ocr': sum(1 for r in self.detection_results if r.has_ocr_results),
            'avg_regions_per_image': np.mean([len(r.text_regions) for r in self.detection_results]) if self.detection_results else 0,
            'total_detection_time': sum(r.detection_time for r in self.detection_results),
            'total_ocr_time': sum(r.ocr_time for r in self.detection_results),
            'languages_detected': list(set(lang for r in self.detection_results for region in r.text_regions for lang in [region.get('language', 'unknown')]))
        }
        
        return project_results
    
    def save_to_directory(self, base_output_dir: Union[str, Path], output_params: Dict[str, Any]):
        """保存整个项目的结果到指定目录"""
        base_output_dir = Path(base_output_dir)
        project_dir = base_output_dir / self.project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子文件夹
        if output_params.get('save_image', True):
            result_images_dir = project_dir / "result_images"
            result_images_dir.mkdir(exist_ok=True)
        
        if output_params.get('save_mask', True):
            masks_dir = project_dir / "masks"
            masks_dir.mkdir(exist_ok=True)
        
        saved_files = []
        
        # 保存每张图片的结果
        for result in self.detection_results:
            base_name = result.image_name
            
            # 保存结果图片
            if output_params.get('save_image', True) and result.result_image is not None:
                result_path = result_images_dir / f"{base_name}_result.{output_params.get('image_format', 'jpg')}"
                imwrite(str(result_path), result.result_image)
                saved_files.append(str(result_path))
            
            # 保存掩码
            if output_params.get('save_mask', True) and result.refined_mask is not None:
                mask_path = masks_dir / f"{base_name}_mask.{output_params.get('mask_format', 'png')}"
                imwrite(str(mask_path), result.refined_mask)
                saved_files.append(str(mask_path))
        
        # 保存项目级别的JSON结果
        if output_params.get('save_json', True):
            # 保存检测结果摘要
            project_results = self.get_project_detection_results()
            result_json_path = project_dir / "detection_results.json"
            with open(result_json_path, 'w', encoding='utf-8') as f:
                json.dump(project_results, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
            saved_files.append(str(result_json_path))

            # 保存OCR结果（如果有）
            project_ocr = self.get_project_ocr_results()
            # 检查是否有任何图片包含OCR文本
            has_ocr_results = any(
                any(text.strip() for text in image_regions.values()) 
                for image_regions in project_ocr.values() 
                if image_regions
            )

            if has_ocr_results:
                ocr_json_path = project_dir / "ocr_results.json"
                with open(ocr_json_path, 'w', encoding='utf-8') as f:
                    json.dump(project_ocr, f, ensure_ascii=False, indent=2)
                saved_files.append(str(ocr_json_path))           
        
        self.total_processing_time = time.time() - self.processing_start_time
        
        print(f"\n项目 '{self.project_name}' 处理完成:")
        print(f"- 处理图片数: {len(self.detection_results)}")
        print(f"- 总处理时间: {self.total_processing_time:.2f}s")
        print(f"- 输出目录: {project_dir}")
        print(f"- 保存文件数: {len(saved_files)}")
        
        return project_dir