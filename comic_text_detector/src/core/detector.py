"""
核心检测器类 - 整合文本检测功能
"""

import cv2
import json
import numpy as np
import torch
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union

from src.core.inference import TextDetector
from src.utils.textmask import refine_mask, refine_undetected_mask, REFINEMASK_ANNOTATION
from src.utils.io_utils import imread, imwrite, NumpyEncoder
from src.utils.textblock import TextBlock, visualize_textblocks
from config.config import Config

# 在 import 部分后添加以下函数

def calculate_iou(box1, box2):
    """计算两个框的IoU"""
    x1, y1, x2, y2 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    # 计算交集
    inter_x1 = max(x1, x1_2)
    inter_y1 = max(y1, y1_2)
    inter_x2 = min(x2, x2_2)
    inter_y2 = min(y2, y2_2)
    
    if inter_x1 >= inter_x2 or inter_y1 >= inter_y2:
        return 0.0
    
    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    
    # 计算并集
    area1 = (x2 - x1) * (y2 - y1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union_area = area1 + area2 - inter_area
    
    return inter_area / union_area if union_area > 0 else 0.0

def calculate_containment_ratio(box_small, box_large):
    """计算小框在大框中的包含比例"""
    x1, y1, x2, y2 = box_small
    x1_2, y1_2, x2_2, y2_2 = box_large
    
    # 计算交集
    inter_x1 = max(x1, x1_2)
    inter_y1 = max(y1, y1_2)
    inter_x2 = min(x2, x2_2)
    inter_y2 = min(y2, y2_2)
    
    if inter_x1 >= inter_x2 or inter_y1 >= inter_y2:
        return 0.0
    
    inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
    small_area = (x2 - x1) * (y2 - y1)
    
    return inter_area / small_area if small_area > 0 else 0.0

def merge_boxes(box1, box2):
    """合并两个框，返回包含它们的最小框"""
    x1, y1, x2, y2 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    return [
        min(x1, x1_2),
        min(y1, y1_2),
        max(x2, x2_2),
        max(y2, y2_2)
    ]

def filter_and_merge_boxes(text_regions, config_params):
    """过滤和合并检测框"""
    if not config_params.get('enable_box_filter', True):
        return text_regions
    
    min_box_size = config_params.get('min_box_size', 10)
    iou_merge_thresh = config_params.get('iou_merge_thresh', 0.3)
    containment_thresh = config_params.get('containment_thresh', 0.8)
    
    # 1. 过滤小框
    filtered_regions = []
    for region in text_regions:
        x1, y1, x2, y2 = region['bbox']
        width = x2 - x1
        height = y2 - y1
        if width >= min_box_size and height >= min_box_size:
            filtered_regions.append(region)
    
    if len(filtered_regions) <= 1:
        return filtered_regions
    
    # 2. 处理包含关系 - 移除被完全包含的框
    to_remove = set()
    for i in range(len(filtered_regions)):
        if i in to_remove:
            continue
        for j in range(len(filtered_regions)):
            if i == j or j in to_remove:
                continue
            
            box_i = filtered_regions[i]['bbox']
            box_j = filtered_regions[j]['bbox']
            
            # 检查i是否完全包含在j中
            containment_i_in_j = calculate_containment_ratio(box_i, box_j)
            if containment_i_in_j > containment_thresh:
                to_remove.add(i)
                print(f"移除被包含的框 {i}: 包含比例 {containment_i_in_j:.3f}")
                break
    
    # 移除被包含的框
    filtered_regions = [region for i, region in enumerate(filtered_regions) if i not in to_remove]
    
    # 3. 处理部分重叠 - 合并重叠的框
    merged = True
    while merged and len(filtered_regions) > 1:
        merged = False
        new_regions = []
        used = set()
        
        for i in range(len(filtered_regions)):
            if i in used:
                continue
            
            current_region = filtered_regions[i]
            merged_with = []
            
            for j in range(i + 1, len(filtered_regions)):
                if j in used:
                    continue
                
                iou = calculate_iou(current_region['bbox'], filtered_regions[j]['bbox'])
                if iou > iou_merge_thresh:
                    merged_with.append(j)
                    used.add(j)
                    merged = True
            
            if merged_with:
                # 合并框
                merged_bbox = current_region['bbox']
                merged_confidence = current_region['confidence']
                merged_languages = [current_region['language']]
                
                for idx in merged_with:
                    merged_bbox = merge_boxes(merged_bbox, filtered_regions[idx]['bbox'])
                    merged_confidence = max(merged_confidence, filtered_regions[idx]['confidence'])
                    if filtered_regions[idx]['language'] not in merged_languages:
                        merged_languages.append(filtered_regions[idx]['language'])
                
                # 创建合并后的区域
                merged_region = current_region.copy()
                merged_region['bbox'] = merged_bbox
                merged_region['confidence'] = merged_confidence
                merged_region['language'] = merged_languages[0] if len(merged_languages) == 1 else 'mixed'
                merged_region['id'] = len(new_regions)
                
                new_regions.append(merged_region)
                print(f"合并框: {[i] + merged_with} -> 新框 {len(new_regions)-1}")
            else:
                current_region['id'] = len(new_regions)
                new_regions.append(current_region)
            
            used.add(i)
        
        filtered_regions = new_regions
    
    return filtered_regions


class DetectionResults:
    """检测结果类"""
    
    def __init__(self, image_path: str, original_image: np.ndarray):
        self.image_path = image_path
        self.original_image = original_image
        self.image_name = Path(image_path).stem
        
        # 检测结果
        self.text_regions: List[Dict] = []
        self.text_blocks: List[TextBlock] = []
        self.text_mask: Optional[np.ndarray] = None
        self.refined_mask: Optional[np.ndarray] = None
        self.result_image: Optional[np.ndarray] = None
        
        # 元数据
        self.detection_time: float = 0.0
        self.model_info: Dict[str, Any] = {}
        self.parameters: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'image_path': self.image_path,
            'image_name': self.image_name,
            'text_regions': self.text_regions,
            'detection_time': self.detection_time,
            'model_info': self.model_info,
            'parameters': self.parameters,
            'stats': {
                'total_regions': len(self.text_regions),
                'languages': list(set(r.get('language', 'unknown') for r in self.text_regions)),
                'avg_confidence': np.mean([r.get('confidence', 0) for r in self.text_regions]) if self.text_regions else 0
            }
        }


