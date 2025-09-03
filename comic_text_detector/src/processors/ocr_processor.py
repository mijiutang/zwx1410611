"""
OCR处理器模块 - 修复数组比较问题
"""

import numpy as np
from typing import List, Dict, Any
from pathlib import Path

# OCR相关导入
try:
    from paddlex import create_pipeline
    PADDLEX_AVAILABLE = True
except ImportError:
    print("Warning: PaddleX not available. OCR功能将被禁用。")
    print("请安装PaddleX: pip install paddlex")
    PADDLEX_AVAILABLE = False


class OCRProcessor:
    """OCR处理器类 - 修复数组比较问题"""
    
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
        """解析OCR结果 - 修复数组比较问题"""
        try:
            texts = []
            
            # 检查 ocr_result 是否为空或None
            if not ocr_result:
                return ""
            
            for result in ocr_result:
                # 安全获取识别文本和位置框
                rec_texts = result.get('rec_texts', [])
                rec_boxes = result.get('rec_boxes', [])
                
                # 修复：安全检查数组内容
                if self._is_empty_or_none(rec_texts) or self._is_empty_or_none(rec_boxes):
                    continue
                
                # 确保文本和框的数量匹配
                min_len = min(len(rec_texts), len(rec_boxes))
                if min_len <= 0:
                    continue
                
                # 创建文本和坐标的配对列表
                text_box_pairs = []
                for idx in range(min_len):
                    text = rec_texts[idx]
                    box = rec_boxes[idx]
                    
                    # 检查文本和框是否有效
                    if text and self._is_valid_box(box):
                        text_box_pairs.append((text, box))
                
                if not text_box_pairs:
                    continue
                
                # 根据语言类型排序
                try:
                    if language == 'ja':  # 日文从右到左
                        sorted_pairs = sorted(text_box_pairs, 
                                            key=lambda pair: self._safe_get_x_coord(pair[1]), 
                                            reverse=True)
                    else:  # 其他语言从左到右
                        sorted_pairs = sorted(text_box_pairs, 
                                            key=lambda pair: self._safe_get_x_coord(pair[1]))
                except Exception as sort_error:
                    print(f"排序失败，使用原始顺序: {sort_error}")
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
    
    def _is_empty_or_none(self, data) -> bool:
        """安全检查数据是否为空或None"""
        if data is None:
            return True
        if isinstance(data, (list, tuple, np.ndarray)):
            return len(data) == 0
        return False
    
    def _is_valid_box(self, box) -> bool:
        """检查边界框是否有效"""
        try:
            if self._is_empty_or_none(box):
                return False
            
            # 转换为列表以安全访问
            if isinstance(box, np.ndarray):
                box_list = box.tolist() if box.size > 0 else []
            else:
                box_list = list(box) if box else []
            
            return len(box_list) > 0
        except Exception:
            return False
    
    def _safe_get_x_coord(self, box) -> float:
        """安全获取边界框的x坐标"""
        try:
            if self._is_empty_or_none(box):
                return 0.0
            
            # 转换为列表以安全访问
            if isinstance(box, np.ndarray):
                box_list = box.tolist() if box.size > 0 else []
            else:
                box_list = list(box) if box else []
            
            if len(box_list) > 0:
                first_element = box_list[0]
                # 如果第一个元素是列表或数组，取其第一个元素
                if isinstance(first_element, (list, tuple, np.ndarray)):
                    return float(first_element[0]) if len(first_element) > 0 else 0.0
                else:
                    return float(first_element)
            
            return 0.0
            
        except (IndexError, TypeError, ValueError):
            return 0.0
    
    def _calculate_average_confidence(self, ocr_result) -> float:
        """计算平均置信度"""
        try:
            confidences = []
            for result in ocr_result:
                if 'rec_scores' in result:
                    scores = result['rec_scores']
                    if scores and len(scores) > 0:
                        confidences.extend([float(score) for score in scores if score is not None])
            
            return float(np.mean(confidences)) if confidences else 0.0
            
        except Exception:
            return 0.0