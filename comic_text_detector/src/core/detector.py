"""
增强版核心检测器类 - 集成OCR文本识别功能
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

# OCR相关导入
try:
    from paddlex import create_pipeline
    PADDLEX_AVAILABLE = True
except ImportError:
    print("Warning: PaddleX not available. OCR功能将被禁用。")
    print("请安装PaddleX: pip install paddlex")
    PADDLEX_AVAILABLE = False

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

def filter_and_merge_boxes(text_regions, config_params):
    """过滤和合并检测框"""
    if not config_params.get('enable_box_filter', True):
        return text_regions
    
    min_box_width = config_params.get('min_box_width', 10)
    min_box_height = config_params.get('min_box_height', 10)
    containment_thresh = config_params.get('containment_thresh', 0.8)
    
    print(f"开始框处理，共有{len(text_regions)}个框")
    
    # 1. 过滤小框
    filtered_regions = []
    for i, region in enumerate(text_regions):
        x1, y1, x2, y2 = region['bbox']
        width = x2 - x1
        height = y2 - y1
        print(f"框{i}: 位置[{x1},{y1},{x2},{y2}], 尺寸{width}x{height}")
        
        if width >= min_box_width or height >= min_box_height:
            filtered_regions.append(region)
        else:
            print(f"过滤掉小框{i}")
    
    if len(filtered_regions) <= 1:
        print("框数量<=1，无需合并")
        return filtered_regions
    
    # 2. 处理包含关系
    to_remove = set()
    for i in range(len(filtered_regions)):
        if i in to_remove:
            continue
        for j in range(len(filtered_regions)):
            if i == j or j in to_remove:
                continue
            
            box_i = filtered_regions[i]['bbox']
            box_j = filtered_regions[j]['bbox']
            
            containment_i_in_j = calculate_containment_ratio(box_i, box_j)
            if containment_i_in_j > containment_thresh:
                to_remove.add(i)
                print(f"移除被包含的框{i}: 包含比例{containment_i_in_j:.3f}")
                break
    
    # 移除被包含的框
    filtered_regions = [region for i, region in enumerate(filtered_regions) if i not in to_remove]
    print(f"包含关系处理后，剩余{len(filtered_regions)}个框")

    return filtered_regions

class OCRProcessor:
    """OCR处理器类"""
    
    def __init__(self, enable_ocr=True):
        self.enable_ocr = enable_ocr and PADDLEX_AVAILABLE
        self.ocr_pipeline = None
        
        if self.enable_ocr:
            try:
                self.ocr_pipeline = create_pipeline(pipeline="OCR")
                print("OCR pipeline 初始化成功")
            except Exception as e:
                print(f"OCR pipeline 初始化失败: {e}")
                self.enable_ocr = False
    
    def extract_text_region(self, image: np.ndarray, bbox: List[int]) -> np.ndarray:
        """从图像中提取文本区域"""
        x1, y1, x2, y2 = bbox
        # 确保坐标在图像范围内
        h, w = image.shape[:2]
        x1 = max(0, min(x1, w-1))
        y1 = max(0, min(y1, h-1))
        x2 = max(x1+1, min(x2, w))
        y2 = max(y1+1, min(y2, h))
        
        region = image[y1:y2, x1:x2]
        return region
    
    def process_text_regions(self, image: np.ndarray, text_regions: List[Dict]) -> Dict[str, str]:
        """处理所有文本区域并进行OCR识别"""
        ocr_results = {}
        
        if not self.enable_ocr:
            print("OCR功能未启用，跳过文本识别")
            return ocr_results
        
        print(f"开始OCR处理，共有{len(text_regions)}个文本区域")
        
        for i, region in enumerate(text_regions):
            try:
                # 提取文本区域图像
                bbox = region['bbox']
                text_region = self.extract_text_region(image, bbox)
                
                if text_region.size == 0:
                    print(f"区域{i}为空，跳过OCR")
                    continue
                
                # 执行OCR
                ocr_result = self.ocr_pipeline.predict(
                    input=text_region,
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=True,
                )
                
                # 处理OCR结果
                recognized_text = self._parse_ocr_result(ocr_result, region.get('language', 'unknown'))
                
                # 存储结果
                region_key = f"region_{i}"
                ocr_results[region_key] = recognized_text
                
                # 更新region信息
                region['ocr_text'] = recognized_text
                region['ocr_confidence'] = self._calculate_average_confidence(ocr_result)
                
                print(f"区域{i}OCR结果: {recognized_text[:50]}...")
                
            except Exception as e:
                print(f"区域{i}OCR处理失败: {e}")
                region_key = f"region_{i}"
                ocr_results[region_key] = ""
                region['ocr_text'] = ""
                region['ocr_confidence'] = 0.0
        
        return ocr_results
    
    def _parse_ocr_result(self, ocr_result, language='unknown') -> str:
        """解析OCR结果"""
        try:
            texts = []
            for result in ocr_result:
                if 'rec_texts' in result:
                    rec_texts = result['rec_texts']
                    boxes = result.get('rec_boxes', [])
                    
                    # 安全检查：确保数据存在且不为空
                    if (rec_texts is not None and len(rec_texts) > 0 and 
                        boxes is not None and len(boxes) > 0):
                        
                        # 确保文本和框的数量匹配
                        min_len = min(len(rec_texts), len(boxes))
                        if min_len > 0:
                            # 创建文本和坐标的配对列表
                            text_box_pairs = list(zip(rec_texts[:min_len], boxes[:min_len]))
                            
                            # 根据语言类型排序
                            if language == 'ja':  # 日文从右到左
                                try:
                                    sorted_pairs = sorted(text_box_pairs, 
                                                        key=lambda pair: float(pair[1][0]) if len(pair[1]) > 0 else 0, 
                                                        reverse=True)
                                except (IndexError, TypeError, ValueError):
                                    # 如果排序失败，使用原始顺序
                                    sorted_pairs = text_box_pairs
                            else:  # 其他语言从左到右
                                try:
                                    sorted_pairs = sorted(text_box_pairs, 
                                                        key=lambda pair: float(pair[1][0]) if len(pair[1]) > 0 else 0)
                                except (IndexError, TypeError, ValueError):
                                    # 如果排序失败，使用原始顺序
                                    sorted_pairs = text_box_pairs
                            
                            # 提取排序后的文本
                            sorted_texts = [str(pair[0]) for pair in sorted_pairs if pair[0]]
                            texts.extend(sorted_texts)
            
            return "".join(texts)
            
        except Exception as e:
            print(f"解析OCR结果失败: {e}")
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
            return ""
    
    def _calculate_average_confidence(self, ocr_result) -> float:
        """计算平均置信度"""
        try:
            confidences = []
            for result in ocr_result:
                if 'rec_scores' in result:
                    confidences.extend(result['rec_scores'])
            
            return float(np.mean(confidences)) if confidences else 0.0
            
        except Exception:
            return 0.0

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
        
        # OCR结果
        self.ocr_results: Dict[str, str] = {}
        
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

class ComicTextDetector:
    """漫画文本检测器主类 - 集成OCR功能"""
    
    def __init__(self, 
                 model_path: Optional[str] = None,
                 device: Optional[str] = None,
                 config: Optional[Config] = None,
                 enable_ocr: bool = True,
                 **kwargs):
        """
        初始化检测器
        
        Args:
            model_path: 模型文件路径
            device: 计算设备
            config: 配置对象
            enable_ocr: 是否启用OCR功能
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
        
        # 初始化检测器和OCR处理器
        self._init_detector()
        self.ocr_processor = OCRProcessor(enable_ocr=enable_ocr)
        
        # 统计信息
        self.detection_count = 0
        self.total_time = 0.0
        self.total_ocr_time = 0.0

    def _resolve_device(self, device: str) -> str:
        """解析设备字符串"""
        if device == 'auto':
            if torch.cuda.is_available():
                return 'cuda'
            else:
                return 'cpu'
        elif device.startswith('cuda'):
            if torch.cuda.is_available():
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
    
    def detect(self, image_path: Union[str, Path], enable_ocr: Optional[bool] = None, **kwargs) -> DetectionResults:
        """
        执行文本检测和OCR识别
        
        Args:
            image_path: 图片路径
            enable_ocr: 是否启用OCR（覆盖初始化设置）
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
            
            # OCR处理
            ocr_start_time = time.time()
            should_do_ocr = enable_ocr if enable_ocr is not None else self.ocr_processor.enable_ocr
            
            if should_do_ocr:
                ocr_results = self.ocr_processor.process_text_regions(img, text_regions)
                results.ocr_results = ocr_results
            
            ocr_time = time.time() - ocr_start_time
            
            # 生成可视化结果
            result_image = self._visualize_results(img.copy(), text_regions)
            
            # 填充结果对象
            results.text_regions = text_regions
            results.text_blocks = blk_list
            results.text_mask = mask
            results.refined_mask = mask_refined
            results.result_image = result_image
            results.detection_time = detection_time
            results.ocr_time = ocr_time
            results.model_info = self._get_model_info()
            results.parameters = self._get_current_parameters(**kwargs)
            
            # 更新统计
            self.detection_count += 1
            self.total_time += detection_time
            self.total_ocr_time += ocr_time
            
            print(f"检测完成: 找到 {len(text_regions)} 个文字区域, 检测耗时: {detection_time:.3f}s, OCR耗时: {ocr_time:.3f}s")
            
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
            
            # 标签包含OCR结果
            label = f"{region['id']}_{region['language']}"
            if region['vertical']:
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
    
    def save_results(self, results: DetectionResults, output_dir: Union[str, Path]):
        """
        保存检测结果（包含OCR结果）
        
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
            
            # 保存JSON结果（包含OCR）
            if output_params.get('save_json', True):
                json_path = output_dir / f"{base_name}_result.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(results.to_dict(), f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
                print(f"JSON结果已保存: {json_path}")
            
            # 单独保存OCR结果
            if results.ocr_results:
                ocr_path = output_dir / f"{base_name}_ocr.json"
                with open(ocr_path, 'w', encoding='utf-8') as f:
                    json.dump({results.image_name: results.ocr_results}, f, ensure_ascii=False, indent=2)
                print(f"OCR结果已保存: {ocr_path}")
            
            return output_dir
            
        except Exception as e:
            print(f"保存结果失败: {e}")
            raise
    
    def _get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            'model_path': self.model_path,
            'device': self.device,
            'backend': getattr(self.detector, 'backend', 'unknown'),
            'ocr_enabled': self.ocr_processor.enable_ocr
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
            'total_ocr_time': self.total_ocr_time,
            'avg_time_per_detection': self.total_time / self.detection_count if self.detection_count > 0 else 0,
            'avg_ocr_time_per_detection': self.total_ocr_time / self.detection_count if self.detection_count > 0 else 0,
            'current_parameters': self._get_current_parameters(),
            'model_info': self._get_model_info()
        }
    
    def batch_process_with_ocr(self, image_paths: List[Union[str, Path]], 
                              output_dir: Union[str, Path]) -> Dict[str, str]:
        """
        批量处理图片并进行OCR识别
        
        Args:
            image_paths: 图片路径列表
            output_dir: 输出目录
            
        Returns:
            Dict[str, str]: 图片名到OCR文本的映射
        """
        batch_results = {}
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"开始批量处理{len(image_paths)}张图片")
        
        for i, image_path in enumerate(image_paths, 1):
            try:
                print(f"处理第{i}/{len(image_paths)}张图片: {image_path}")
                
                # 执行检测和OCR
                results = self.detect(image_path, enable_ocr=True)
                
                # 保存结果
                self.save_results(results, output_dir)
                
                # 汇总OCR文本
                all_texts = []
                for region_key, text in results.ocr_results.items():
                    if text.strip():
                        all_texts.append(text.strip())
                
                combined_text = " ".join(all_texts)
                batch_results[results.image_name] = combined_text
                
                print(f"完成处理: {results.image_name}, 识别文本: {combined_text[:100]}...")
                
            except Exception as e:
                print(f"处理图片{image_path}时出错: {e}")
                image_name = Path(image_path).stem
                batch_results[image_name] = ""
        
        # 保存批量OCR结果
        batch_ocr_path = output_dir / "batch_ocr_results.json"
        with open(batch_ocr_path, 'w', encoding='utf-8') as f:
            json.dump(batch_results, f, ensure_ascii=False, indent=2)
        
        print(f"批量处理完成，结果已保存到: {batch_ocr_path}")
        return batch_results
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'detector'):
            del self.detector
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

# 便捷函数
def quick_detect_with_ocr(image_path: Union[str, Path], 
                         model_path: Optional[str] = None,
                         output_dir: Optional[str] = None,
                         enable_ocr: bool = True,
                         **kwargs) -> DetectionResults:
    """
    快速检测和OCR函数
    
    Args:
        image_path: 图片路径
        model_path: 模型路径
        output_dir: 输出目录
        enable_ocr: 是否启用OCR
        **kwargs: 检测参数
        
    Returns:
        DetectionResults: 检测结果
    """
    detector = ComicTextDetector(model_path=model_path, enable_ocr=enable_ocr, **kwargs)
    results = detector.detect(image_path, enable_ocr=enable_ocr)
    
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
        results = quick_detect_with_ocr(image_path, output_dir=output_dir, enable_ocr=True)
        print(f"检测完成! 找到 {len(results.text_regions)} 个文字区域")
        print(f"OCR结果: {results.ocr_results}")
        
    except Exception as e:
        print(f"检测失败: {e}")
        sys.exit(1)