class ComicTextDetector:
    """漫画文本检测器主类"""
    
    def __init__(self, 
             model_path: Optional[str] = None,
             device: Optional[str] = None,
             config: Optional[Config] = None,
             **kwargs):
        """
        初始化检测器
        
        Args:
            model_path: 模型文件路径
            device: 计算设备 ('cuda', 'cpu', 'auto', 'cuda:0', 'cuda:1', etc.)
            config: 配置对象
            **kwargs: 其他检测参数
        """
        # 配置管理
        self.config = config or Config()
        
        # 设备设置
        if device is None:
            device = kwargs.get('device', self.config.get('detector.device', 'auto'))
        
        self.device = self._resolve_device(device)
        
        # 模型路径
        self.model_path = model_path or str(self.config.model_path)
        if not Path(self.model_path).exists():
            raise FileNotFoundError(f"模型文件不存在: {self.model_path}")
        
        # 检测参数
        detector_params = self.config.detector_params.copy()
        detector_params.update(kwargs)
        
        self.input_size = detector_params.get('input_size', 1280)
        self.conf_thresh = detector_params.get('conf_thresh', 0.4)
        self.nms_thresh = detector_params.get('nms_thresh', 0.35)
        self.mask_thresh = detector_params.get('mask_thresh', 0.3)
        self.allowed_languages = detector_params.get('allowed_languages', ['zh', 'ja'])
        
        # 初始化检测器
        self._init_detector()
        
        # 统计信息
        self.detection_count = 0
        self.total_time = 0.0

    def _resolve_device(self, device: str) -> str:
        """解析设备字符串"""
        if device == 'auto':
            if torch.cuda.is_available():
                return 'cuda'
            else:
                return 'cpu'
        elif device.startswith('cuda'):
            if torch.cuda.is_available():
                # 检查指定的GPU是否存在
                if ':' in device:
                    gpu_id = int(device.split(':')[1])
                    if gpu_id < torch.cuda.device_count():
                        return device
                    else:
                        print(f"警告: GPU {gpu_id} 不存在，回退到 cuda:0")
                        return 'cuda:0' if torch.cuda.device_count() > 0 else 'cpu'
                return 'cuda'
            else:
                print("警告: CUDA不可用，回退到CPU")
                return 'cpu'
        else:
            return 'cpu'
    
    def _init_detector(self):
        """初始化底层检测器"""
        try:
            self.detector = TextDetector(
                model_path=self.model_path,
                input_size=self.input_size,
                device=self.device,
                conf_thresh=self.conf_thresh,
                nms_thresh=self.nms_thresh,
                mask_thresh=self.mask_thresh
            )

        except Exception as e:
            raise RuntimeError(f"检测器初始化失败: {e}")
    
    def detect(self, image_path: Union[str, Path], **kwargs) -> DetectionResults:
        """
        执行文本检测
        
        Args:
            image_path: 图片路径
            **kwargs: 临时覆盖的参数
            
        Returns:
            DetectionResults: 检测结果对象
        """
        import time
        
        image_path = str(image_path)
        if not Path(image_path).exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        # 读取图片
        img = imread(image_path)
        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")
        
        # 创建结果对象
        results = DetectionResults(image_path, img.copy())
        
        start_time = time.time()
        
        try:
            # 执行检测
            mask, mask_refined, blk_list = self.detector(
                img, 
                refine_mode=REFINEMASK_ANNOTATION, 
                keep_undetected_mask=True
            )
            
            detection_time = time.time() - start_time
            
            # 处理检测结果
            text_regions = self._process_detection_results(blk_list, img.shape)
            
            # 生成可视化结果
            result_image = self._visualize_results(img.copy(), text_regions)
            
            # 填充结果对象
            results.text_regions = text_regions
            results.text_blocks = blk_list
            results.text_mask = mask
            results.refined_mask = mask_refined
            results.result_image = result_image
            results.detection_time = detection_time
            results.model_info = self._get_model_info()
            results.parameters = self._get_current_parameters(**kwargs)
            
            # 更新统计
            self.detection_count += 1
            self.total_time += detection_time
            
            print(f"检测完成: 找到 {len(text_regions)} 个文字区域, 耗时: {detection_time:.3f}s")
            
            return results
            
        except Exception as e:
            print(f"检测失败: {e}")
            raise
    
    def _process_detection_results(self, blk_list: List[TextBlock], img_shape: Tuple) -> List[Dict]:
        """处理检测结果，转换为标准格式"""
        text_regions = []
        
        for i, blk in enumerate(blk_list):
            # 语言过滤
            if blk.language not in self.allowed_languages:
                continue
            
            # 获取置信度
            confidence = getattr(blk, 'confidence', getattr(blk, 'prob', 1.0))
            
            region_info = {
                'id': len(text_regions),
                'bbox': blk.xyxy,
                'confidence': float(confidence) if confidence is not None else 1.0,
                'language': blk.language,
                'vertical': blk.vertical,
                'font_size': blk.font_size,
                'lines': blk.lines if hasattr(blk, 'lines') else [],
                'text': blk.get_text() if hasattr(blk, 'get_text') else "",
                'angle': getattr(blk, 'angle', 0)
            }
            
            text_regions.append(region_info)
        
        # 应用框过滤和合并逻辑
        current_params = self._get_current_parameters()
        text_regions = filter_and_merge_boxes(text_regions, current_params)
        
        return text_regions
    
    def _visualize_results(self, img: np.ndarray, text_regions: List[Dict]) -> np.ndarray:
        """生成可视化结果图片"""
        result = img.copy()
        
        for region in text_regions:
            x1, y1, x2, y2 = region['bbox']
            
            # 根据置信度调整颜色
            confidence = region['confidence']
            color_intensity = int(255 * min(confidence, 1.0))
            color = (0, color_intensity, 0)
            
            # 绘制边界框
            cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)
            
            # 标签
            label = f"{region['id']}_{region['language']}"
            if region['vertical']:
                label += "_V"
            label += f"_{confidence:.3f}"
            
            # 绘制标签
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(result, (x1, y1-25), (x1+label_size[0], y1), color, -1)
            cv2.putText(result, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return result
    
    def save_results(self, results: DetectionResults, output_dir: Union[str, Path]):
        """
        保存检测结果
        
        Args:
            results: 检测结果对象
            output_dir: 输出目录
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        base_name = results.image_name
        output_params = self.config.output_params
        
        try:
            # 保存结果图片
            if output_params.get('save_image', True):
                result_path = output_dir / f"{base_name}_result.{output_params.get('image_format', 'jpg')}"
                imwrite(str(result_path), results.result_image)
                print(f"结果图片已保存: {result_path}")
            
            # 保存文字掩码
            if output_params.get('save_mask', True) and results.refined_mask is not None:
                mask_path = output_dir / f"{base_name}_mask.{output_params.get('mask_format', 'png')}"
                imwrite(str(mask_path), results.refined_mask)
                print(f"文字掩码已保存: {mask_path}")
            
            # 保存JSON结果
            if output_params.get('save_json', True):
                json_path = output_dir / f"{base_name}_result.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(results.to_dict(), f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
                print(f"JSON结果已保存: {json_path}")
            
            return output_dir
            
        except Exception as e:
            print(f"保存结果失败: {e}")
            raise
    
    def _get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            'model_path': self.model_path,
            'device': self.device,
            'backend': getattr(self.detector, 'backend', 'unknown')
        }
    
    def _get_current_parameters(self, **kwargs) -> Dict[str, Any]:
        """获取当前检测参数"""
        params = {
            'input_size': self.input_size,
            'conf_thresh': self.conf_thresh,
            'nms_thresh': self.nms_thresh,
            'mask_thresh': self.mask_thresh,
            'allowed_languages': self.allowed_languages
        }
        params.update(kwargs)
        return params
    
    def update_parameters(self, **kwargs):
        """动态更新检测参数"""
        updated = False
        
        if 'conf_thresh' in kwargs:
            self.conf_thresh = kwargs['conf_thresh']
            self.detector.conf_thresh = self.conf_thresh
            updated = True
        
        if 'mask_thresh' in kwargs:
            self.mask_thresh = kwargs['mask_thresh']
            self.detector.mask_thresh = self.mask_thresh
            updated = True
        
        if 'allowed_languages' in kwargs:
            self.allowed_languages = kwargs['allowed_languages']
            updated = True
        
        if updated:
            print(f"参数已更新: {kwargs}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取检测器统计信息"""
        return {
            'detection_count': self.detection_count,
            'total_time': self.total_time,
            'avg_time_per_detection': self.total_time / self.detection_count if self.detection_count > 0 else 0,
            'current_parameters': self._get_current_parameters(),
            'model_info': self._get_model_info()
        }
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'detector'):
            del self.detector
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


# 便捷函数
def quick_detect(image_path: Union[str, Path], 
                 model_path: Optional[str] = None,
                 output_dir: Optional[str] = None,
                 **kwargs) -> DetectionResults:
    """
    快速检测函数
    
    Args:
        image_path: 图片路径
        model_path: 模型路径
        output_dir: 输出目录
        **kwargs: 检测参数
        
    Returns:
        DetectionResults: 检测结果
    """
    detector = ComicTextDetector(model_path=model_path, **kwargs)
    results = detector.detect(image_path)
    
    if output_dir:
        detector.save_results(results, output_dir)
    
    return results


if __name__ == "__main__":
    # 测试检测器
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python detector.py <image_path> [output_dir]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "test_results"
    
    try:
        results = quick_detect(image_path, output_dir=output_dir)
        print(f"检测完成! 找到 {len(results.text_regions)} 个文字区域")
        
    except Exception as e:
        print(f"检测失败: {e}")
        sys.exit(1)