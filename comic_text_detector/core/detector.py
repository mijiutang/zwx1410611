"""
分离版核心检测器类 - 优化输出文件结构
"""

import cv2
import json
import numpy as np
import torch
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union
import time

from core.inference import TextDetector
from utils.textmask import refine_mask, refine_undetected_mask, REFINEMASK_ANNOTATION
from utils.io_utils import imread, imwrite, NumpyEncoder
from utils.textblock import TextBlock, visualize_textblocks
from config.config import Config
from utils.detection_utils import filter_and_merge_boxes
from src.processors.ocr_processor import OCRProcessor
from core.results import DetectionResults, ProjectResults


# OCR相关导入
try:
    from paddlex import create_pipeline
    PADDLEX_AVAILABLE = True
except ImportError:
    print("Warning: PaddleX not available. OCR功能将被禁用。")
    print("请安装PaddleX: pip install paddlex")
    PADDLEX_AVAILABLE = False

class ComicTextDetector:
    """漫画文本检测器主类 - 分离的检测和OCR功能"""
    
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
    
    def detect_only(self, image_path: Union[str, Path], **kwargs) -> DetectionResults:
        """
        仅执行文本检测，不进行OCR识别
        
        Args:
            image_path: 图片路径
            **kwargs: 临时覆盖的参数
            
        Returns:
            DetectionResults: 仅包含检测结果的对象
        """
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
            results.ocr_time = 0.0
            results.has_ocr_results = False
            results.model_info = self._get_model_info()
            results.parameters = self._get_current_parameters(**kwargs)
            
            # 更新统计
            self.detection_count += 1
            self.total_time += detection_time
            
            print(f"检测完成: 找到 {len(text_regions)} 个文字区域, 检测耗时: {detection_time:.3f}s")
            
            return results
            
        except Exception as e:
            print(f"检测失败: {e}")
            raise
    
    def run_ocr_on_results(self, results: DetectionResults) -> DetectionResults:
        """
        对现有检测结果进行OCR识别
        
        Args:
            results: 检测结果对象
            
        Returns:
            DetectionResults: 更新了OCR结果的对象
        """
        if not self.ocr_processor.enable_ocr:
            print("OCR功能未启用，跳过文本识别")
            return results
        
        if results.has_ocr_results:
            print("该结果已包含OCR结果，跳过重复处理")
            return results
        
        ocr_start_time = time.time()
        
        try:
            # 进行OCR处理
            ocr_results = self.ocr_processor.process_text_regions(
                results.original_image, 
                results.text_regions
            )
            
            ocr_time = time.time() - ocr_start_time
            
            # 更新结果对象
            results.ocr_results = ocr_results
            results.ocr_time = ocr_time
            results.has_ocr_results = True
            
            # 重新生成可视化结果（包含OCR文本）
            results.result_image = self._visualize_results(results.original_image.copy(), results.text_regions)
            
            # 更新统计
            self.total_ocr_time += ocr_time
            
            print(f"OCR完成: 处理 {len(results.text_regions)} 个文字区域, OCR耗时: {ocr_time:.3f}s")
            
            return results
            
        except Exception as e:
            print(f"OCR处理失败: {e}")
            raise
    
    def detect(self, image_path: Union[str, Path], enable_ocr: Optional[bool] = None, **kwargs) -> DetectionResults:
        """
        执行文本检测，可选择是否进行OCR识别（保持兼容性）
        
        Args:
            image_path: 图片路径
            enable_ocr: 是否启用OCR（覆盖初始化设置）
            **kwargs: 临时覆盖的参数
            
        Returns:
            DetectionResults: 检测结果对象
        """
        # 先进行检测
        results = self.detect_only(image_path, **kwargs)
        
        # 如果需要OCR，则进行OCR处理
        should_do_ocr = enable_ocr if enable_ocr is not None else self.ocr_processor.enable_ocr
        if should_do_ocr:
            results = self.run_ocr_on_results(results)
        
        return results
    
    def batch_process_project(self, 
                            image_files: List[str], 
                            project_name: str,
                            output_dir: Union[str, Path],
                            include_ocr: bool = True,
                            progress_callback=None) -> ProjectResults:
        """
        批量处理项目，返回项目结果对象
        """
        project_results = ProjectResults(project_name)
        
        # 【新增】提前创建项目结构
        project_results.create_project_structure(output_dir, self.config.output_params)
        
        total_files = len(image_files)
        
        print(f"开始批量处理项目: {project_name} ({total_files} 个文件)")
        
        for i, image_path in enumerate(image_files, 1):
            try:
                file_name = Path(image_path).name
                
                if progress_callback:
                    progress_callback(i, total_files, f"正在检测: {file_name}")
                
                # 执行检测
                results = self.detect_only(image_path)
                
                # 【新增】立即保存检测结果
                project_results.update_image_detection_result(results, self.config.output_params)
                
                # 如果需要OCR，执行OCR
                if include_ocr:
                    if progress_callback:
                        progress_callback(i, total_files, f"正在OCR: {file_name}")
                    results = self.run_ocr_on_results(results)
                    
                    # 【新增】立即保存OCR结果
                    project_results.update_image_ocr_result(results)
                
                # 添加到项目结果
                project_results.add_result(results)
                
                print(f"完成 ({i}/{total_files}): {file_name} - {len(results.text_regions)} 个区域")
                
            except Exception as e:
                print(f"处理文件 {image_path} 时出错: {e}")
                # 创建空结果占位
                empty_result = DetectionResults(image_path, np.zeros((100, 100, 3), dtype=np.uint8))
                empty_result.detection_time = 0.0
                empty_result.ocr_time = 0.0
                project_results.add_result(empty_result)
        
        # 【新增】完成项目处理
        project_results.finalize_project()
        
        print(f"项目 '{project_name}' 批量处理完成！")
        return project_results

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
        保存单个检测结果（兼容方法，建议使用 batch_process_project）
        
        Args:
            results: 检测结果对象
            output_dir: 输出目录
        """
        project_results = ProjectResults("single_image")
        project_results.add_result(results)
        return project_results.save_to_directory(output_dir, self.config.output_params)
    
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
            'allowed_languages': self.allowed_languages,
            'containment_thresh': self.config.detector_params.get('containment_thresh', 0.8),
            'enable_box_filter': self.config.detector_params.get('enable_box_filter', True),
            'min_box_width': self.config.detector_params.get('min_box_width', 10),
            'min_box_height': self.config.detector_params.get('min_box_height', 10)
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
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'detector'):
            del self.detector
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

# 便捷函数
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

if __name__ == "__main__":
    # 测试检测器
    import sys
    
    if len(sys.argv) < 3:
        print("用法: python detector.py <image_dir> <project_name> [output_dir]")
        sys.exit(1)
    
    image_dir = Path(sys.argv[1])
    project_name = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "test_results"
    
    if not image_dir.exists():
        print(f"图片目录不存在: {image_dir}")
        sys.exit(1)
    
    try:
        # 获取图片文件列表
        from utils.io_utils import find_all_imgs
        image_files = find_all_imgs(str(image_dir), abs_path=True)
        
        if not image_files:
            print(f"目录中没有找到图片文件: {image_dir}")
            sys.exit(1)
        
        print(f"找到 {len(image_files)} 个图片文件")
        
        # 批量处理
        project_results = batch_process_project(
            image_files=image_files,
            project_name=project_name,
            output_dir=output_dir,
            include_ocr=True
        )
        
        print(f"处理完成！项目结果保存在: {project_results}")
        
    except Exception as e:
        print(f"处理失败: {e}")
        sys.exit(1)