"""
检测结果管理模块
"""

import time
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Union

from utils.io_utils import imwrite, NumpyEncoder
from utils.textblock import TextBlock


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
        """保存整个项目的结果到指定目录（兼容方法，建议使用新的增量方法）"""
        # 创建项目结构
        self.create_project_structure(base_output_dir, output_params)
        
        # 保存所有结果
        for result in self.detection_results:
            self.update_image_detection_result(result, output_params)
            if result.has_ocr_results:
                self.update_image_ocr_result(result)
        
        # 完成项目
        self.finalize_project()
        
        return self.project_dir

    def create_project_structure(self, base_output_dir: Union[str, Path], output_params: Dict[str, Any]):
        """提前创建项目结构和初始json文件"""
        base_output_dir = Path(base_output_dir)
        self.project_dir = base_output_dir / self.project_name
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子文件夹
        if output_params.get('save_image', True):
            self.result_images_dir = self.project_dir / "result_images"
            self.result_images_dir.mkdir(exist_ok=True)
        
        if output_params.get('save_mask', True):
            self.masks_dir = self.project_dir / "masks"
            self.masks_dir.mkdir(exist_ok=True)
        
        # 创建初始的合并json文件
        if output_params.get('save_json', True):
            self.json_file_path = self.project_dir / "results.json"
            initial_data = {
                "project_name": self.project_name,
                "total_images": len(self.detection_results) if self.detection_results else 0,
                "processing_time": 0.0,
                "created_at": time.strftime('%Y-%m-%d %H:%M:%S'),
                "status": "processing",
                "images": [],
                "stats": {
                    "total_regions": 0,
                    "images_with_ocr": 0,
                    "avg_regions_per_image": 0,
                    "total_detection_time": 0,
                    "total_ocr_time": 0,
                    "languages_detected": []
                }
            }
            
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
        
        print(f"项目结构已创建: {self.project_dir}")
        return self.project_dir

    def update_image_detection_result(self, result: DetectionResults, output_params: Dict[str, Any]):
        """更新单个图片的检测结果到json文件"""
        if not hasattr(self, 'json_file_path') or not self.json_file_path.exists():
            return
        
        # 保存图片和掩码文件
        base_name = result.image_name
        
        if output_params.get('save_image', True) and result.result_image is not None:
            result_path = self.result_images_dir / f"{base_name}_result.{output_params.get('image_format', 'jpg')}"
            imwrite(str(result_path), result.result_image)
        
        if output_params.get('save_mask', True) and result.refined_mask is not None:
            mask_path = self.masks_dir / f"{base_name}_mask.{output_params.get('mask_format', 'png')}"
            imwrite(str(mask_path), result.refined_mask)
        
        # 读取现有json
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 构建图片检测结果
        image_data = {
            "image_name": result.image_name,
            "image_path": result.image_path,
            "detection_results": {
                "text_regions_count": len(result.text_regions),
                "detection_time": result.detection_time,
                "languages": list(set(r.get('language', 'unknown') for r in result.text_regions)),
                "avg_confidence": np.mean([r.get('confidence', 0) for r in result.text_regions]) if result.text_regions else 0,
                "text_regions": result.text_regions
            },
            "ocr_results": None  # 初始为None，后续OCR时更新
        }
        
        # 查找是否已存在该图片的数据
        existing_index = None
        for i, img in enumerate(data["images"]):
            if img["image_name"] == result.image_name:
                existing_index = i
                break
        
        if existing_index is not None:
            # 更新现有数据，保留OCR结果
            data["images"][existing_index]["detection_results"] = image_data["detection_results"]
        else:
            # 添加新数据
            data["images"].append(image_data)
        
        # 更新统计信息
        self._update_stats(data)
        
        # 写回文件
        with open(self.json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)

    def update_image_ocr_result(self, result: DetectionResults):
        """更新单个图片的OCR结果到json文件"""
        if not hasattr(self, 'json_file_path') or not self.json_file_path.exists():
            return
        
        if not result.has_ocr_results:
            return
        
        # 读取现有json
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 查找对应图片数据
        for img_data in data["images"]:
            if img_data["image_name"] == result.image_name:
                # 构建OCR结果，格式化为区域形式
                ocr_regions = {}
                for region_key, text in result.ocr_results.items():
                    if text.strip():
                        if region_key.startswith("region_"):
                            region_num = region_key.split("_")[1]
                            display_key = f"区域{region_num}"
                        else:
                            display_key = region_key
                        ocr_regions[display_key] = text.strip()
                
                img_data["ocr_results"] = {
                    "ocr_time": result.ocr_time,
                    "has_ocr": True,
                    "avg_ocr_confidence": np.mean([r.get('ocr_confidence', 0) for r in result.text_regions if 'ocr_confidence' in r]) if result.text_regions else 0,
                    "regions": ocr_regions
                }
                break
        
        # 更新统计信息
        self._update_stats(data)
        
        # 写回文件
        with open(self.json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)

    def _update_stats(self, data):
        """更新统计信息"""
        total_regions = sum(img["detection_results"]["text_regions_count"] for img in data["images"] if img["detection_results"])
        images_with_ocr = sum(1 for img in data["images"] if img["ocr_results"] and img["ocr_results"]["has_ocr"])
        total_detection_time = sum(img["detection_results"]["detection_time"] for img in data["images"] if img["detection_results"])
        total_ocr_time = sum(img["ocr_results"]["ocr_time"] for img in data["images"] if img["ocr_results"] and img["ocr_results"]["has_ocr"])
        
        all_languages = set()
        for img in data["images"]:
            if img["detection_results"]:
                all_languages.update(img["detection_results"]["languages"])
        
        data["stats"].update({
            "total_regions": total_regions,
            "images_with_ocr": images_with_ocr,
            "avg_regions_per_image": total_regions / len(data["images"]) if data["images"] else 0,
            "total_detection_time": total_detection_time,
            "total_ocr_time": total_ocr_time,
            "languages_detected": list(all_languages)
        })

    def finalize_project(self):
        """完成项目处理，更新最终状态"""
        if not hasattr(self, 'json_file_path') or not self.json_file_path.exists():
            return
        
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data["status"] = "completed"
        data["processing_time"] = time.time() - self.processing_start_time
        
        with open(self.json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
        
        print(f"项目处理完成: {self.project_dir}")