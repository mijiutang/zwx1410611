# comic_text_detector - Markdown文档

---

# `config`

## `config.py`

```py
"""
配置管理模块
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
import torch


class Config:
    """配置管理类"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.project_root = Path(__file__).parent.parent
        
        # 默认配置文件路径
        self.default_config_file = self.project_root / "config" / "default_settings.json"
        self.config_file = config_file or str(self.default_config_file)
        
        # 默认配置
        self._default_config = {
            # 路径配置
            "paths": {
                "models_dir": "data/models",
                "examples_dir": "data/examples", 
                "results_dir": "data/results",
                "default_model": "data/models/comictextdetector.pt"
            },
            
            # 设备配置
            "device": "auto",  # 改为 "auto" 而不是直接判断
            
            # 在 _default_config 中修改检测器参数部分
            "detector": {
                "input_size": 1280,
                "conf_thresh": 0.4,
                "nms_thresh": 0.35,
                "mask_thresh": 0.3,
                "allowed_languages": ["zh", "ja"],
                "device": "auto",
                "min_box_width": 10,          # 最小框宽度
                "min_box_height": 10,         # 最小框高度  
                
                "containment_thresh": 0.8,    # 包含关系阈值
                "enable_box_filter": True     # 是否启用框过滤功能
            },
            
            # GUI配置
            "gui": {
                "window_size": [1200, 800],
                "recent_files_count": 10,
                "auto_save_results": True
            },
            
            # 输出配置
            "output": {
                "save_image": True,
                "save_mask": True,
                "save_json": True,
                "image_format": "jpg",
                "mask_format": "png"
            }
        }
        
        # 加载配置
        self.config = self._load_config()
        
        # 创建必要的目录
        self._ensure_directories()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config = self._default_config.copy()
        
        # 首先尝试加载默认配置文件
        if self.default_config_file.exists():
            try:
                with open(self.default_config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                config = self._deep_update(config, user_config)
                print(f"已加载默认配置: {self.default_config_file}")
            except Exception as e:
                print(f"警告：无法加载默认配置文件 {self.default_config_file}: {e}")
                # 如果默认配置文件不存在或有问题，创建一个新的
                self._create_default_config()
        else:
            # 创建默认配置文件
            self._create_default_config()
        
        # 如果指定了其他配置文件，则覆盖加载
        if self.config_file != str(self.default_config_file) and Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                        user_config = yaml.safe_load(f)
                    else:
                        user_config = json.load(f)
                
                config = self._deep_update(config, user_config)
                
            except Exception as e:
                print(f"警告：无法加载配置文件 {self.config_file}: {e}")
        
        return config
    
    def _create_default_config(self):
        """创建默认配置文件"""
        try:
            # 确保config目录存在
            self.default_config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.default_config_file, 'w', encoding='utf-8') as f:
                json.dump(self._default_config, f, indent=2, ensure_ascii=False)
            print(f"已创建默认配置文件: {self.default_config_file}")
        except Exception as e:
            print(f"警告：无法创建默认配置文件: {e}")
    
    def save_as_default(self):
        """将当前配置保存为默认配置"""
        try:
            # 确保config目录存在
            self.default_config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.default_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"配置已更新并保存为默认配置: {self.default_config_file}")
            return True
        except Exception as e:
            print(f"错误：无法保存默认配置: {e}")
            return False
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict) -> Dict:
        """递归更新字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                base_dict[key] = self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
        return base_dict
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        dirs_to_create = [
            self.models_dir,
            self.examples_dir,
            self.results_dir,
        ]
        
        for dir_path in dirs_to_create:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, file_path: Optional[str] = None):
        """保存配置到文件"""
        if file_path is None:
            file_path = self.config_file
        
        with open(file_path, 'w', encoding='utf-8') as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            else:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    # 便捷属性保持不变...
    @property
    def project_root(self) -> Path:
        return self._project_root
    
    @project_root.setter
    def project_root(self, value: Path):
        self._project_root = value
    
    @property
    def models_dir(self) -> Path:
        return self.project_root / self.get('paths.models_dir', 'data/models')
    
    @property
    def examples_dir(self) -> Path:
        return self.project_root / self.get('paths.examples_dir', 'data/examples')
    
    @property
    def results_dir(self) -> Path:
        return self.project_root / self.get('paths.results_dir', 'data/results')
    
    @property
    def model_path(self) -> Path:
        return self.project_root / self.get('paths.default_model', 'data/models/comictextdetector.pt')
    
    @property
    def device(self) -> str:
        return self.get('device', 'cpu')
    
    @property
    def detector_params(self) -> Dict[str, Any]:
        return self.get('detector', {})
    
    @property
    def gui_params(self) -> Dict[str, Any]:
        return self.get('gui', {})
    
    @property
    def output_params(self) -> Dict[str, Any]:
        return self.get('output', {})


# 创建默认配置文件的函数保持不变...
def create_default_config(file_path: str = "config.yaml"):
    """创建默认配置文件"""
    config = Config()
    config.save(file_path)
    print(f"默认配置文件已创建：{file_path}")


if __name__ == "__main__":
    # 测试配置管理
    config = Config()
    print("设备:", config.device)
    print("模型路径:", config.model_path)
    print("检测器参数:", config.detector_params)
```

## `paths.py`

```py

```

## `__init__.py`

```py

```

# `core`

## `basemodel.py`

```py
# 修复后的 basemodel.py - 更新所有导入路径

from utils.general import CUDA, DEVICE
from src.models.yolov5.yolo import Model
import torch
import cv2
import numpy as np
from src.models.yolov5.yolo import load_yolov5_ckpt  # 修复导入路径
from utils.yolov5_utils import fuse_conv_and_bn  # 修复导入路径
import glob
import torch.nn as nn
from utils.weight_init import init_weights  # 修复导入路径
from src.models.yolov5.common import C3, Conv  # 修复导入路径
from torchsummary import summary
import torch.nn.functional as F
import copy

TEXTDET_MASK = 0
TEXTDET_DET = 1
TEXTDET_INFERENCE = 2

class double_conv_up_c3(nn.Module):
    def __init__(self, in_ch, mid_ch, out_ch, act=True):
        super(double_conv_up_c3, self).__init__()
        self.conv = nn.Sequential(
        C3(in_ch+mid_ch, mid_ch, act=act),
        nn.ConvTranspose2d(mid_ch, out_ch, kernel_size=4, stride = 2, padding=1, bias=False),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.conv(x)

class double_conv_c3(nn.Module):
    def __init__(self, in_ch, out_ch, stride=1, act=True):
        super(double_conv_c3, self).__init__()
        if stride > 1 :
            self.down = nn.AvgPool2d(2,stride=2) if stride > 1 else None
        self.conv = C3(in_ch, out_ch, act=act)

    def forward(self, x):
        if self.down is not None :
            x = self.down(x)
        x = self.conv(x)
        return x

class UnetHead(nn.Module):
    def __init__(self, act=True) -> None:

        super(UnetHead, self).__init__()
        self.down_conv1 = double_conv_c3(512, 512, 2, act=act)
        self.upconv0 = double_conv_up_c3(0, 512, 256, act=act)
        self.upconv2 = double_conv_up_c3(256, 512, 256, act=act)
        self.upconv3 = double_conv_up_c3(0, 512, 256, act=act)
        self.upconv4 = double_conv_up_c3(128, 256, 128, act=act)
        self.upconv5 = double_conv_up_c3(64, 128, 64, act=act)
        self.upconv6 = nn.Sequential(
            nn.ConvTranspose2d(64, 1, kernel_size=4, stride = 2, padding=1, bias=False),
            nn.Sigmoid()
        )

    def forward(self, f160, f80, f40, f20, f3, forward_mode=TEXTDET_MASK):
        # input: 640@3
        d10 = self.down_conv1(f3) # 512@10
        u20 = self.upconv0(d10)  # 256@10
        u40 = self.upconv2(torch.cat([f20, u20], dim = 1)) # 256@40

        if forward_mode == TEXTDET_DET:
            return f80, f40, u40
        else:
            u80 = self.upconv3(torch.cat([f40, u40], dim = 1)) # 256@80
            u160 = self.upconv4(torch.cat([f80, u80], dim = 1)) # 128@160
            u320 = self.upconv5(torch.cat([f160, u160], dim = 1)) # 64@320
            mask = self.upconv6(u320)
            if forward_mode == TEXTDET_MASK:
                return mask
            else:
                return mask, [f80, f40, u40]
            
    def init_weight(self, init_func):
        self.apply(init_func)

class DBHead(nn.Module):
    def __init__(self, in_channels, k = 50, shrink_with_sigmoid=True, act=True):
        super().__init__()
        self.k = k
        self.shrink_with_sigmoid = shrink_with_sigmoid
        self.upconv3 = double_conv_up_c3(0, 512, 256, act=act)
        self.upconv4 = double_conv_up_c3(128, 256, 128, act=act)
        self.conv = nn.Sequential(
            nn.Conv2d(128, in_channels, 1),
            nn.BatchNorm2d(in_channels),
            nn.ReLU(inplace=True)
        )
        self.binarize = nn.Sequential(
            nn.Conv2d(in_channels, in_channels // 4, 3, padding=1),
            nn.BatchNorm2d(in_channels // 4),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(in_channels // 4, in_channels // 4, 2, 2),
            nn.BatchNorm2d(in_channels // 4),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(in_channels // 4, 1, 2, 2)
            )
        self.thresh = self._init_thresh(in_channels)

    def forward(self, f80, f40, u40, shrink_with_sigmoid=True, step_eval=False):
        shrink_with_sigmoid = self.shrink_with_sigmoid
        u80 = self.upconv3(torch.cat([f40, u40], dim = 1)) # 256@80
        x = self.upconv4(torch.cat([f80, u80], dim = 1)) # 128@160
        x = self.conv(x)
        threshold_maps = self.thresh(x)
        x = self.binarize(x)
        shrink_maps = torch.sigmoid(x)
        
        if self.training:
            binary_maps = self.step_function(shrink_maps, threshold_maps)
            if shrink_with_sigmoid:
                return torch.cat((shrink_maps, threshold_maps, binary_maps), dim=1)
            else:
                return torch.cat((shrink_maps, threshold_maps, binary_maps, x), dim=1)
        else:
            if step_eval:
                return self.step_function(shrink_maps, threshold_maps)
            else:
                return torch.cat((shrink_maps, threshold_maps), dim=1)

    def init_weight(self, init_func):
        self.apply(init_func)

    def _init_thresh(self, inner_channels, serial=False, smooth=False, bias=False):
        in_channels = inner_channels
        if serial:
            in_channels += 1
        self.thresh = nn.Sequential(
            nn.Conv2d(in_channels, inner_channels // 4, 3, padding=1, bias=bias),
            nn.BatchNorm2d(inner_channels // 4),
            nn.ReLU(inplace=True),
            self._init_upsample(inner_channels // 4, inner_channels // 4, smooth=smooth, bias=bias),
            nn.BatchNorm2d(inner_channels // 4),
            nn.ReLU(inplace=True),
            self._init_upsample(inner_channels // 4, 1, smooth=smooth, bias=bias),
            nn.Sigmoid())
        return self.thresh

    def _init_upsample(self, in_channels, out_channels, smooth=False, bias=False):
        if smooth:
            inter_out_channels = out_channels
            if out_channels == 1:
                inter_out_channels = in_channels
            module_list = [
                nn.Upsample(scale_factor=2, mode='nearest'),
                nn.Conv2d(in_channels, inter_out_channels, 3, 1, 1, bias=bias)]
            if out_channels == 1:
                module_list.append(nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=1, padding=1, bias=True))
            return nn.Sequential(module_list)
        else:
            return nn.ConvTranspose2d(in_channels, out_channels, 2, 2)

    def step_function(self, x, y):
        return torch.reciprocal(1 + torch.exp(-self.k * (x - y)))

class TextDetector(nn.Module):
    def __init__(self, weights, map_location='cpu', forward_mode=TEXTDET_MASK, act=True):
        super(TextDetector, self).__init__()

        yolov5s_backbone = load_yolov5_ckpt(weights=weights, map_location=map_location)
        yolov5s_backbone.eval()
        out_indices = [1, 3, 5, 7, 9]
        yolov5s_backbone.out_indices = out_indices
        yolov5s_backbone.model = yolov5s_backbone.model[:max(out_indices)+1]
        self.act = act
        self.seg_net = UnetHead(act=act)
        self.backbone = yolov5s_backbone
        self.dbnet = None
        self.forward_mode = forward_mode

    def train_mask(self):
        self.forward_mode = TEXTDET_MASK
        self.backbone.eval()
        self.seg_net.train()

    def initialize_db(self, unet_weights):
        self.dbnet = DBHead(64, act=self.act)
        self.seg_net.load_state_dict(torch.load(unet_weights, map_location='cpu')['weights'])
        self.dbnet.init_weight(init_weights)
        self.dbnet.upconv3 = copy.deepcopy(self.seg_net.upconv3)
        self.dbnet.upconv4 = copy.deepcopy(self.seg_net.upconv4)
        del self.seg_net.upconv3
        del self.seg_net.upconv4
        del self.seg_net.upconv5
        del self.seg_net.upconv6
        # del self.seg_net.conv_mask
    
    def train_db(self):
        self.forward_mode = TEXTDET_DET
        self.backbone.eval()
        self.seg_net.eval()
        self.dbnet.train()

    def forward(self, x):
        forward_mode = self.forward_mode
        with torch.no_grad():
            outs = self.backbone(x)
        if forward_mode == TEXTDET_MASK:
            return self.seg_net(*outs, forward_mode=forward_mode)
        elif forward_mode == TEXTDET_DET:
            with torch.no_grad():
                outs = self.seg_net(*outs, forward_mode=forward_mode)
            return self.dbnet(*outs)

def get_base_det_models(model_path, device='cpu', half=False, act='leaky'):
    textdetector_dict = torch.load(model_path, map_location=device)
    blk_det = load_yolov5_ckpt(textdetector_dict['blk_det'], map_location=device)
    text_seg = UnetHead(act=act)
    text_seg.load_state_dict(textdetector_dict['text_seg'])
    text_det = DBHead(64, act=act)
    text_det.load_state_dict(textdetector_dict['text_det'])
    if half:
        return blk_det.eval().half(), text_seg.eval().half(), text_det.eval().half()
    return blk_det.eval().to(device), text_seg.eval().to(device), text_det.eval().to(device)

class TextDetBase(nn.Module):
    def __init__(self, model_path, device='cpu', half=False, fuse=False, act='leaky'):
        super(TextDetBase, self).__init__()
        self.blk_det, self.text_seg, self.text_det = get_base_det_models(model_path, device, half, act=act)
        if fuse:
            self.fuse()

    def fuse(self):
        def _fuse(model):
            for m in model.modules():
                if isinstance(m, (Conv)) and hasattr(m, 'bn'):
                    m.conv = fuse_conv_and_bn(m.conv, m.bn)  # update conv
                    delattr(m, 'bn')  # remove batchnorm
                    m.forward = m.forward_fuse  # update forward
            return model
        self.text_seg = _fuse(self.text_seg)
        self.text_det = _fuse(self.text_det)

    def forward(self, features):
        blks, features = self.blk_det(features, detect=True)
        mask, features = self.text_seg(*features, forward_mode=TEXTDET_INFERENCE)
        lines = self.text_det(*features, step_eval=False)
        return blks[0], mask, lines

class TextDetBaseDNN:
    def __init__(self, input_size, model_path):
        self.input_size = input_size
        self.model = cv2.dnn.readNetFromONNX(model_path)
        self.uoln = self.model.getUnconnectedOutLayersNames()
    
    def __call__(self, im_in):
        blob = cv2.dnn.blobFromImage(im_in, scalefactor=1 / 255.0, size=(self.input_size, self.input_size))
        self.model.setInput(blob)
        blks, mask, lines_map  = self.model.forward(self.uoln)
        return blks, mask, lines_map

if __name__ == '__main__':
    device = 'cuda'
    weights = r'data/yolov5sblk.ckpt'

    # yolov5s_backbone = load_yolov5_ckpt(weights=weights, map_location='cpu')

    model = TextDetector(weights, map_location=DEVICE)
    model.to(DEVICE)
    model.train_mask()
    summary(model, (3, 640, 640), device=DEVICE)

    # model.initialize_db(unet_weights='data/unet_head.pt')
    # model.train_db()
    # summary(model, (3, 640, 640), device=DEVICE)
```

## `detector.py`

```py
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
```

## `inference.py`

```py
import json
from core.basemodel import TextDetBase, TextDetBaseDNN  # 修复导入路径
import os.path as osp
from tqdm import tqdm
import numpy as np
import cv2
import torch
from pathlib import Path
import torch
from utils.yolov5_utils import non_max_suppression  # 修复导入路径
from utils.db_utils import SegDetectorRepresenter  # 修复导入路径
from utils.io_utils import imread, imwrite, find_all_imgs, NumpyEncoder  # 修复导入路径
from utils.imgproc_utils import letterbox, xyxy2yolo, get_yololabel_strings  # 修复导入路径
from utils.textblock import TextBlock, group_output, visualize_textblocks  # 修复导入路径
from utils.textmask import refine_mask, refine_undetected_mask, REFINEMASK_INPAINT, REFINEMASK_ANNOTATION  # 修复导入路径
from pathlib import Path
from typing import Union

def model2annotations(model_path, img_dir_list, save_dir, save_json=False):
    if isinstance(img_dir_list, str):
        img_dir_list = [img_dir_list]
    cuda = torch.cuda.is_available()
    device = 'cuda' if cuda else 'cpu'
    model = TextDetector(model_path=model_path, input_size=1024, device=device, act='leaky')  
    imglist = []
    for img_dir in img_dir_list:
        imglist += find_all_imgs(img_dir, abs_path=True)
    for img_path in tqdm(imglist):
        imgname = osp.basename(img_path)
        img = imread(img_path)
        im_h, im_w = img.shape[:2]
        imname = imgname.replace(Path(imgname).suffix, '')
        maskname = 'mask-'+imname+'.png'
        poly_save_path = osp.join(save_dir, 'line-' + imname + '.txt')
        mask, mask_refined, blk_list = model(img, refine_mode=REFINEMASK_ANNOTATION, keep_undetected_mask=True)
        polys = []
        blk_xyxy = []
        blk_dict_list = []
        for blk in blk_list:
            polys += blk.lines
            blk_xyxy.append(blk.xyxy)
            blk_dict_list.append(blk.to_dict())
        blk_xyxy = xyxy2yolo(blk_xyxy, im_w, im_h)
        if blk_xyxy is not None:
            cls_list = [1] * len(blk_xyxy)
            yolo_label = get_yololabel_strings(cls_list, blk_xyxy)
        else:
            yolo_label = ''
        with open(osp.join(save_dir, imname+'.txt'), 'w', encoding='utf8') as f:
            f.write(yolo_label)

        if len(polys) != 0:
            if isinstance(polys, list):
                polys = np.array(polys)
            polys = polys.reshape(-1, 8)
            np.savetxt(poly_save_path, polys, fmt='%d')
        if save_json:
            with open(osp.join(save_dir, imname+'.json'), 'w', encoding='utf8') as f:
                f.write(json.dumps(blk_dict_list, ensure_ascii=False, cls=NumpyEncoder))
        imwrite(osp.join(save_dir, imgname), img)
        imwrite(osp.join(save_dir, maskname), mask_refined)

def preprocess_img(img, input_size=(1024, 1024), device='cpu', bgr2rgb=True, half=False, to_tensor=True):
    if bgr2rgb:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_in, ratio, (dw, dh) = letterbox(img, new_shape=input_size, auto=False, stride=64)
    if to_tensor:
        img_in = img_in.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
        img_in = np.array([np.ascontiguousarray(img_in)]).astype(np.float32) / 255
        if to_tensor:
            img_in = torch.from_numpy(img_in).to(device)
            if half:
                img_in = img_in.half()
    return img_in, ratio, int(dw), int(dh)

def postprocess_mask(img: Union[torch.Tensor, np.ndarray], thresh=None):
    # img = img.permute(1, 2, 0)
    if isinstance(img, torch.Tensor):
        img = img.squeeze_()
        if img.device != 'cpu':
            img = img.detach_().cpu()
        img = img.numpy()
    else:
        img = img.squeeze()
    if thresh is not None:
        img = img > thresh
    img = img * 255
    # if isinstance(img, torch.Tensor):

    return img.astype(np.uint8)

def postprocess_yolo(det, conf_thresh, nms_thresh, resize_ratio, sort_func=None):
    det = non_max_suppression(det, conf_thresh, nms_thresh)[0]
    # bbox = det[..., 0:4]
    if det.device != 'cpu':
        det = det.detach_().cpu().numpy()
    det[..., [0, 2]] = det[..., [0, 2]] * resize_ratio[0]
    det[..., [1, 3]] = det[..., [1, 3]] * resize_ratio[1]
    if sort_func is not None:
        det = sort_func(det)

    blines = det[..., 0:4].astype(np.int32)
    confs = np.round(det[..., 4], 3)
    cls = det[..., 5].astype(np.int32)
    return blines, cls, confs

class TextDetector:
    lang_list = ['eng', 'ja', 'unknown']
    langcls2idx = {'eng': 0, 'ja': 1, 'unknown': 2}

    def __init__(self, model_path, input_size=1024, device='cpu', half=False, nms_thresh=0.35, conf_thresh=0.4, mask_thresh=0.3, act='leaky'):
        super(TextDetector, self).__init__()
        cuda = device == 'cuda'

        if Path(model_path).suffix == '.onnx':
            self.model = cv2.dnn.readNetFromONNX(model_path)
            self.net = TextDetBaseDNN(input_size, model_path)
            self.backend = 'opencv'
        else:
            self.net = TextDetBase(model_path, device=device, act=act)
            self.backend = 'torch'
        
        if isinstance(input_size, int):
            input_size = (input_size, input_size)
        self.input_size = input_size
        self.device = device
        self.half = half
        self.conf_thresh = conf_thresh
        self.nms_thresh = nms_thresh
        self.mask_thresh = mask_thresh  # 添加 mask_thresh 属性
        self.seg_rep = SegDetectorRepresenter(thresh=0.3)

    @torch.no_grad()
    def __call__(self, img, refine_mode=REFINEMASK_INPAINT, keep_undetected_mask=False):
        img_in, ratio, dw, dh = preprocess_img(img, input_size=self.input_size, device=self.device, half=self.half, to_tensor=self.backend=='torch')
        im_h, im_w = img.shape[:2]

        blks, mask, lines_map = self.net(img_in)

        resize_ratio = (im_w / (self.input_size[0] - dw), im_h / (self.input_size[1] - dh))
        blks = postprocess_yolo(blks, self.conf_thresh, self.nms_thresh, resize_ratio)

        if self.backend == 'opencv':
            if mask.shape[1] == 2:     # some version of opencv spit out reversed result
                tmp = mask
                mask = lines_map
                lines_map = tmp
        mask = postprocess_mask(mask)

        lines, scores = self.seg_rep(self.input_size, lines_map)
        box_thresh = 0.6
        idx = np.where(scores[0] > box_thresh)
        lines, scores = lines[0][idx], scores[0][idx]
        
        # map output to input img
        mask = mask[: mask.shape[0]-dh, : mask.shape[1]-dw]
        mask = cv2.resize(mask, (im_w, im_h), interpolation=cv2.INTER_LINEAR)
        if lines.size == 0 :
            lines = []
        else :
            lines = lines.astype(np.float64)
            lines[..., 0] *= resize_ratio[0]
            lines[..., 1] *= resize_ratio[1]
            lines = lines.astype(np.int32)
        blk_list = group_output(blks, lines, im_w, im_h, mask)
        mask_refined = refine_mask(img, mask, blk_list, refine_mode=refine_mode)
        if keep_undetected_mask:
            mask_refined = refine_undetected_mask(img, mask, mask_refined, blk_list, refine_mode=refine_mode)
    
        return mask, mask_refined, blk_list

def traverse_by_dict(img_dir_list, dict_dir):
    if isinstance(img_dir_list, str):
        img_dir_list = [img_dir_list]
    imglist = []
    for img_dir in img_dir_list:
        imglist += find_all_imgs(img_dir, abs_path=True)
    for img_path in tqdm(imglist):
        imgname = osp.basename(img_path)
        imname = imgname.replace(Path(imgname).suffix, '')
        mask_path = osp.join(dict_dir, 'mask-'+imname+'.png')
        with open(osp.join(dict_dir, imname+'.json'), 'r', encoding='utf8') as f:
            blk_dict_list = json.loads(f.read())
            blk_list = [TextBlock(**blk_dict) for blk_dict in blk_dict_list]
        img = cv2.imread(img_path)
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        mask = refine_mask(img, mask, blk_list)

        visualize_textblocks(img, blk_list)
        cv2.imshow('im', img)
        cv2.imshow('mask', mask)
        cv2.waitKey(0)

if __name__ == '__main__':
    device = 'cpu'
    model_path = 'data/comictextdetector.pt'
    model_path = 'data/comictextdetector.pt.onnx'
    img_dir = r'data/examples'
    save_dir = r'data/backup'
    model2annotations(model_path, img_dir, save_dir, save_json=True)
    traverse_by_dict(img_dir, save_dir)
```

## `results.py`

```py
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
```

## `__init__.py`

```py

```

# `main.py`

```py
#!/usr/bin/env python3
"""
漫画文本检测器 - GUI模式
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ui.main_window import ComicTextDetectorGUI
from config.config import Config
from utils.general import set_logging

def main():
    """主函数 - 只启动GUI"""
    # 设置日志
    set_logging(verbose=False)
    
    try:
        from PyQt5.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        app.setApplicationName("漫画文本检测器")
        app.setApplicationVersion("1.0")
        
        # 创建主窗口
        window = ComicTextDetectorGUI()
        window.show()
        
        return app.exec_()
        
    except ImportError:
        print("错误：GUI模式需要安装PyQt5")
        print("请运行：pip install PyQt5")
        return 1
    except Exception as e:
        print(f"启动失败：{e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

# `ui`

## `event_handlers.py`

```py
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
        output_dir = str(input_folder.parent)
        
        # 【新增】创建项目结果对象并提前创建结构
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
        self.main_window.progress_bar.setRange(0, len(self.main_window.current_image_files))
        
        # 禁用控件
        self.main_window.detect_button.setEnabled(False)
        self.main_window.ocr_button.setEnabled(False)
        
        
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
        
        # 【新增】如果在项目模式下，立即保存检测结果
        if (self.main_window.current_project_folder and 
            hasattr(self.main_window, 'current_project_results')):
            self.main_window.current_project_results.update_image_detection_result(
                results, self.main_window.config.output_params)
        
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
        
        # 【新增】如果在项目模式下，立即保存OCR结果
        if (self.main_window.current_project_folder and 
            hasattr(self.main_window, 'current_project_results')):
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

    def _auto_save_results(self, results: DetectionResults, operation_type: str):
        """自动保存结果"""
        try:
            # 确定保存路径
            if self.main_window.current_project_folder:
                # 如果有项目文件夹，保存到项目文件夹同级的输出目录
                input_folder = Path(self.main_window.current_project_folder)
                project_name = f"{input_folder.name}_{operation_type}"
                output_dir = str(input_folder.parent)
            else:
                # 如果是单个文件，保存到图片同级目录
                image_path = Path(results.image_path)
                project_name = f"{image_path.stem}_{operation_type}"
                output_dir = str(image_path.parent)
            
            # 使用检测器的保存方法
            saved_dir = self.main_window.detector.save_results(results, output_dir)
            
            print(f"结果已自动保存到: {saved_dir}")
            
        except Exception as e:
            print(f"自动保存失败: {e}")
            # 可以选择显示错误提示，但不阻断流程

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
```

## `main_window.py`

```py
"""
GUI应用主类 - 简化版本（模块化）
"""

import sys
from pathlib import Path
from typing import Optional, List

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
except ImportError:
    raise ImportError("PyQt5未安装，请运行：pip install PyQt5")

from core.detector import ComicTextDetector, DetectionResults
from core.results import ProjectResults
from ui.widgets.image_viewer import ImageViewer
from ui.widgets.parameter_panel import ParameterPanel
from ui.menu_manager import MenuManager
from ui.event_handlers import EventHandlers
from config.config import Config


class ComicTextDetectorGUI(QMainWindow):
    """漫画文本检测器GUI主窗口 - 模块化版本"""
    
    def __init__(self):
        super().__init__()
        
        # 配置
        self.config = Config()
        
        # 应用状态
        self.detector: Optional[ComicTextDetector] = None
        self.current_results: Optional[DetectionResults] = None
        self.current_image_path: Optional[str] = None
        self.recent_files: List[str] = []
        
        # 项目管理
        self.current_project_folder: Optional[str] = None
        self.current_image_files: List[str] = []
        self.current_image_index: int = 0
        self.current_project_results: Optional[ProjectResults] = None

        # 工作线程（由事件处理器管理）
        self.detection_worker = None
        self.ocr_worker = None
        self.batch_worker = None
        
        # 管理器和处理器
        self.menu_manager: Optional[MenuManager] = None
        self.event_handlers: Optional[EventHandlers] = None
        
        # 初始化UI和管理器
        self.init_ui()
        self.init_managers()
        self.init_detector()
        self.event_handlers.load_settings()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("漫画文本检测器 v1.0 (模块化版)")
        self.setMinimumSize(1000, 700)
        
        # 设置窗口大小
        gui_config = self.config.gui_params
        if 'window_size' in gui_config:
            self.resize(*gui_config['window_size'])
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧面板 - 参数控制
        self.parameter_panel = ParameterPanel(self.config)
        main_layout.addWidget(self.parameter_panel, stretch=0)
        
        # 右侧面板 - 图像显示和控制
        right_widget = self.create_right_panel()
        main_layout.addWidget(right_widget, stretch=1)
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
    
    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 控制按钮区域
        control_widget = self.create_control_buttons()
        right_layout.addWidget(control_widget)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)
        
        # 图像查看器
        self.image_viewer = ImageViewer()
        right_layout.addWidget(self.image_viewer, stretch=1)
        
        # 导航和状态栏
        nav_status_widget = self.create_navigation_bar()
        right_layout.addWidget(nav_status_widget)
        
        return right_widget
    
    def create_control_buttons(self) -> QWidget:
        """创建控制按钮"""
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(5, 5, 5, 5)
        
        # 检测按钮
        self.detect_button = QPushButton("🔍 开始检测")
        self.detect_button.setStyleSheet(self.get_button_style("#2196F3", "#1976D2"))
        self.detect_button.setEnabled(False)
        control_layout.addWidget(self.detect_button)
        
        # OCR按钮
        self.ocr_button = QPushButton("📝 OCR识别")
        self.ocr_button.setStyleSheet(self.get_button_style("#4CAF50", "#45a049"))
        self.ocr_button.setEnabled(False)
        control_layout.addWidget(self.ocr_button)
        
        control_layout.addStretch()
        return control_widget
    
    def create_navigation_bar(self) -> QWidget:
        """创建导航栏"""
        nav_status_widget = QWidget()
        nav_status_layout = QHBoxLayout(nav_status_widget)
        nav_status_layout.setContentsMargins(0, 5, 0, 5)

        # 导航按钮
        self.prev_button = QPushButton("⬅️ 上一张")
        self.prev_button.setEnabled(False)
        nav_status_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("下一张 ➡️")
        self.next_button.setEnabled(False)
        nav_status_layout.addWidget(self.next_button)
        
        nav_status_layout.addStretch()
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666666; font-size: 12px;")
        nav_status_layout.addWidget(self.status_label)

        return nav_status_widget
    
    def get_button_style(self, bg_color: str, hover_color: str) -> str:
        """获取按钮样式"""
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
        """
    
    def init_managers(self):
        """初始化管理器和处理器"""
        # 创建菜单管理器
        self.menu_manager = MenuManager(self)
        self.menu_manager.create_menu_bar()
        
        # 创建事件处理器
        self.event_handlers = EventHandlers(self)
        
        # 连接信号
        self.connect_signals()
    
    def connect_signals(self):
        """连接所有信号"""
        # 菜单信号
        self.menu_manager.open_folder_requested.connect(
            self.event_handlers.handle_open_folder)
        self.menu_manager.batch_detection_requested.connect(
            self.event_handlers.handle_batch_detection)
        self.menu_manager.batch_ocr_requested.connect(
            self.event_handlers.handle_batch_ocr)
        self.menu_manager.exit_requested.connect(self.close)
        
        self.menu_manager.toggle_regions_requested.connect(
            self.event_handlers.handle_toggle_regions)
        self.menu_manager.toggle_lines_requested.connect(
            self.event_handlers.handle_toggle_lines)
        self.menu_manager.toggle_blocks_requested.connect(
            self.event_handlers.handle_toggle_blocks)
        
        self.menu_manager.start_detection_requested.connect(
            self.event_handlers.handle_start_detection)
        self.menu_manager.start_ocr_requested.connect(
            self.event_handlers.handle_start_ocr)
        
        self.menu_manager.about_requested.connect(
            self.event_handlers.handle_show_about)
        
        # 按钮信号
        self.detect_button.clicked.connect(
            self.event_handlers.handle_start_detection)
        self.ocr_button.clicked.connect(
            self.event_handlers.handle_start_ocr)
        
        # 导航按钮信号
        self.prev_button.clicked.connect(
            self.event_handlers.handle_prev_image)
        self.next_button.clicked.connect(
            self.event_handlers.handle_next_image)
        
        # 参数面板信号
        self.parameter_panel.parameters_changed.connect(self.on_parameters_changed)
        self.parameter_panel.ocr_text_modified.connect(self.on_ocr_text_modified)
    
    def init_detector(self):
        """初始化检测器"""
        try:
            model_path = self.parameter_panel.get_model_path()
            if model_path and Path(model_path).exists():
                params = self.parameter_panel.get_parameters()
                self.detector = ComicTextDetector(
                    model_path=model_path,
                    config=self.config,
                    enable_ocr=True,  # 总是启用OCR，但分离执行
                    **params
                )
                device_info = f"({self.detector.device})" if hasattr(self.detector, 'device') else ""
                self.statusBar().showMessage(f"检测器已加载: {Path(model_path).name} {device_info}")
            else:
                self.statusBar().showMessage("请选择模型文件")
        except Exception as e:
            QMessageBox.warning(self, "警告", f"检测器初始化失败: {e}")
            self.statusBar().showMessage("检测器初始化失败")
    
    def on_parameters_changed(self):
        """参数变化回调"""
        if hasattr(self, 'detector') and self.detector:
            try:
                params = self.parameter_panel.get_parameters()
                model_path = self.parameter_panel.get_model_path()
                
                # 检查是否需要重新初始化检测器
                need_reinit = (model_path != self.detector.model_path or 
                             params.get('device') != self.detector.device)
                
                if need_reinit:
                    self.init_detector()
                else:
                    self.detector.update_parameters(**params)
            except Exception as e:
                QMessageBox.warning(self, "警告", f"参数更新失败: {e}")

    def on_ocr_text_modified(self, region_idx: int, new_text: str):
        """OCR文本修改回调 - 自动保存"""
        if self.current_results:
            try:
                # 更新可视化（如果需要重新生成带OCR文本的结果图）
                self.image_viewer.set_detection_regions(self.current_results.text_regions)
                
                # 更新状态栏
                self.statusBar().showMessage(f"区域{region_idx}的OCR文本已修改并保存")
                
            except Exception as e:
                print(f"保存OCR修改时出错: {e}")
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 停止所有工作线程
        workers = [
            ('detection_worker', "检测"),
            ('ocr_worker', "OCR识别"), 
            ('batch_worker', "批量处理")
        ]
        
        running_workers = []
        for worker_name, worker_desc in workers:
            if hasattr(self, worker_name):
                worker = getattr(self, worker_name)
                if worker and worker.isRunning():
                    running_workers.append(worker_desc)
        
        if running_workers:
            reply = QMessageBox.question(
                self, "确认退出", 
                f"以下任务正在进行中：{', '.join(running_workers)}\n确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            
            # 停止所有线程
            for worker_name, _ in workers:
                if hasattr(self, worker_name):
                    worker = getattr(self, worker_name)
                    if worker and worker.isRunning():
                        worker.quit()
                        worker.wait()
        
        # 保存设置并清理资源
        if self.event_handlers:
            self.event_handlers.save_settings()
        
        if self.detector:
            del self.detector
        
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("漫画文本检测器")
    app.setApplicationVersion("1.0")
    
    window = ComicTextDetectorGUI()
    window.show()
    
    sys.exit(app.exec_())
```

## `menu_manager.py`

```py
"""
菜单管理器 - 负责创建和管理所有菜单
"""

from pathlib import Path
from typing import List, Callable
from PyQt5.QtWidgets import QAction, QMenu
from PyQt5.QtCore import QObject, pyqtSignal


class MenuManager(QObject):
    """菜单管理器"""
    
    # 信号定义
    open_folder_requested = pyqtSignal()
    batch_detection_requested = pyqtSignal()
    batch_ocr_requested = pyqtSignal()
    exit_requested = pyqtSignal()
    
    toggle_regions_requested = pyqtSignal()
    toggle_lines_requested = pyqtSignal()
    toggle_blocks_requested = pyqtSignal()
    
    start_detection_requested = pyqtSignal()
    start_ocr_requested = pyqtSignal()
    
    about_requested = pyqtSignal()
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.recent_menu = None
        
        # 菜单动作存储
        self.toggle_regions_action = None
        self.toggle_lines_action = None
        self.toggle_blocks_action = None
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.main_window.menuBar()
        
        # 文件菜单
        self._create_file_menu(menubar)
        
        # 视图菜单
        self._create_view_menu(menubar)
        
        # 处理菜单
        self._create_process_menu(menubar)
        
        # 帮助菜单
        self._create_help_menu(menubar)
    
    def _create_file_menu(self, menubar):
        """创建文件菜单"""
        file_menu = menubar.addMenu('文件(&F)')
        
        # 打开项目文件夹
        open_action = QAction('打开项目文件夹(&O)', self.main_window)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_folder_requested.emit)
        file_menu.addAction(open_action)
        
        # 最近项目菜单
        self.recent_menu = file_menu.addMenu('最近项目(&R)')
        
        file_menu.addSeparator()
        
        # 批量处理
        batch_action = QAction('批量处理（仅检测）- 自动输出(&B)', self.main_window)
        batch_action.triggered.connect(self.batch_detection_requested.emit)
        file_menu.addAction(batch_action)

        # 批量处理（包含OCR）
        batch_ocr_action = QAction('批量处理（含OCR）- 自动输出(&M)', self.main_window)
        batch_ocr_action.triggered.connect(self.batch_ocr_requested.emit)
        file_menu.addAction(batch_ocr_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction('退出(&X)', self.main_window)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.exit_requested.emit)
        file_menu.addAction(exit_action)

    def _create_view_menu(self, menubar):
        """创建视图菜单"""
        view_menu = menubar.addMenu('视图(&V)')
        
        # 显示检测区域
        self.toggle_regions_action = QAction('显示检测区域(&R)', self.main_window)
        self.toggle_regions_action.setShortcut('Ctrl+R')
        self.toggle_regions_action.setCheckable(True)
        self.toggle_regions_action.setChecked(True)
        self.toggle_regions_action.triggered.connect(self.toggle_regions_requested.emit)
        view_menu.addAction(self.toggle_regions_action)

        # 显示文本行
        self.toggle_lines_action = QAction('显示文本行(&L)', self.main_window)
        self.toggle_lines_action.setShortcut('Ctrl+L')
        self.toggle_lines_action.setCheckable(True)
        self.toggle_lines_action.setChecked(True)
        self.toggle_lines_action.triggered.connect(self.toggle_lines_requested.emit)
        view_menu.addAction(self.toggle_lines_action)

        # 显示文本块
        self.toggle_blocks_action = QAction('显示文本块(&B)', self.main_window)
        self.toggle_blocks_action.setShortcut('Ctrl+Shift+B')
        self.toggle_blocks_action.setCheckable(True)
        self.toggle_blocks_action.setChecked(True)
        self.toggle_blocks_action.triggered.connect(self.toggle_blocks_requested.emit)
        view_menu.addAction(self.toggle_blocks_action)

    def _create_process_menu(self, menubar):
        """创建处理菜单"""
        process_menu = menubar.addMenu('处理(&P)')
        
        # 开始检测
        detect_action = QAction('开始检测(&D)', self.main_window)
        detect_action.setShortcut('F5')
        detect_action.triggered.connect(self.start_detection_requested.emit)
        process_menu.addAction(detect_action)
        
        # OCR识别
        ocr_action = QAction('OCR识别(&O)', self.main_window)
        ocr_action.setShortcut('F6')
        ocr_action.triggered.connect(self.start_ocr_requested.emit)
        process_menu.addAction(ocr_action)

    def _create_help_menu(self, menubar):
        """创建帮助菜单"""
        help_menu = menubar.addMenu('帮助(&H)')
        
        about_action = QAction('关于(&A)', self.main_window)
        about_action.triggered.connect(self.about_requested.emit)
        help_menu.addAction(about_action)
    
    def update_recent_menu(self, recent_files: List[str], load_callback: Callable[[str], None]):
        """更新最近项目文件夹菜单"""
        if not self.recent_menu:
            return
            
        self.recent_menu.clear()
        
        for i, folder_path in enumerate(recent_files):
            if Path(folder_path).exists():
                # 显示文件夹名 + 上级目录，避免路径过长
                folder_name = Path(folder_path).name
                parent_name = Path(folder_path).parent.name
                display_name = f"{parent_name}/{folder_name}" if parent_name != folder_name else folder_name
                
                action = QAction(f"{i+1}. {display_name}", self.main_window)
                # 设置工具提示显示完整路径
                action.setToolTip(folder_path)
                action.triggered.connect(lambda checked, path=folder_path: load_callback(path))
                self.recent_menu.addAction(action)
        
        if not recent_files:
            action = QAction("(空)", self.main_window)
            action.setEnabled(False)
            self.recent_menu.addAction(action)
    
    def update_toggle_actions_text(self, show_regions: bool, show_lines: bool, show_blocks: bool):
        """更新切换动作的文本"""
        if self.toggle_regions_action:
            self.toggle_regions_action.setText('隐藏检测区域(&R)' if show_regions else '显示检测区域(&R)')
        
        if self.toggle_lines_action:
            self.toggle_lines_action.setText('隐藏文本行(&L)' if show_lines else '显示文本行(&L)')
        
        if self.toggle_blocks_action:
            self.toggle_blocks_action.setText('隐藏文本块(&B)' if show_blocks else '显示文本块(&B)')
```

## `widgets`

### `image_viewer.py`

```py
"""
图像查看器组件
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *



class ImageViewer(QScrollArea):
    """图像查看器组件"""
    
    image_clicked = pyqtSignal(QPoint)
    region_selected = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        
        # 图像标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("QLabel { background-color: #f0f0f0; }")
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setScaledContents(False)
        
        # 设置滚动区域
        self.setWidget(self.image_label)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignCenter)
        
        # 图像数据
        self.original_image: Optional[np.ndarray] = None
        self.result_image: Optional[np.ndarray] = None
        self.current_pixmap: Optional[QPixmap] = None
        
        # 检测区域
        self.detection_regions: List[Dict] = []
        self.selected_region: Optional[int] = None
        
        # 显示状态
        self.zoom_factor = 1.0
        self.show_original = True
        self.show_regions = True
        self.show_lines = True
        self.show_blocks = True
        self.auto_fit = True
        
        # 鼠标事件
        self.image_label.mousePressEvent = self.mouse_press_event
        
        # 初始化UI
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        # 右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # 默认显示
        self.show_placeholder()
    
    def show_placeholder(self):
        """显示占位符"""
        pixmap = QPixmap(400, 300)
        pixmap.fill(Qt.lightGray)
        
        painter = QPainter(pixmap)
        painter.setPen(Qt.darkGray)
        painter.setFont(QFont("Arial", 14))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "点击打开图片\n或拖拽图片到此处")
        painter.end()
        
        self.image_label.setPixmap(pixmap)
    
    def load_image(self, image_path: str):
        """加载图片"""
        try:
            # 使用OpenCV读取图片
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError("无法读取图片文件")
            
            # 转换为RGB格式
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            self.original_image = img_rgb.copy()
            self.result_image = None
            
            # 清空检测结果
            self.detection_regions.clear()
            self.selected_region = None
            
            # 显示图片
            self.display_image(self.original_image)
            
            # 重置缩放
            self.zoom_factor = 1.0
            self.fit_to_window()
            
        except Exception as e:
            self.show_error(f"加载图片失败: {e}")

    def toggle_blocks(self):
        """切换文本块显示"""
        self.show_blocks = not self.show_blocks
        self.update_display()
    
    def resizeEvent(self, event):
        """窗口大小改变事件处理"""
        super().resizeEvent(event)
        if self.auto_fit and self.current_pixmap is not None:
            # 延迟执行适应窗口，避免频繁调用
            QTimer.singleShot(100, self.fit_to_window)
    
    def set_result_image(self, result_image: np.ndarray):
        """设置检测结果图片"""
        self.result_image = result_image.copy()
        if not self.show_original:
            self.display_image(self.result_image)
    
    def set_detection_regions(self, regions: List[Dict]):
        """设置检测区域"""
        self.detection_regions = regions
        self.update_display()
    
    def display_image(self, image: np.ndarray):
        """显示图片"""
        if image is None:
            return
        
        try:
            # 创建QImage
            h, w, ch = image.shape
            bytes_per_line = ch * w
            q_image = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # 转换为QPixmap
            pixmap = QPixmap.fromImage(q_image)
            
            # 如果需要显示检测区域，在图片上绘制
            if self.show_regions and self.detection_regions:
                pixmap = self.draw_regions_on_pixmap(pixmap)
            
            self.current_pixmap = pixmap
            
            # 应用缩放
            scaled_pixmap = pixmap.scaled(
                pixmap.size() * self.zoom_factor,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            self.image_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            self.show_error(f"显示图片失败: {e}")
    
    def draw_regions_on_pixmap(self, pixmap: QPixmap) -> QPixmap:
        """在pixmap上绘制检测区域"""
        if not self.detection_regions:
            return pixmap
        
        # 创建副本进行绘制
        result_pixmap = pixmap.copy()
        painter = QPainter(result_pixmap)
        
        try:
            # 绘制文本块（检测区域）
            if self.show_regions and self.show_blocks:  # 添加 show_blocks 条件
                for i, region in enumerate(self.detection_regions):
                    x1, y1, x2, y2 = region['bbox']
                    
                    # 设置颜色
                    if i == self.selected_region:
                        color = QColor(255, 0, 0)  # 选中区域红色
                        line_width = 3
                    else:
                        confidence = region.get('confidence', 1.0)
                        blue_value = int(255 * min(confidence, 1.0))
                        color = QColor(50, 100, blue_value)
                        line_width = 2
                    
                    # 绘制边界框
                    pen = QPen(color, line_width)
                    painter.setPen(pen)
                    painter.drawRect(x1, y1, x2 - x1, y2 - y1)
                    
                    # 绘制标签
                    label = f"{i}_{region['language']}"
                    if region.get('vertical', False):
                        label += "_V"
                    if 'confidence' in region:
                        label += f"_{region['confidence']:.3f}"
                    
                    # 标签背景
                    font = QFont("Arial", 16)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    text_rect = fm.boundingRect(label)
                    text_rect.moveTopLeft(QPoint(x1, y1 - text_rect.height() - 2))
                    
                    painter.fillRect(text_rect.adjusted(-2, -2, 2, 2), color)
                    painter.setPen(QPen(Qt.white))
                    painter.drawText(text_rect, Qt.AlignCenter, label)
            
            # 绘制文本行
            if self.show_lines:
                cyan_color = QColor(0, 255, 255)  # 青色
                pen = QPen(cyan_color, 1)
                painter.setPen(pen)
                
                for i, region in enumerate(self.detection_regions):
                    # 从TextBlock对象获取文本行数据
                    if hasattr(region, 'lines') and region.lines:
                        lines = region.lines
                    elif 'lines' in region and region['lines']:
                        lines = region['lines']
                    else:
                        continue
                    
                    # 绘制每个文本行
                    for line_idx, line_coords in enumerate(lines):
                        if len(line_coords) >= 4:
                            points = []
                            for coord in line_coords:
                                if len(coord) >= 2:
                                    points.append(QPoint(int(coord[0]), int(coord[1])))
                            
                            if len(points) >= 3:
                                polygon = QPolygon(points)
                                painter.drawPolygon(polygon)
        
        finally:
            painter.end()
        
        return result_pixmap
        
    def toggle_lines(self):
        """切换文本行显示"""
        self.show_lines = not self.show_lines
        self.update_display()

    def update_display(self):
        """更新显示"""
        if self.show_original and self.original_image is not None:
            self.display_image(self.original_image)
        elif not self.show_original and self.result_image is not None:
            self.display_image(self.result_image)
    
    def toggle_view(self):
        """切换原图/结果图显示"""
        if self.result_image is not None:
            self.show_original = not self.show_original
            self.update_display()
    
    def toggle_regions(self):
        """切换区域显示"""
        self.show_regions = not self.show_regions
        self.update_display()
    
    def zoom_in(self):
        """放大"""
        self.zoom_factor = min(self.zoom_factor * 1.25, 5.0)
        self.update_display()
    
    def zoom_out(self):
        """缩小"""
        self.zoom_factor = max(self.zoom_factor / 1.25, 0.1)
        self.update_display()
    
    def fit_to_window(self):
        """适应窗口"""
        if self.current_pixmap is None:
            return
        
        # 计算合适的缩放因子
        label_size = self.image_label.size()
        pixmap_size = self.current_pixmap.size()
        
        scale_x = label_size.width() / pixmap_size.width()
        scale_y = label_size.height() / pixmap_size.height()
        
        self.zoom_factor = min(scale_x, scale_y, 1.0)
        self.update_display()
    
    def actual_size(self):
        """实际大小"""
        self.zoom_factor = 1.0
        self.update_display()
    
    def mouse_press_event(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton and self.current_pixmap:
            # 转换坐标到原图坐标系
            click_pos = event.pos()
            
            # 发射点击信号
            self.image_clicked.emit(click_pos)
            
            # 检查是否点击了检测区域
            self.check_region_click(click_pos)

    def toggle_auto_fit(self):
        """切换自动适应模式"""
        self.auto_fit = not self.auto_fit
        if self.auto_fit and self.current_pixmap is not None:
            self.fit_to_window()
    
    def check_region_click(self, click_pos: QPoint):
        """检查是否点击了检测区域"""
        if not self.detection_regions or not self.current_pixmap:
            return
        
        # 转换点击坐标
        label_rect = self.image_label.rect()
        pixmap_rect = self.current_pixmap.rect()
        
        # 计算图片在label中的实际位置
        if self.current_pixmap.width() <= label_rect.width():
            x_offset = (label_rect.width() - self.current_pixmap.width()) // 2
        else:
            x_offset = 0
        
        if self.current_pixmap.height() <= label_rect.height():
            y_offset = (label_rect.height() - self.current_pixmap.height()) // 2
        else:
            y_offset = 0
        
        # 转换到原图坐标
        img_x = (click_pos.x() - x_offset) / self.zoom_factor
        img_y = (click_pos.y() - y_offset) / self.zoom_factor
        
        # 检查点击的区域
        for i, region in enumerate(self.detection_regions):
            x1, y1, x2, y2 = region['bbox']
            if x1 <= img_x <= x2 and y1 <= img_y <= y2:
                self.selected_region = i if self.selected_region != i else None
                self.update_display()
                self.region_selected.emit(i if self.selected_region is not None else -1)
                break
    
    def show_context_menu(self, pos):
        """显示右键菜单"""
        menu = QMenu(self)
        
        if self.original_image is not None:
            # 只保留视图切换功能（如果有结果图的话）
            if self.result_image is not None:
                toggle_action = QAction("切换到结果图" if self.show_original else "切换到原图", self)
                toggle_action.triggered.connect(self.toggle_view)
                menu.addAction(toggle_action)
            
            # 如果菜单不为空才显示
            if menu.actions():
                menu.exec_(self.mapToGlobal(pos))
    
    def show_error(self, message: str):
        """显示错误信息"""
        pixmap = QPixmap(400, 100)
        pixmap.fill(Qt.white)
        
        painter = QPainter(pixmap)
        painter.setPen(Qt.red)
        painter.setFont(QFont("Arial", 12))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, message)
        painter.end()
        
        self.image_label.setPixmap(pixmap)
    
    def get_selected_region(self) -> Optional[Dict]:
        """获取选中的区域"""
        if self.selected_region is not None and 0 <= self.selected_region < len(self.detection_regions):
            return self.detection_regions[self.selected_region]
        return None
    
    def clear(self):
        """清空显示"""
        self.original_image = None
        self.result_image = None
        self.current_pixmap = None
        self.detection_regions.clear()
        self.selected_region = None
        self.show_placeholder()


# 支持拖拽的图像查看器
class DragDropImageViewer(ImageViewer):
    """支持拖拽的图像查看器"""
    
    file_dropped = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            # 检查是否为图片文件
            image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif'}
            for file_path in files:
                if Path(file_path).suffix.lower() in image_extensions:
                    self.file_dropped.emit(file_path)
                    break
```

### `parameter_panel.py`

```py
"""
参数控制面板组件 - 清理版本
"""

from pathlib import Path
from typing import Dict, Any
import torch
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from config.config import Config


class ParameterPanel(QWidget):
    """参数控制面板"""
    
    parameters_changed = pyqtSignal()
    ocr_text_modified = pyqtSignal(int, str)  # 新增：OCR文本修改信号(region_idx, new_text)
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        
        # 控件引用
        self.model_path_edit = None
        self.device_combo = None
        self.input_size_combo = None
        self.conf_thresh_input = None
        self.mask_thresh_input = None
        self.containment_input = None
        self.min_box_width_spin = None
        self.min_box_height_spin = None
        self.enable_filter_checkbox = None
        self.lang_checkboxes = {}
        self.ocr_results_widgets = {}  # 存储OCR结果编辑控件
        self.current_detection_results = None  # 当前检测结果对象
        
        # 初始化UI
        self.init_ui()
        self.load_parameters()
    
    def init_ui(self):
        """初始化UI"""
        self.setFixedWidth(300)
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("检测参数")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        # 模型选择组
        model_group = self.create_model_group()
        layout.addWidget(model_group)
        
        # 设备和尺寸配置组
        config_group = self.create_config_group()
        layout.addWidget(config_group)
        
        # 检测参数组
        detection_group = self.create_detection_group()
        layout.addWidget(detection_group)
        
        # 语言选择组
        language_group = self.create_language_group()
        layout.addWidget(language_group)
        
        # OCR结果组
        ocr_group = self.create_ocr_group()
        layout.addWidget(ocr_group)
        
        # 弹簧，将控件推到顶部
        layout.addStretch()
        
        # 按钮区域
        button_layout = QVBoxLayout()
        
        # 重置参数按钮
        reset_button = QPushButton("重置参数")
        reset_button.clicked.connect(self.reset_parameters)
        button_layout.addWidget(reset_button)
        
        # 更新配置按钮
        self.update_config_button = QPushButton("更新默认配置")
        self.update_config_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.update_config_button.clicked.connect(self.update_default_config)
        button_layout.addWidget(self.update_config_button)
        
        layout.addLayout(button_layout)

    def create_model_group(self) -> QGroupBox:
        """创建模型选择组"""
        group = QGroupBox("模型设置")
        layout = QVBoxLayout(group)
        
        # 模型路径选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("模型文件:"))
        
        self.model_path_edit = QLineEdit()
        self.model_path_edit.setPlaceholderText("选择模型文件...")
        self.model_path_edit.textChanged.connect(self.parameters_changed.emit)
        model_layout.addWidget(self.model_path_edit, 1)
        
        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(self.browse_model)
        model_layout.addWidget(browse_button)
        
        layout.addLayout(model_layout)
        return group

    def create_config_group(self) -> QGroupBox:
        """创建配置参数组"""
        group = QGroupBox("运行配置")
        layout = QVBoxLayout(group)
        
        # 设备选择
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("计算设备:"))
        
        self.device_combo = QComboBox()
        
        # 检测可用设备
        devices = ["auto", "cpu"]
        if torch.cuda.is_available():
            devices.append("cuda")
            # 添加多GPU支持
            for i in range(torch.cuda.device_count()):
                devices.append(f"cuda:{i}")
        
        self.device_combo.addItems(devices)
        self.device_combo.setCurrentText("auto")
        self.device_combo.currentTextChanged.connect(self.parameters_changed.emit)
        
        device_layout.addWidget(self.device_combo)
        device_layout.addStretch()
        layout.addLayout(device_layout)

        # 输入尺寸选择
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("输入尺寸:"))
        
        self.input_size_combo = QComboBox()
        self.input_size_combo.addItems(["1024", "1280", "1536"])
        self.input_size_combo.setCurrentText("1280")
        self.input_size_combo.currentTextChanged.connect(self.parameters_changed.emit)
        
        size_layout.addWidget(self.input_size_combo)
        size_layout.addStretch()
        layout.addLayout(size_layout)
        
        return group

    def create_detection_group(self) -> QGroupBox:
        """创建检测参数组"""
        group = QGroupBox("检测参数")
        layout = QVBoxLayout(group)
        
        # 置信度阈值
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(QLabel("置信度阈值:"))
        
        self.conf_thresh_input = QDoubleSpinBox()
        self.conf_thresh_input.setRange(0.01, 0.99)
        self.conf_thresh_input.setSingleStep(0.01)
        self.conf_thresh_input.setDecimals(2)
        self.conf_thresh_input.setValue(0.40)
        self.conf_thresh_input.valueChanged.connect(self.parameters_changed.emit)
        
        conf_layout.addWidget(self.conf_thresh_input)
        conf_layout.addStretch()
        layout.addLayout(conf_layout)
        
        # 掩码阈值
        mask_layout = QHBoxLayout()
        mask_layout.addWidget(QLabel("掩码阈值:"))
        
        self.mask_thresh_input = QDoubleSpinBox()
        self.mask_thresh_input.setRange(0.01, 0.80)
        self.mask_thresh_input.setSingleStep(0.01)
        self.mask_thresh_input.setDecimals(2)
        self.mask_thresh_input.setValue(0.30)
        self.mask_thresh_input.valueChanged.connect(self.parameters_changed.emit)
        
        mask_layout.addWidget(self.mask_thresh_input)
        mask_layout.addStretch()
        layout.addLayout(mask_layout)
        
        # 包含关系阈值
        contain_layout = QHBoxLayout()
        contain_layout.addWidget(QLabel("包含关系阈值:"))
        
        self.containment_input = QDoubleSpinBox()
        self.containment_input.setRange(0.50, 1.00)
        self.containment_input.setSingleStep(0.01)
        self.containment_input.setDecimals(2)
        self.containment_input.setValue(0.80)
        self.containment_input.valueChanged.connect(self.parameters_changed.emit)
        
        contain_layout.addWidget(self.containment_input)
        contain_layout.addStretch()
        layout.addLayout(contain_layout)
        
        # 最小框尺寸
        min_size_layout = QHBoxLayout()
        min_size_layout.addWidget(QLabel("最小框尺寸:"))

        self.min_box_width_spin = QSpinBox()
        self.min_box_width_spin.setRange(1, 500)
        self.min_box_width_spin.setValue(10)
        self.min_box_width_spin.setSuffix(" px")
        self.min_box_width_spin.valueChanged.connect(self.parameters_changed.emit)

        self.min_box_height_spin = QSpinBox()
        self.min_box_height_spin.setRange(1, 500)
        self.min_box_height_spin.setValue(10)
        self.min_box_height_spin.setSuffix(" px")
        self.min_box_height_spin.valueChanged.connect(self.parameters_changed.emit)

        min_size_layout.addWidget(QLabel("宽:"))
        min_size_layout.addWidget(self.min_box_width_spin)
        min_size_layout.addWidget(QLabel("高:"))
        min_size_layout.addWidget(self.min_box_height_spin)
        min_size_layout.addStretch()
        layout.addLayout(min_size_layout)
        
        # 启用框过滤
        self.enable_filter_checkbox = QCheckBox("启用框过滤")
        self.enable_filter_checkbox.setChecked(True)
        self.enable_filter_checkbox.stateChanged.connect(self.parameters_changed.emit)
        layout.addWidget(self.enable_filter_checkbox)

        return group
      
    def create_language_group(self) -> QGroupBox:
        """创建语言选择组"""
        group = QGroupBox("支持语言")
        layout = QVBoxLayout(group)
        
        languages = [
            ("zh", "中文"),
            ("ja", "日文"), 
            ("eng", "英文"),
            ("unknown", "未知")
        ]
        
        for lang_code, lang_name in languages:
            checkbox = QCheckBox(lang_name)
            if lang_code in ["zh", "ja"]:  # 默认选中中文和日文
                checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.parameters_changed.emit)
            self.lang_checkboxes[lang_code] = checkbox
            layout.addWidget(checkbox)
        
        return group
    
    def browse_model(self):
        """浏览模型文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择模型文件",
            str(self.config.models_dir),
            "模型文件 (*.pt *.pth *.onnx)"
        )
        
        if file_path:
            self.model_path_edit.setText(file_path)
    
    def get_model_path(self) -> str:
        """获取模型路径"""
        return self.model_path_edit.text().strip()
    
    def get_parameters(self) -> Dict[str, Any]:
        """获取参数"""
        # 获取选中的语言
        allowed_languages = []
        for lang_code, checkbox in self.lang_checkboxes.items():
            if checkbox.isChecked():
                allowed_languages.append(lang_code)
        
        params = {
            "input_size": int(self.input_size_combo.currentText()),
            "conf_thresh": self.conf_thresh_input.value(),
            "mask_thresh": self.mask_thresh_input.value(),
            "allowed_languages": allowed_languages,
            "device": self.device_combo.currentText(),
            "containment_thresh": self.containment_input.value(),
            "enable_box_filter": self.enable_filter_checkbox.isChecked(),
            "min_box_width": self.min_box_width_spin.value(),
            "min_box_height": self.min_box_height_spin.value()
        }
        
        return params

    def set_parameters(self, params: Dict[str, Any]):
        """设置参数"""
        # 阻止信号发射
        self.blockSignals(True)
        
        try:
            # 设置输入尺寸
            if "input_size" in params:
                self.input_size_combo.setCurrentText(str(params["input_size"]))
            
            # 设置设备
            if "device" in params:
                self.device_combo.setCurrentText(params["device"])
            
            # 设置置信度阈值
            if "conf_thresh" in params:
                self.conf_thresh_input.setValue(params["conf_thresh"])
            
            # 设置掩码阈值
            if "mask_thresh" in params:
                self.mask_thresh_input.setValue(params["mask_thresh"])
            
            # 设置包含关系阈值
            if "containment_thresh" in params:
                self.containment_input.setValue(params["containment_thresh"])
            
            # 设置语言选择
            if "allowed_languages" in params:
                allowed_langs = params["allowed_languages"]
                for lang_code, checkbox in self.lang_checkboxes.items():
                    checkbox.setChecked(lang_code in allowed_langs)
            
            # 设置最小框尺寸
            if "min_box_width" in params:
                self.min_box_width_spin.setValue(params["min_box_width"])
            
            if "min_box_height" in params:
                self.min_box_height_spin.setValue(params["min_box_height"])
            
            # 设置启用框过滤
            if "enable_box_filter" in params:
                self.enable_filter_checkbox.setChecked(params["enable_box_filter"])
                
        finally:
            self.blockSignals(False)

    def load_parameters(self):
        """从配置加载参数"""
        # 设置默认模型路径
        if self.config.model_path.exists():
            self.model_path_edit.setText(str(self.config.model_path))
        
        # 设置检测参数
        params = self.config.detector_params
        self.set_parameters(params)
        
        print(f"已从配置加载参数: {params}")
    
    def reset_parameters(self):
        """重置为默认参数"""
        default_params = {
            "input_size": 1280,
            "conf_thresh": 0.4,
            "mask_thresh": 0.3,
            "containment_thresh": 0.8,
            "min_box_width": 10,
            "min_box_height": 10,
            "enable_box_filter": True,
            "allowed_languages": ["zh", "ja"],
            "device": "auto"
        }
        self.set_parameters(default_params)
        self.parameters_changed.emit()
    
    def update_default_config(self):
        """更新默认配置"""
        try:
            # 获取当前参数
            current_params = self.get_parameters()
            model_path = self.get_model_path()
            
            # 更新配置对象
            if model_path:
                try:
                    relative_path = str(Path(model_path).relative_to(self.config.project_root))
                    self.config.set('paths.default_model', relative_path)
                except ValueError:
                    # 如果无法获取相对路径，保存绝对路径
                    self.config.set('paths.default_model', model_path)
            
            for key, value in current_params.items():
                if key != 'device':  # device 不保存到默认配置
                    self.config.set(f'detector.{key}', value)
            
            # 保存为默认配置
            if self.config.save_as_default():
                QMessageBox.information(
                    self, 
                    "成功", 
                    "默认配置已更新！\n下次启动应用时将使用当前参数作为默认值。"
                )
            else:
                QMessageBox.warning(self, "警告", "默认配置更新失败！")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新默认配置时发生错误：{e}")

    def create_ocr_group(self) -> QGroupBox:
        """创建OCR结果显示组"""
        group = QGroupBox("OCR结果")
        self.ocr_layout = QVBoxLayout(group)
        
        # 滚动区域用于显示多个OCR结果
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)  # 从200改为300
        scroll_area.setMaximumHeight(400)  # 从300改为400
        
        # 创建OCR结果容器
        self.ocr_container = QWidget()
        self.ocr_container_layout = QVBoxLayout(self.ocr_container)
        self.ocr_container_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll_area.setWidget(self.ocr_container)
        self.ocr_layout.addWidget(scroll_area)
        
        # 提示标签
        self.ocr_hint_label = QLabel("请先完成检测和OCR识别")
        self.ocr_hint_label.setAlignment(Qt.AlignCenter)
        self.ocr_hint_label.setStyleSheet("color: #888888; font-style: italic;")
        self.ocr_container_layout.addWidget(self.ocr_hint_label)
        
        return group

    def update_ocr_results(self, detection_results):
        """更新OCR结果显示"""
        from core.detector import DetectionResults
        
        self.current_detection_results = detection_results
        
        # 清空现有的OCR控件
        self.clear_ocr_results()
        
        if not isinstance(detection_results, DetectionResults) or not detection_results.has_ocr_results:
            self.ocr_hint_label.setText("暂无OCR结果")
            self.ocr_hint_label.setVisible(True)
            return
        
        self.ocr_hint_label.setVisible(False)
        
        # 根据text_regions创建OCR结果编辑控件
        for i, region in enumerate(detection_results.text_regions):
            ocr_text = region.get('ocr_text', '')
            
            # 创建每个OCR结果的控件组
            result_widget = QWidget()
            result_layout = QVBoxLayout(result_widget)
            result_layout.setContentsMargins(5, 5, 5, 5)
            
            # 次序标签（从1开始，不显示置信度）
            sequence_label = QLabel(f"{i+1}")  # 从区域0改为1，区域1改为2
            sequence_label.setFont(QFont("Arial", 10, QFont.Bold))
            sequence_label.setStyleSheet("color: #333333; padding: 2px 0px;")
            result_layout.addWidget(sequence_label)
            
            # 文本编辑框
            text_edit = QTextEdit()
            text_edit.setPlainText(ocr_text)
            text_edit.setMaximumHeight(80)
            text_edit.setMinimumHeight(50)
            
            # 连接文本变化信号到自动保存
            text_edit.textChanged.connect(
                lambda region_idx=i: self.on_ocr_text_changed(region_idx)
            )
            
            result_layout.addWidget(text_edit)
            
            # 分隔线
            if i < len(detection_results.text_regions) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                line.setStyleSheet("color: #cccccc;")
                result_layout.addWidget(line)
            
            # 保存控件引用
            self.ocr_results_widgets[i] = text_edit
            
            # 添加到容器
            self.ocr_container_layout.addWidget(result_widget)

    def on_ocr_text_changed(self, region_idx: int):
        """OCR文本变化时的回调"""
        if (self.current_detection_results and 
            region_idx < len(self.current_detection_results.text_regions)):
            
            # 获取修改后的文本
            if region_idx in self.ocr_results_widgets:
                new_text = self.ocr_results_widgets[region_idx].toPlainText()
                
                # 更新检测结果中的OCR文本
                self.current_detection_results.text_regions[region_idx]['ocr_text'] = new_text
                
                # 更新OCR结果字典
                region_key = f"region_{region_idx}"
                self.current_detection_results.ocr_results[region_key] = new_text
                
                # 发射信号通知主窗口保存更改
                self.ocr_text_modified.emit(region_idx, new_text)

    def clear_ocr_results(self):
        """清空OCR结果显示"""
        # 清空控件引用
        self.ocr_results_widgets.clear()
        
        # 清空布局中的所有控件
        while self.ocr_container_layout.count():
            child = self.ocr_container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 重新添加提示标签
        self.ocr_hint_label = QLabel("请先完成检测和OCR识别")
        self.ocr_hint_label.setAlignment(Qt.AlignCenter)
        self.ocr_hint_label.setStyleSheet("color: #888888; font-style: italic;")
        self.ocr_container_layout.addWidget(self.ocr_hint_label)
     
    def validate_parameters(self) -> tuple[bool, str]:
        """验证参数有效性"""
        # 检查模型文件
        model_path = self.get_model_path()
        if not model_path:
            return False, "请选择模型文件"
        
        if not Path(model_path).exists():
            return False, f"模型文件不存在: {model_path}"
        
        # 检查语言选择
        params = self.get_parameters()
        if not params["allowed_languages"]:
            return False, "请至少选择一种支持的语言"
        
        return True, ""
    
    def get_parameter_summary(self) -> str:
        """获取参数摘要"""
        params = self.get_parameters()
        model_name = Path(self.get_model_path()).name if self.get_model_path() else "未选择"
        
        summary = f"""参数摘要:
模型: {model_name}
设备: {params['device']}
输入尺寸: {params['input_size']}
置信度阈值: {params['conf_thresh']:.2f}
掩码阈值: {params['mask_thresh']:.2f}
支持语言: {', '.join(params['allowed_languages'])}
框过滤: {'启用' if params['enable_box_filter'] else '禁用'}"""
        
        return summary


if __name__ == "__main__":
    # 测试参数面板
    import sys
    
    app = QApplication(sys.argv)
    
    config = Config()
    panel = ParameterPanel(config)
    
    # 创建测试窗口
    window = QWidget()
    layout = QHBoxLayout(window)
    layout.addWidget(panel)
    
    window.show()
    
    sys.exit(app.exec_())
```

### `__init__.py`

```py

```

## `workers.py`

```py
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
```

## `__init__.py`

```py

```

# `utils`

## `db_utils.py`

```py
import cv2
import numpy as np
import pyclipper
from shapely.geometry import Polygon
from collections import namedtuple
import torch
import warnings
warnings.filterwarnings('ignore')


def iou_rotate(box_a, box_b, method='union'):
    rect_a = cv2.minAreaRect(box_a)
    rect_b = cv2.minAreaRect(box_b)
    r1 = cv2.rotatedRectangleIntersection(rect_a, rect_b)
    if r1[0] == 0:
        return 0
    else:
        inter_area = cv2.contourArea(r1[1])
        area_a = cv2.contourArea(box_a)
        area_b = cv2.contourArea(box_b)
        union_area = area_a + area_b - inter_area
        if union_area == 0 or inter_area == 0:
            return 0
        if method == 'union':
            iou = inter_area / union_area
        elif method == 'intersection':
            iou = inter_area / min(area_a, area_b)
        else:
            raise NotImplementedError
        return iou

class SegDetectorRepresenter():
    def __init__(self, thresh=0.3, box_thresh=0.7, max_candidates=1000, unclip_ratio=1.5):
        self.min_size = 3
        self.thresh = thresh
        self.box_thresh = box_thresh
        self.max_candidates = max_candidates
        self.unclip_ratio = unclip_ratio

    def __call__(self, batch, pred, is_output_polygon=False):
        '''
        batch: (image, polygons, ignore_tags
        batch: a dict produced by dataloaders.
            image: tensor of shape (N, C, H, W).
            polygons: tensor of shape (N, K, 4, 2), the polygons of objective regions.
            ignore_tags: tensor of shape (N, K), indicates whether a region is ignorable or not.
            shape: the original shape of images.
            filename: the original filenames of images.
        pred:
            binary: text region segmentation map, with shape (N, H, W)
            thresh: [if exists] thresh hold prediction with shape (N, H, W)
            thresh_binary: [if exists] binarized with threshold, (N, H, W)
        '''
        pred = pred[:, 0, :, :]
        segmentation = self.binarize(pred)
        boxes_batch = []
        scores_batch = []
        # print(pred.size())
        batch_size = pred.size(0) if isinstance(pred, torch.Tensor) else pred.shape[0]
        for batch_index in range(batch_size):
            # height, width = batch['shape'][batch_index]
            height, width = pred.shape[1], pred.shape[2]
            if is_output_polygon:
                boxes, scores = self.polygons_from_bitmap(pred[batch_index], segmentation[batch_index], width, height)
            else:
                boxes, scores = self.boxes_from_bitmap(pred[batch_index], segmentation[batch_index], width, height)
            boxes_batch.append(boxes)
            scores_batch.append(scores)
        return boxes_batch, scores_batch

    def binarize(self, pred):
        return pred > self.thresh

    def polygons_from_bitmap(self, pred, _bitmap, dest_width, dest_height):
        '''
        _bitmap: single map with shape (H, W),
            whose values are binarized as {0, 1}
        '''

        assert len(_bitmap.shape) == 2
        bitmap = _bitmap.cpu().numpy()  # The first channel
        pred = pred.cpu().detach().numpy()
        height, width = bitmap.shape
        boxes = []
        scores = []

        contours, _ = cv2.findContours((bitmap * 255).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours[:self.max_candidates]:
            epsilon = 0.005 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            points = approx.reshape((-1, 2))
            if points.shape[0] < 4:
                continue
            # _, sside = self.get_mini_boxes(contour)
            # if sside < self.min_size:
            #     continue
            score = self.box_score_fast(pred, contour.squeeze(1))
            if self.box_thresh > score:
                continue

            if points.shape[0] > 2:
                box = self.unclip(points, unclip_ratio=self.unclip_ratio)
                if len(box) > 1:
                    continue
            else:
                continue
            box = box.reshape(-1, 2)
            _, sside = self.get_mini_boxes(box.reshape((-1, 1, 2)))
            if sside < self.min_size + 2:
                continue

            if not isinstance(dest_width, int):
                dest_width = dest_width.item()
                dest_height = dest_height.item()

            box[:, 0] = np.clip(np.round(box[:, 0] / width * dest_width), 0, dest_width)
            box[:, 1] = np.clip(np.round(box[:, 1] / height * dest_height), 0, dest_height)
            boxes.append(box)
            scores.append(score)
        return boxes, scores

    def boxes_from_bitmap(self, pred, _bitmap, dest_width, dest_height):
        '''
        _bitmap: single map with shape (H, W),
            whose values are binarized as {0, 1}
        '''

        assert len(_bitmap.shape) == 2
        if isinstance(pred, torch.Tensor):
            bitmap = _bitmap.cpu().numpy()  # The first channel
            pred = pred.cpu().detach().numpy()
        else:
            bitmap = _bitmap
        height, width = bitmap.shape
        contours, _ = cv2.findContours((bitmap * 255).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        num_contours = min(len(contours), self.max_candidates)
        boxes = np.zeros((num_contours, 4, 2), dtype=np.int16)
        scores = np.zeros((num_contours,), dtype=np.float32)

        for index in range(num_contours):
            contour = contours[index].squeeze(1)
            points, sside = self.get_mini_boxes(contour)
            # if sside < self.min_size:
            #     continue
            if sside < 2:
                continue
            points = np.array(points)
            score = self.box_score_fast(pred, contour)
            # if self.box_thresh > score:
            #     continue

            box = self.unclip(points, unclip_ratio=self.unclip_ratio).reshape(-1, 1, 2)
            box, sside = self.get_mini_boxes(box)
            # if sside < 5:
            #     continue
            box = np.array(box)
            if not isinstance(dest_width, int):
                dest_width = dest_width.item()
                dest_height = dest_height.item()

            box[:, 0] = np.clip(np.round(box[:, 0] / width * dest_width), 0, dest_width)
            box[:, 1] = np.clip(np.round(box[:, 1] / height * dest_height), 0, dest_height)
            boxes[index, :, :] = box.astype(np.int16)
            scores[index] = score
        return boxes, scores

    def unclip(self, box, unclip_ratio=1.5):
        poly = Polygon(box)
        distance = poly.area * unclip_ratio / poly.length
        offset = pyclipper.PyclipperOffset()
        offset.AddPath(box, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
        expanded = np.array(offset.Execute(distance))
        return expanded

    def get_mini_boxes(self, contour):
        bounding_box = cv2.minAreaRect(contour)
        points = sorted(list(cv2.boxPoints(bounding_box)), key=lambda x: x[0])

        index_1, index_2, index_3, index_4 = 0, 1, 2, 3
        if points[1][1] > points[0][1]:
            index_1 = 0
            index_4 = 1
        else:
            index_1 = 1
            index_4 = 0
        if points[3][1] > points[2][1]:
            index_2 = 2
            index_3 = 3
        else:
            index_2 = 3
            index_3 = 2

        box = [points[index_1], points[index_2], points[index_3], points[index_4]]
        return box, min(bounding_box[1])

    def box_score_fast(self, bitmap, _box):
        h, w = bitmap.shape[:2]
        box = _box.copy()
        xmin = np.clip(np.floor(box[:, 0].min()).astype(np.int64), 0, w - 1)
        xmax = np.clip(np.ceil(box[:, 0].max()).astype(np.int64), 0, w - 1)
        ymin = np.clip(np.floor(box[:, 1].min()).astype(np.int64), 0, h - 1)
        ymax = np.clip(np.ceil(box[:, 1].max()).astype(np.int64), 0, h - 1)

        mask = np.zeros((ymax - ymin + 1, xmax - xmin + 1), dtype=np.uint8)
        box[:, 0] = box[:, 0] - xmin
        box[:, 1] = box[:, 1] - ymin
        cv2.fillPoly(mask, box.reshape(1, -1, 2).astype(np.int32), 1)
        if bitmap.dtype == np.float16:
            bitmap = bitmap.astype(np.float32)
        return cv2.mean(bitmap[ymin:ymax + 1, xmin:xmax + 1], mask)[0]

class AverageMeter(object):
    """Computes and stores the average and current value"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count
        return self


class DetectionIoUEvaluator(object):
    def __init__(self, is_output_polygon=False, iou_constraint=0.5, area_precision_constraint=0.5):
        self.is_output_polygon = is_output_polygon
        self.iou_constraint = iou_constraint
        self.area_precision_constraint = area_precision_constraint

    def evaluate_image(self, gt, pred):

        def get_union(pD, pG):
            return Polygon(pD).union(Polygon(pG)).area

        def get_intersection_over_union(pD, pG):
            return get_intersection(pD, pG) / get_union(pD, pG)

        def get_intersection(pD, pG):
            return Polygon(pD).intersection(Polygon(pG)).area

        def compute_ap(confList, matchList, numGtCare):
            correct = 0
            AP = 0
            if len(confList) > 0:
                confList = np.array(confList)
                matchList = np.array(matchList)
                sorted_ind = np.argsort(-confList)
                confList = confList[sorted_ind]
                matchList = matchList[sorted_ind]
                for n in range(len(confList)):
                    match = matchList[n]
                    if match:
                        correct += 1
                        AP += float(correct) / (n + 1)

                if numGtCare > 0:
                    AP /= numGtCare

            return AP

        perSampleMetrics = {}

        matchedSum = 0

        Rectangle = namedtuple('Rectangle', 'xmin ymin xmax ymax')

        numGlobalCareGt = 0
        numGlobalCareDet = 0

        arrGlobalConfidences = []
        arrGlobalMatches = []

        recall = 0
        precision = 0
        hmean = 0

        detMatched = 0

        iouMat = np.empty([1, 1])

        gtPols = []
        detPols = []

        gtPolPoints = []
        detPolPoints = []

        # Array of Ground Truth Polygons' keys marked as don't Care
        gtDontCarePolsNum = []
        # Array of Detected Polygons' matched with a don't Care GT
        detDontCarePolsNum = []

        pairs = []
        detMatchedNums = []

        arrSampleConfidences = []
        arrSampleMatch = []

        evaluationLog = ""

        for n in range(len(gt)):
            points = gt[n]['points']
            # transcription = gt[n]['text']
            dontCare = gt[n]['ignore']

            if not Polygon(points).is_valid or not Polygon(points).is_simple:
                continue

            gtPol = points
            gtPols.append(gtPol)
            gtPolPoints.append(points)
            if dontCare:
                gtDontCarePolsNum.append(len(gtPols) - 1)

        evaluationLog += "GT polygons: " + str(len(gtPols)) + (" (" + str(len(
            gtDontCarePolsNum)) + " don't care)\n" if len(gtDontCarePolsNum) > 0 else "\n")

        for n in range(len(pred)):
            points = pred[n]['points']
            if not Polygon(points).is_valid or not Polygon(points).is_simple:
                continue

            detPol = points
            detPols.append(detPol)
            detPolPoints.append(points)
            if len(gtDontCarePolsNum) > 0:
                for dontCarePol in gtDontCarePolsNum:
                    dontCarePol = gtPols[dontCarePol]
                    intersected_area = get_intersection(dontCarePol, detPol)
                    pdDimensions = Polygon(detPol).area
                    precision = 0 if pdDimensions == 0 else intersected_area / pdDimensions
                    if (precision > self.area_precision_constraint):
                        detDontCarePolsNum.append(len(detPols) - 1)
                        break

        evaluationLog += "DET polygons: " + str(len(detPols)) + (" (" + str(len(
            detDontCarePolsNum)) + " don't care)\n" if len(detDontCarePolsNum) > 0 else "\n")

        if len(gtPols) > 0 and len(detPols) > 0:
            # Calculate IoU and precision matrixs
            outputShape = [len(gtPols), len(detPols)]
            iouMat = np.empty(outputShape)
            gtRectMat = np.zeros(len(gtPols), np.int8)
            detRectMat = np.zeros(len(detPols), np.int8)
            if self.is_output_polygon:
                for gtNum in range(len(gtPols)):
                    for detNum in range(len(detPols)):
                        pG = gtPols[gtNum]
                        pD = detPols[detNum]
                        iouMat[gtNum, detNum] = get_intersection_over_union(pD, pG)
            else:
                # gtPols = np.float32(gtPols)
                # detPols = np.float32(detPols)
                for gtNum in range(len(gtPols)):
                    for detNum in range(len(detPols)):
                        pG = np.float32(gtPols[gtNum])
                        pD = np.float32(detPols[detNum])
                        iouMat[gtNum, detNum] = iou_rotate(pD, pG)
            for gtNum in range(len(gtPols)):
                for detNum in range(len(detPols)):
                    if gtRectMat[gtNum] == 0 and detRectMat[
                        detNum] == 0 and gtNum not in gtDontCarePolsNum and detNum not in detDontCarePolsNum:
                        if iouMat[gtNum, detNum] > self.iou_constraint:
                            gtRectMat[gtNum] = 1
                            detRectMat[detNum] = 1
                            detMatched += 1
                            pairs.append({'gt': gtNum, 'det': detNum})
                            detMatchedNums.append(detNum)
                            evaluationLog += "Match GT #" + \
                                             str(gtNum) + " with Det #" + str(detNum) + "\n"

        numGtCare = (len(gtPols) - len(gtDontCarePolsNum))
        numDetCare = (len(detPols) - len(detDontCarePolsNum))
        if numGtCare == 0:
            recall = float(1)
            precision = float(0) if numDetCare > 0 else float(1)
        else:
            recall = float(detMatched) / numGtCare
            precision = 0 if numDetCare == 0 else float(
                detMatched) / numDetCare

        hmean = 0 if (precision + recall) == 0 else 2.0 * \
                                                    precision * recall / (precision + recall)

        matchedSum += detMatched
        numGlobalCareGt += numGtCare
        numGlobalCareDet += numDetCare

        perSampleMetrics = {
            'precision': precision,
            'recall': recall,
            'hmean': hmean,
            'pairs': pairs,
            'iouMat': [] if len(detPols) > 100 else iouMat.tolist(),
            'gtPolPoints': gtPolPoints,
            'detPolPoints': detPolPoints,
            'gtCare': numGtCare,
            'detCare': numDetCare,
            'gtDontCare': gtDontCarePolsNum,
            'detDontCare': detDontCarePolsNum,
            'detMatched': detMatched,
            'evaluationLog': evaluationLog
        }

        return perSampleMetrics

    def combine_results(self, results):
        numGlobalCareGt = 0
        numGlobalCareDet = 0
        matchedSum = 0
        for result in results:
            numGlobalCareGt += result['gtCare']
            numGlobalCareDet += result['detCare']
            matchedSum += result['detMatched']

        methodRecall = 0 if numGlobalCareGt == 0 else float(
            matchedSum) / numGlobalCareGt
        methodPrecision = 0 if numGlobalCareDet == 0 else float(
            matchedSum) / numGlobalCareDet
        methodHmean = 0 if methodRecall + methodPrecision == 0 else 2 * \
                                                                    methodRecall * methodPrecision / (
                                                                            methodRecall + methodPrecision)

        methodMetrics = {'precision': methodPrecision,
                         'recall': methodRecall, 'hmean': methodHmean}

        return methodMetrics

class QuadMetric():
    def __init__(self, is_output_polygon=False):
        self.is_output_polygon = is_output_polygon
        self.evaluator = DetectionIoUEvaluator(is_output_polygon=is_output_polygon)

    def measure(self, batch, output, box_thresh=0.6):
        '''
        batch: (image, polygons, ignore_tags
        batch: a dict produced by dataloaders.
            image: tensor of shape (N, C, H, W).
            polygons: tensor of shape (N, K, 4, 2), the polygons of objective regions.
            ignore_tags: tensor of shape (N, K), indicates whether a region is ignorable or not.
            shape: the original shape of images.
            filename: the original filenames of images.
        output: (polygons, ...)
        '''
        results = []
        gt_polyons_batch = batch['text_polys']
        ignore_tags_batch = batch['ignore_tags']
        pred_polygons_batch = np.array(output[0])
        pred_scores_batch = np.array(output[1])
        for polygons, pred_polygons, pred_scores, ignore_tags in zip(gt_polyons_batch, pred_polygons_batch, pred_scores_batch, ignore_tags_batch):
            gt = [dict(points=np.int64(polygons[i]), ignore=ignore_tags[i]) for i in range(len(polygons))]
            if self.is_output_polygon:
                pred = [dict(points=pred_polygons[i]) for i in range(len(pred_polygons))]
            else:
                pred = []
                # print(pred_polygons.shape)
                for i in range(pred_polygons.shape[0]):
                    if pred_scores[i] >= box_thresh:
                        # print(pred_polygons[i,:,:].tolist())
                        pred.append(dict(points=pred_polygons[i, :, :].astype(np.int64)))
                # pred = [dict(points=pred_polygons[i,:,:].tolist()) if pred_scores[i] >= box_thresh for i in range(pred_polygons.shape[0])]
            results.append(self.evaluator.evaluate_image(gt, pred))
        return results

    def validate_measure(self, batch, output, box_thresh=0.6):
        return self.measure(batch, output, box_thresh)

    def evaluate_measure(self, batch, output):
        return self.measure(batch, output), np.linspace(0, batch['image'].shape[0]).tolist()

    def gather_measure(self, raw_metrics):
        raw_metrics = [image_metrics
                       for batch_metrics in raw_metrics
                       for image_metrics in batch_metrics]

        result = self.evaluator.combine_results(raw_metrics)

        precision = AverageMeter()
        recall = AverageMeter()
        fmeasure = AverageMeter()

        precision.update(result['precision'], n=len(raw_metrics))
        recall.update(result['recall'], n=len(raw_metrics))
        fmeasure_score = 2 * precision.val * recall.val / (precision.val + recall.val + 1e-8)
        fmeasure.update(fmeasure_score)

        return {
            'precision': precision,
            'recall': recall,
            'fmeasure': fmeasure
        }

def shrink_polygon_py(polygon, shrink_ratio):
    """
    对框进行缩放，返回去的比例为1/shrink_ratio 即可
    """
    cx = polygon[:, 0].mean()
    cy = polygon[:, 1].mean()
    polygon[:, 0] = cx + (polygon[:, 0] - cx) * shrink_ratio
    polygon[:, 1] = cy + (polygon[:, 1] - cy) * shrink_ratio
    return polygon


def shrink_polygon_pyclipper(polygon, shrink_ratio):
    from shapely.geometry import Polygon
    import pyclipper
    polygon_shape = Polygon(polygon)
    distance = polygon_shape.area * (1 - np.power(shrink_ratio, 2)) / polygon_shape.length
    subject = [tuple(l) for l in polygon]
    padding = pyclipper.PyclipperOffset()
    padding.AddPath(subject, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
    shrunk = padding.Execute(-distance)
    if shrunk == []:
        shrunk = np.array(shrunk)
    else:
        shrunk = np.array(shrunk[0]).reshape(-1, 2)
    return shrunk

class MakeShrinkMap():
    r'''
    Making binary mask from detection data with ICDAR format.
    Typically following the process of class `MakeICDARData`.
    '''

    def __init__(self, min_text_size=4, shrink_ratio=0.4, shrink_type='pyclipper'):
        shrink_func_dict = {'py': shrink_polygon_py, 'pyclipper': shrink_polygon_pyclipper}
        self.shrink_func = shrink_func_dict[shrink_type]
        self.min_text_size = min_text_size
        self.shrink_ratio = shrink_ratio

    def __call__(self, data: dict) -> dict:
        """
        从scales中随机选择一个尺度，对图片和文本框进行缩放
        :param data: {'imgs':,'text_polys':,'texts':,'ignore_tags':}
        :return:
        """
        image = data['imgs']
        text_polys = data['text_polys']
        ignore_tags = data['ignore_tags']

        h, w = image.shape[:2]
        text_polys, ignore_tags = self.validate_polygons(text_polys, ignore_tags, h, w)
        gt = np.zeros((h, w), dtype=np.float32)
        mask = np.ones((h, w), dtype=np.float32)
        for i in range(len(text_polys)):
            polygon = text_polys[i]
            height = max(polygon[:, 1]) - min(polygon[:, 1])
            width = max(polygon[:, 0]) - min(polygon[:, 0])
            if ignore_tags[i] or min(height, width) < self.min_text_size:
                cv2.fillPoly(mask, polygon.astype(np.int32)[np.newaxis, :, :], 0)
                ignore_tags[i] = True
            else:
                shrunk = self.shrink_func(polygon, self.shrink_ratio)
                if shrunk.size == 0:
                    cv2.fillPoly(mask, polygon.astype(np.int32)[np.newaxis, :, :], 0)
                    ignore_tags[i] = True
                    continue
                cv2.fillPoly(gt, [shrunk.astype(np.int32)], 1)

        data['shrink_map'] = gt
        data['shrink_mask'] = mask
        return data

    def validate_polygons(self, polygons, ignore_tags, h, w):
        '''
        polygons (numpy.array, required): of shape (num_instances, num_points, 2)
        '''
        if len(polygons) == 0:
            return polygons, ignore_tags
        assert len(polygons) == len(ignore_tags)
        for polygon in polygons:
            polygon[:, 0] = np.clip(polygon[:, 0], 0, w - 1)
            polygon[:, 1] = np.clip(polygon[:, 1], 0, h - 1)

        for i in range(len(polygons)):
            area = self.polygon_area(polygons[i])
            if abs(area) < 1:
                ignore_tags[i] = True
            if area > 0:
                polygons[i] = polygons[i][::-1, :]
        return polygons, ignore_tags

    def polygon_area(self, polygon):
        return cv2.contourArea(polygon)


class MakeBorderMap():
    def __init__(self, shrink_ratio=0.4, thresh_min=0.3, thresh_max=0.7):
        self.shrink_ratio = shrink_ratio
        self.thresh_min = thresh_min
        self.thresh_max = thresh_max

    def __call__(self, data: dict) -> dict:
        """
        从scales中随机选择一个尺度，对图片和文本框进行缩放
        :param data: {'imgs':,'text_polys':,'texts':,'ignore_tags':}
        :return:
        """
        im = data['imgs']
        text_polys = data['text_polys']
        ignore_tags = data['ignore_tags']

        canvas = np.zeros(im.shape[:2], dtype=np.float32)
        mask = np.zeros(im.shape[:2], dtype=np.float32)

        for i in range(len(text_polys)):
            if ignore_tags[i]:
                continue
            self.draw_border_map(text_polys[i], canvas, mask=mask)
        canvas = canvas * (self.thresh_max - self.thresh_min) + self.thresh_min

        data['threshold_map'] = canvas
        data['threshold_mask'] = mask
        return data

    def draw_border_map(self, polygon, canvas, mask):
        polygon = np.array(polygon)
        assert polygon.ndim == 2
        assert polygon.shape[1] == 2

        polygon_shape = Polygon(polygon)
        if polygon_shape.area <= 0:
            return
        distance = polygon_shape.area * (1 - np.power(self.shrink_ratio, 2)) / polygon_shape.length
        subject = [tuple(l) for l in polygon]
        padding = pyclipper.PyclipperOffset()
        padding.AddPath(subject, pyclipper.JT_ROUND,
                        pyclipper.ET_CLOSEDPOLYGON)

        padded_polygon = np.array(padding.Execute(distance)[0])
        cv2.fillPoly(mask, [padded_polygon.astype(np.int32)], 1.0)

        xmin = padded_polygon[:, 0].min()
        xmax = padded_polygon[:, 0].max()
        ymin = padded_polygon[:, 1].min()
        ymax = padded_polygon[:, 1].max()
        width = xmax - xmin + 1
        height = ymax - ymin + 1

        polygon[:, 0] = polygon[:, 0] - xmin
        polygon[:, 1] = polygon[:, 1] - ymin

        xs = np.broadcast_to(
            np.linspace(0, width - 1, num=width).reshape(1, width), (height, width))
        ys = np.broadcast_to(
            np.linspace(0, height - 1, num=height).reshape(height, 1), (height, width))

        distance_map = np.zeros(
            (polygon.shape[0], height, width), dtype=np.float32)
        for i in range(polygon.shape[0]):
            j = (i + 1) % polygon.shape[0]
            absolute_distance = self.distance(xs, ys, polygon[i], polygon[j])
            distance_map[i] = np.clip(absolute_distance / distance, 0, 1)
        distance_map = distance_map.min(axis=0)

        xmin_valid = min(max(0, xmin), canvas.shape[1] - 1)
        xmax_valid = min(max(0, xmax), canvas.shape[1] - 1)
        ymin_valid = min(max(0, ymin), canvas.shape[0] - 1)
        ymax_valid = min(max(0, ymax), canvas.shape[0] - 1)
        canvas[ymin_valid:ymax_valid + 1, xmin_valid:xmax_valid + 1] = np.fmax(
            1 - distance_map[
                ymin_valid - ymin:ymax_valid - ymax + height,
                xmin_valid - xmin:xmax_valid - xmax + width],
            canvas[ymin_valid:ymax_valid + 1, xmin_valid:xmax_valid + 1])

    def distance(self, xs, ys, point_1, point_2):
        '''
        compute the distance from point to a line
        ys: coordinates in the first axis
        xs: coordinates in the second axis
        point_1, point_2: (x, y), the end of the line
        '''
        height, width = xs.shape[:2]
        square_distance_1 = np.square(xs - point_1[0]) + np.square(ys - point_1[1])
        square_distance_2 = np.square(xs - point_2[0]) + np.square(ys - point_2[1])
        square_distance = np.square(point_1[0] - point_2[0]) + np.square(point_1[1] - point_2[1])

        cosin = (square_distance - square_distance_1 - square_distance_2) / (2 * np.sqrt(square_distance_1 * square_distance_2))
        square_sin = 1 - np.square(cosin)
        square_sin = np.nan_to_num(square_sin)

        result = np.sqrt(square_distance_1 * square_distance_2 * square_sin / square_distance)
        result[cosin < 0] = np.sqrt(np.fmin(square_distance_1, square_distance_2))[cosin < 0]
        return result

    def extend_line(self, point_1, point_2, result):
        ex_point_1 = (int(round(point_1[0] + (point_1[0] - point_2[0]) * (1 + self.shrink_ratio))),
                      int(round(point_1[1] + (point_1[1] - point_2[1]) * (1 + self.shrink_ratio))))
        cv2.line(result, tuple(ex_point_1), tuple(point_1), 4096.0, 1, lineType=cv2.LINE_AA, shift=0)
        ex_point_2 = (int(round(point_2[0] + (point_2[0] - point_1[0]) * (1 + self.shrink_ratio))),
                      int(round(point_2[1] + (point_2[1] - point_1[1]) * (1 + self.shrink_ratio))))
        cv2.line(result, tuple(ex_point_2), tuple(point_2), 4096.0, 1, lineType=cv2.LINE_AA, shift=0)
        return ex_point_1, ex_point_2
```

## `detection_utils.py`

```py
"""
检测相关的辅助函数
"""

import numpy as np
from typing import List, Dict, Any

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
```

## `general.py`

```py
# utils/general.py - 简化版
import os
import logging
import torch

def set_logging(name=None, verbose=True):
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(format="%(message)s", level=logging.INFO if verbose else logging.WARNING)
    return logging.getLogger(name)

LOGGER = set_logging(__name__)

CUDA = True if torch.cuda.is_available() else False
DEVICE = 'cuda' if CUDA else 'cpu'

# 删除 Loggers 类和其他训练相关功能
```

## `imgproc_utils.py`

```py
import numpy as np
import cv2
import random

def hex2bgr(hex):
    gmask = 254 << 8
    rmask = 254
    b = hex >> 16
    g = (hex & gmask) >> 8
    r = hex & rmask
    return np.stack([b, g, r]).transpose()

def union_area(bboxa, bboxb):
    x1 = max(bboxa[0], bboxb[0])
    y1 = max(bboxa[1], bboxb[1])
    x2 = min(bboxa[2], bboxb[2])
    y2 = min(bboxa[3], bboxb[3])
    if y2 < y1 or x2 < x1:
        return -1
    return (y2 - y1) * (x2 - x1)

def get_yololabel_strings(clslist, labellist):
    content = ''
    for cls, xywh in zip(clslist, labellist):
        content += str(int(cls)) + ' ' + ' '.join([str(e) for e in xywh]) + '\n'
    if len(content) != 0:
        content = content[:-1]
    return content

# 4 points bbox to 8 points polygon
def xywh2xyxypoly(xywh, to_int=True):
    xyxypoly = np.tile(xywh[:, [0, 1]], 4)
    xyxypoly[:, [2, 4]] += xywh[:, [2]]
    xyxypoly[:, [5, 7]] += xywh[:, [3]]
    if to_int:
        xyxypoly = xyxypoly.astype(np.int64)
    return xyxypoly

def xyxy2yolo(xyxy, w: int, h: int):
    if xyxy == [] or len(xyxy) == 0:
        return None
    if isinstance(xyxy, list):
        xyxy = np.array(xyxy)
    if len(xyxy.shape) == 1:
        xyxy = np.array([xyxy])
    yolo = np.copy(xyxy).astype(np.float64)
    yolo[:, [0, 2]] =  yolo[:, [0, 2]] / w
    yolo[:, [1, 3]] = yolo[:, [1, 3]] / h
    yolo[:, [2, 3]] -= yolo[:, [0, 1]]
    yolo[:, [0, 1]] += yolo[:, [2, 3]] / 2
    return yolo

def yolo_xywh2xyxy(xywh: np.array, w: int, h:  int, to_int=True):
    if xywh is None:
        return None
    if len(xywh) == 0:
        return None
    if len(xywh.shape) == 1:
        xywh = np.array([xywh])
    xywh[:, [0, 2]] *= w
    xywh[:, [1, 3]] *= h
    xywh[:, [0, 1]] -= xywh[:, [2, 3]] / 2
    xywh[:, [2, 3]] += xywh[:, [0, 1]]
    if to_int:
        xywh = xywh.astype(np.int64)
    return xywh

def rotate_polygons(center, polygons, rotation, new_center=None, to_int=True):
    if new_center is None:
        new_center = center
    rotation = np.deg2rad(rotation)
    s, c = np.sin(rotation), np.cos(rotation)
    polygons = polygons.astype(np.float32)
    
    polygons[:, 1::2] -= center[1]
    polygons[:, ::2] -= center[0]
    rotated = np.copy(polygons)
    rotated[:, 1::2] = polygons[:, 1::2] * c - polygons[:, ::2] * s
    rotated[:, ::2] = polygons[:, 1::2] * s + polygons[:, ::2] * c
    rotated[:, 1::2] += new_center[1]
    rotated[:, ::2] += new_center[0]
    if to_int:
        return rotated.astype(np.int64)
    return rotated

def letterbox(im, new_shape=(640, 640), color=(0, 0, 0), auto=False, scaleFill=False, scaleup=True, stride=128):
    # Resize and pad image while meeting stride-multiple constraints
    shape = im.shape[:2]  # current shape [height, width]
    if not isinstance(new_shape, tuple):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:  # only scale down, do not scale up (for better val mAP)
        r = min(r, 1.0)

    # Compute padding
    ratio = r, r  # width, height ratios
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding
    if auto:  # minimum rectangle
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding
    elif scaleFill:  # stretch
        dw, dh = 0.0, 0.0
        new_unpad = (new_shape[1], new_shape[0])
        ratio = new_shape[1] / shape[1], new_shape[0] / shape[0]  # width, height ratios

    # dw /= 2  # divide padding into 2 sides
    # dh /= 2
    dh, dw = int(dh), int(dw)

    if shape[::-1] != new_unpad:  # resize
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im, 0, dh, 0, dw, cv2.BORDER_CONSTANT, value=color)  # add border
    return im, ratio, (dw, dh)

def resize_keepasp(im, new_shape=640, scaleup=True, interpolation=cv2.INTER_LINEAR, stride=None):
    shape = im.shape[:2]  # current shape [height, width]

    if new_shape is not None:
        if not isinstance(new_shape, tuple):
            new_shape = (new_shape, new_shape)
    else:
        new_shape = shape

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:  # only scale down, do not scale up (for better val mAP)
        r = min(r, 1.0)

    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))

    if stride is not None:
        h, w = new_unpad
        if new_shape[0] % stride != 0 :
            new_h = (stride - (new_shape[0] % stride)) + h
        else :
            new_h = h
        if w % stride != 0 :
            new_w = (stride - (w % stride)) + w
        else :
            new_w = w
        new_unpad = (new_h, new_w)

    if shape[::-1] != new_unpad:  # resize
        im = cv2.resize(im, new_unpad, interpolation=interpolation)
    return im

def expand_textwindow(img_size, xyxy, expand_r=8, shrink=False):
    im_h, im_w = img_size[:2]
    x1, y1 , x2, y2 = xyxy
    w = x2 - x1
    h = y2 - y1
    paddings = int(round((max(h, w) * 0.25 + min(h, w) * 0.75) / expand_r))
    if shrink:
        paddings *= -1
    x1, y1 = max(0, x1 - paddings), max(0, y1 - paddings)
    x2, y2 = min(im_w-1, x2+paddings), min(im_h-1, y2+paddings)
    return [x1, y1, x2, y2]

def draw_connected_labels(num_labels, labels, stats, centroids, names="draw_connected_labels", skip_background=True):
    labdraw = np.zeros((labels.shape[0], labels.shape[1], 3), dtype=np.uint8)
    max_ind = 0
    if isinstance(num_labels, int):
        num_labels = range(num_labels)
    
    # for ind, lab in enumerate((range(num_labels))):
    for lab in num_labels:
        if skip_background and lab == 0:
            continue
        randcolor = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
        labdraw[np.where(labels==lab)] = randcolor
        maxr, minr = 0.5, 0.001
        maxw, maxh = stats[max_ind][2] * maxr, stats[max_ind][3] * maxr
        minarea = labdraw.shape[0] * labdraw.shape[1] * minr

        stat = stats[lab]
        bboxarea = stat[2] * stat[3]
        if stat[2] < maxw and stat[3] < maxh and bboxarea > minarea:
            pix = np.zeros((labels.shape[0], labels.shape[1]), dtype=np.uint8)
            pix[np.where(labels==lab)] = 255

            rect = cv2.minAreaRect(cv2.findNonZero(pix))
            box = np.int0(cv2.boxPoints(rect))
            labdraw = cv2.drawContours(labdraw, [box], 0, randcolor, 2)
            labdraw = cv2.circle(labdraw, (int(centroids[lab][0]),int(centroids[lab][1])), radius=5, color=(random.randint(0,255), random.randint(0,255), random.randint(0,255)), thickness=-1)                

    cv2.imshow(names, labdraw)
    return labdraw


```

## `io_utils.py`

```py
import os
import os.path as osp
import glob
from pathlib import Path  # 添加这行
import cv2
import numpy as np
import json

IMG_EXT = ['.bmp', '.jpg', '.png', '.jpeg']

NP_BOOL_TYPES = (np.bool_, bool)
NP_FLOAT_TYPES = (np.float_, np.float16, np.float32, np.float64)
NP_INT_TYPES = (np.int_, np.int8, np.int16, np.int32, np.int64, np.uint, np.uint8, np.uint16, np.uint32, np.uint64)

# https://stackoverflow.com/questions/26646362/numpy-array-is-not-json-serializable
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.ScalarType):
            if isinstance(obj, NP_BOOL_TYPES):
                return bool(obj)
            elif isinstance(obj, NP_FLOAT_TYPES):
                return float(obj)
            elif isinstance(obj, NP_INT_TYPES):
                return int(obj)
        return json.JSONEncoder.default(self, obj)

def find_all_imgs(img_dir, abs_path=False):
    imglist = list()
    for filep in glob.glob(osp.join(img_dir, "*")):
        filename = osp.basename(filep)
        file_suffix = Path(filename).suffix
        if file_suffix.lower() not in IMG_EXT:
            continue
        if abs_path:
            imglist.append(filep)
        else:
            imglist.append(filename)
    return imglist

imread = lambda imgpath, read_type=cv2.IMREAD_COLOR: cv2.imdecode(np.fromfile(imgpath, dtype=np.uint8), read_type)
# def imread(imgpath, read_type=cv2.IMREAD_COLOR):
#     img = cv2.imdecode(np.fromfile(imgpath, dtype=np.uint8), read_type)
#     return img

def imwrite(img_path, img, ext='.png'):
    suffix = Path(img_path).suffix
    if suffix != '':
        img_path = img_path.replace(suffix, ext)
    else:
        img_path += ext
    cv2.imencode(ext, img)[1].tofile(img_path)
```

## `textblock.py`

```py
from typing import List
import numpy as np
from shapely.geometry import Polygon
import math
import copy
from utils.imgproc_utils import union_area, xywh2xyxypoly, rotate_polygons
import cv2

LANG_LIST = ['eng', 'ja', 'unknown']
LANGCLS2IDX = {'eng': 0, 'ja': 1, 'unknown': 2}

class TextBlock(object):
    def __init__(self, xyxy: List, 
                       lines: List = None, 
                       language: str = 'unknown',
                       vertical: bool = False, 
                       font_size: float = -1,
                       distance: List = None,
                       angle: int = 0,
                       vec: List = None,
                       norm: float = -1,
                       merged: bool = False,
                       weight: float = -1,
                       text: List = None,
                       translation: str = "",
                       fg_r = 0,
                       fg_g = 0,
                       fg_b = 0,
                       bg_r = 0,
                       bg_g = 0,
                       bg_b = 0,                
                       line_spacing = 1.,
                       font_family: str = "",
                       bold: bool = False,
                       underline: bool = False,
                       italic: bool = False,
                       alignment: int = -1,
                       alpha: float = 255,
                       rich_text: str = "",
                       _bounding_rect: List = None,
                       accumulate_color = True,
                       default_stroke_width = 0.2,
                       target_lang: str = "",
                       **kwargs) -> None:
        self.xyxy = [int(num) for num in xyxy]                    # boundingbox of textblock
        self.lines = [] if lines is None else lines     # polygons of textlines
        self.vertical = vertical            # orientation of textlines
        self.language = language
        self.font_size = font_size          # font pixel size
        self.distance = None if distance is None else np.array(distance, np.float64)   # distance between textlines and "origin"          
        self.angle = angle                  # rotation angle of textlines

        self.vec = None if vec is None else np.array(vec, np.float64) # primary vector of textblock
        self.norm = norm                    # primary norm of textblock
        self.merged = merged
        self.weight = weight

        self.text = text if text is not None else []
        self.prob = 1

        self.translation = translation

        # note they're accumulative rgb values of textlines
        self.fg_r = fg_r                       
        self.fg_g = fg_g
        self.fg_b = fg_b
        self.bg_r = bg_r
        self.bg_g = bg_g
        self.bg_b = bg_b

        # self.stroke_width = stroke_width
        self.font_family: str = font_family
        self.bold: bool = bold
        self.underline: bool = underline
        self.italic: bool = italic
        self.alpha = alpha
        self.rich_text = rich_text
        self.line_spacing = line_spacing
        # self.alignment = alignment
        self._alignment = alignment
        self._target_lang = target_lang

        self._bounding_rect = _bounding_rect
        self.default_stroke_width = default_stroke_width
        self.accumulate_color = accumulate_color

    def adjust_bbox(self, with_bbox=False):
        lines = self.lines_array().astype(np.int32)
        if with_bbox:
            self.xyxy[0] = min(lines[..., 0].min(), self.xyxy[0])
            self.xyxy[1] = min(lines[..., 1].min(), self.xyxy[1])
            self.xyxy[2] = max(lines[..., 0].max(), self.xyxy[2])
            self.xyxy[3] = max(lines[..., 1].max(), self.xyxy[3])
        else:
            self.xyxy[0] = lines[..., 0].min()
            self.xyxy[1] = lines[..., 1].min()
            self.xyxy[2] = lines[..., 0].max()
            self.xyxy[3] = lines[..., 1].max()

    def sort_lines(self):
        if self.distance is not None:
            idx = np.argsort(self.distance)
            self.distance = self.distance[idx]
            lines = np.array(self.lines, dtype=np.int32)
            self.lines = lines[idx].tolist()

    def lines_array(self, dtype=np.float64):
        return np.array(self.lines, dtype=dtype)

    def aspect_ratio(self) -> float:
        min_rect = self.min_rect()
        middle_pnts = (min_rect[:, [1, 2, 3, 0]] + min_rect) / 2
        norm_v = np.linalg.norm(middle_pnts[:, 2] - middle_pnts[:, 0])
        norm_h = np.linalg.norm(middle_pnts[:, 1] - middle_pnts[:, 3])
        return norm_v / norm_h

    def center(self):
        xyxy = np.array(self.xyxy)
        return (xyxy[:2] + xyxy[2:]) / 2
    
    def min_rect(self, rotate_back=True):
        angled = self.angle != 0
        center = self.center()
        polygons = self.lines_array().reshape(-1, 8)
        if angled:
            polygons = rotate_polygons(center, polygons, self.angle)
        min_x = polygons[:, ::2].min()
        min_y = polygons[:, 1::2].min()
        max_x = polygons[:, ::2].max()
        max_y = polygons[:, 1::2].max()
        min_bbox = np.array([[min_x, min_y, max_x, min_y, max_x, max_y, min_x, max_y]])
        if angled and rotate_back:
            min_bbox = rotate_polygons(center, min_bbox, -self.angle)
        return min_bbox.reshape(-1, 4, 2).astype(np.int64)

    # equivalent to qt's boundingRect, ignore angle
    def bounding_rect(self):
        if self._bounding_rect is None:
        # if True:
            min_bbox = self.min_rect(rotate_back=False)[0]
            x, y = min_bbox[0]
            w, h = min_bbox[2] - min_bbox[0]
            return [x, y, w, h]
        return self._bounding_rect

    def __getattribute__(self, name: str):
        if name == 'pts':
            return self.lines_array()
        # else:
        return object.__getattribute__(self, name)

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, idx):
        return self.lines[idx]

    def to_dict(self):
        blk_dict = copy.deepcopy(vars(self))
        return blk_dict

    def get_transformed_region(self, img, idx, textheight) -> np.ndarray :
        im_h, im_w = img.shape[:2]
        direction = 'v' if self.vertical else 'h'
        src_pts = np.array(self.lines[idx], dtype=np.float64)

        if self.language == 'eng' or (self.language == 'unknown' and not self.vertical):
            e_size = self.font_size / 3
            src_pts[..., 0] += np.array([-e_size, e_size, e_size, -e_size])
            src_pts[..., 1] += np.array([-e_size, -e_size, e_size, e_size])
            src_pts[..., 0] = np.clip(src_pts[..., 0], 0, im_w)
            src_pts[..., 1] = np.clip(src_pts[..., 1], 0, im_h)

        middle_pnt = (src_pts[[1, 2, 3, 0]] + src_pts) / 2
        vec_v = middle_pnt[2] - middle_pnt[0]   # vertical vectors of textlines
        vec_h = middle_pnt[1] - middle_pnt[3]   # horizontal vectors of textlines
        ratio = np.linalg.norm(vec_v) / np.linalg.norm(vec_h)

        if direction == 'h' :
            h = int(textheight)
            w = int(round(textheight / ratio))
            dst_pts = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]]).astype(np.float32)
            M, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            region = cv2.warpPerspective(img, M, (w, h))
        elif direction == 'v' :
            w = int(textheight)
            h = int(round(textheight * ratio))
            dst_pts = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]]).astype(np.float32)
            M, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            region = cv2.warpPerspective(img, M, (w, h))
            region = cv2.rotate(region, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
        return region

    def get_text(self):
        if isinstance(self.text, str):
            return self.text
        return ' '.join(self.text).strip()

    def set_font_colors(self, frgb, srgb, accumulate=True):
        self.accumulate_color = accumulate
        num_lines = len(self.lines) if accumulate and len(self.lines) > 0 else 1
        # set font color
        frgb = np.array(frgb) * num_lines
        self.fg_r, self.fg_g, self.fg_b = frgb
        # set stroke color  
        srgb = np.array(srgb) * num_lines
        self.bg_r, self.bg_g, self.bg_b = srgb

    def get_font_colors(self, bgr=False):
        num_lines = len(self.lines)
        frgb = np.array([self.fg_r, self.fg_g, self.fg_b])
        brgb = np.array([self.bg_r, self.bg_g, self.bg_b])
        if self.accumulate_color:
            if num_lines > 0:
                frgb = (frgb / num_lines).astype(np.int32)
                brgb = (brgb / num_lines).astype(np.int32)
                if bgr:
                    return frgb[::-1], brgb[::-1]
                else:
                    return frgb, brgb
            else:
                return [0, 0, 0], [0, 0, 0]
        else:
            return frgb, brgb

    def xywh(self):
        x, y, w, h = self.xyxy
        return [x, y, w-x, h-y]

    # alignleft: 0, center: 1, right: 2 
    def alignment(self):
        if self._alignment >= 0:
            return self._alignment
        elif self.vertical:
            return 0
        lines = self.lines_array()
        if len(lines) == 1:
            return 0
        angled = self.angle != 0
        polygons = lines.reshape(-1, 8)
        if angled:
            polygons = rotate_polygons((0, 0), polygons, self.angle)
        polygons = polygons.reshape(-1, 4, 2)
        
        left_std = np.std(polygons[:, 0, 0])
        # right_std = np.std(polygons[:, 1, 0])
        center_std = np.std((polygons[:, 0, 0] + polygons[:, 1, 0]) / 2)
        if left_std < center_std:
            return 0
        else:
            return 1

    def target_lang(self):
        return self.target_lang

    @property
    def stroke_width(self):
        var = np.array([self.fg_r, self.fg_g, self.fg_b]) \
            - np.array([self.bg_r, self.bg_g, self.bg_b])
        var = np.abs(var).sum()
        if var > 40:
            return self.default_stroke_width
        return 0

def sort_textblk_list(blk_list: List[TextBlock], im_w: int, im_h: int) -> List[TextBlock]:
    if len(blk_list) == 0:
        return blk_list
    num_ja = 0
    xyxy = []
    for blk in blk_list:
        if blk.language == 'ja':
            num_ja += 1
        xyxy.append(blk.xyxy)
    xyxy = np.array(xyxy)
    flip_lr = num_ja > len(blk_list) / 2
    im_oriw = im_w
    if im_w > im_h:
        im_w /= 2
    num_gridy, num_gridx = 4, 3
    img_area = im_h * im_w
    center_x = (xyxy[:, 0] + xyxy[:, 2]) / 2
    if flip_lr:
        if im_w != im_oriw:
            center_x = im_oriw - center_x
        else:
            center_x = im_w - center_x
    grid_x = (center_x / im_w * num_gridx).astype(np.int32)
    center_y = (xyxy[:, 1] + xyxy[:, 3]) / 2
    grid_y = (center_y / im_h * num_gridy).astype(np.int32)
    grid_indices = grid_y * num_gridx + grid_x
    grid_weights = grid_indices * img_area + 1.2 * (center_x - grid_x * im_w / num_gridx) + (center_y - grid_y * im_h / num_gridy)
    if im_w != im_oriw:
        grid_weights[np.where(grid_x >= num_gridx)] += img_area * num_gridy * num_gridx
    
    for blk, weight in zip(blk_list, grid_weights):
        blk.weight = weight
    blk_list.sort(key=lambda blk: blk.weight)
    return blk_list

def examine_textblk(blk: TextBlock, im_w: int, im_h: int, sort: bool = False) -> None:
    lines = blk.lines_array()
    middle_pnts = (lines[:, [1, 2, 3, 0]] + lines) / 2
    vec_v = middle_pnts[:, 2] - middle_pnts[:, 0]   # vertical vectors of textlines
    vec_h = middle_pnts[:, 1] - middle_pnts[:, 3]   # horizontal vectors of textlines
    # if sum of vertical vectors is longer, then text orientation is vertical, and vice versa.
    center_pnts = (lines[:, 0] + lines[:, 2]) / 2
    v = np.sum(vec_v, axis=0)
    h = np.sum(vec_h, axis=0)
    norm_v, norm_h = np.linalg.norm(v), np.linalg.norm(h)
    if blk.language == 'ja':
        vertical = norm_v > norm_h
    else:
        vertical = norm_v > norm_h * 2
    # calculate distance between textlines and origin 
    if vertical:
        primary_vec, primary_norm = v, norm_v
        distance_vectors = center_pnts - np.array([[im_w, 0]], dtype=np.float64)   # vertical manga text is read from right to left, so origin is (imw, 0)
        font_size = int(round(norm_h / len(lines)))
    else:
        primary_vec, primary_norm = h, norm_h
        distance_vectors = center_pnts - np.array([[0, 0]], dtype=np.float64)
        font_size = int(round(norm_v / len(lines)))
    
    rotation_angle = int(math.atan2(primary_vec[1], primary_vec[0]) / math.pi * 180)     # rotation angle of textlines
    distance = np.linalg.norm(distance_vectors, axis=1)     # distance between textlinecenters and origin
    rad_matrix = np.arccos(np.einsum('ij, j->i', distance_vectors, primary_vec) / (distance * primary_norm))
    distance = np.abs(np.sin(rad_matrix) * distance)
    blk.lines = lines.astype(np.int32).tolist()
    blk.distance = distance
    blk.angle = rotation_angle
    if vertical:
        blk.angle -= 90
    if abs(blk.angle) < 3:
        blk.angle = 0
    blk.font_size = font_size
    blk.vertical = vertical
    blk.vec = primary_vec
    blk.norm = primary_norm
    if sort:
        blk.sort_lines()

def try_merge_textline(blk: TextBlock, blk2: TextBlock, fntsize_tol=1.3, distance_tol=2) -> bool:
    if blk2.merged:
        return False
    fntsize_div = blk.font_size / blk2.font_size
    num_l1, num_l2 = len(blk), len(blk2)
    fntsz_avg = (blk.font_size * num_l1 + blk2.font_size * num_l2) / (num_l1 + num_l2)
    vec_prod = blk.vec @ blk2.vec
    vec_sum = blk.vec + blk2.vec
    cos_vec = vec_prod / blk.norm / blk2.norm
    distance = blk2.distance[-1] - blk.distance[-1]
    distance_p1 = np.linalg.norm(np.array(blk2.lines[-1][0]) - np.array(blk.lines[-1][0]))
    l1, l2 = Polygon(blk.lines[-1]), Polygon(blk2.lines[-1])
    if not l1.intersects(l2):
        if fntsize_div > fntsize_tol or 1 / fntsize_div > fntsize_tol:
            return False
        if abs(cos_vec) < 0.866:   # cos30
            return False
        if distance > distance_tol * fntsz_avg or distance_p1 > fntsz_avg * 2.5:
            return False
    # merge
    blk.lines.append(blk2.lines[0])
    blk.vec = vec_sum
    blk.angle = int(round(np.rad2deg(math.atan2(vec_sum[1], vec_sum[0]))))
    if blk.vertical:
        blk.angle -= 90
    blk.norm = np.linalg.norm(vec_sum)
    blk.distance = np.append(blk.distance, blk2.distance[-1])
    blk.font_size = fntsz_avg
    blk2.merged = True
    return True

def merge_textlines(blk_list: List[TextBlock]) -> List[TextBlock]:
    if len(blk_list) < 2:
        return blk_list
    blk_list.sort(key=lambda blk: blk.distance[0])
    merged_list = []
    for ii, current_blk in enumerate(blk_list):
        if current_blk.merged:
            continue
        for jj, blk in enumerate(blk_list[ii+1:]):
            try_merge_textline(current_blk, blk)
        merged_list.append(current_blk)
    for blk in merged_list:
        blk.adjust_bbox(with_bbox=False)
    return merged_list

def split_textblk(blk: TextBlock):
    font_size, distance, lines = blk.font_size, blk.distance, blk.lines
    l0 = np.array(blk.lines[0])
    lines.sort(key=lambda line: np.linalg.norm(np.array(line[0]) - l0[0]))
    distance_tol = font_size * 2
    current_blk = copy.deepcopy(blk)
    current_blk.lines = [l0]
    sub_blk_list = [current_blk]
    textblock_splitted = False
    for jj, line in enumerate(lines[1:]):
        l1, l2 = Polygon(lines[jj]), Polygon(line)
        split = False
        if not l1.intersects(l2):
            line_disance = abs(distance[jj+1] - distance[jj])
            if line_disance > distance_tol:
                split = True
            elif blk.vertical and abs(blk.angle) < 15:
                if len(current_blk.lines) > 1 or line_disance > font_size:
                    split = abs(lines[jj][0][1] - line[0][1]) > font_size
        if split:
            current_blk = copy.deepcopy(current_blk)
            current_blk.lines = [line]
            sub_blk_list.append(current_blk)
        else:
            current_blk.lines.append(line)
    if len(sub_blk_list) > 1:
        textblock_splitted = True
        for current_blk in sub_blk_list:
            current_blk.adjust_bbox(with_bbox=False)
    return textblock_splitted, sub_blk_list

def group_output(blks, lines, im_w, im_h, mask=None, sort_blklist=True) -> List[TextBlock]:
    blk_list: List[TextBlock] = []
    scattered_lines = {'ver': [], 'hor': []}
    for bbox, cls, conf in zip(*blks):
        # cls could give wrong result
        blk = TextBlock(bbox, language=LANG_LIST[cls])
        blk.confidence = float(conf)  # 设置真实置信度
        blk.prob = float(conf)        # 保持兼容性
        blk_list.append(blk)

    # step1: filter & assign lines to textblocks
    bbox_score_thresh = 0.4
    mask_score_thresh = 0.1
    for ii, line in enumerate(lines):
        bx1, bx2 = line[:, 0].min(), line[:, 0].max()
        by1, by2 = line[:, 1].min(), line[:, 1].max()
        bbox_score, bbox_idx = -1, -1
        line_area = (by2-by1) * (bx2-bx1)
        for jj, blk in enumerate(blk_list):
            score = union_area(blk.xyxy, [bx1, by1, bx2, by2]) / line_area
            if bbox_score < score:
                bbox_score = score
                bbox_idx = jj
        if bbox_score > bbox_score_thresh:
            blk_list[bbox_idx].lines.append(line)
        else:   # if no textblock was assigned, check whether there is "enough" textmask
            if mask is not None:
                mask_score = mask[by1: by2, bx1: bx2].mean() / 255
                if mask_score < mask_score_thresh:
                    continue
            blk = TextBlock([bx1, by1, bx2, by2], [line])
            examine_textblk(blk, im_w, im_h, sort=False)
            if blk.vertical:
                scattered_lines['ver'].append(blk)
            else:
                scattered_lines['hor'].append(blk)

    # step2: filter textblocks, sort & split textlines
    final_blk_list = []
    for blk in blk_list:
        # filter textblocks 
        if len(blk.lines) == 0:
            bx1, by1, bx2, by2 = blk.xyxy
            if mask is not None:
                mask_score = mask[by1: by2, bx1: bx2].mean() / 255
                if mask_score < mask_score_thresh:
                    continue
            xywh = np.array([[bx1, by1, bx2-bx1, by2-by1]])
            blk.lines = xywh2xyxypoly(xywh).reshape(-1, 4, 2).tolist()
        examine_textblk(blk, im_w, im_h, sort=True)
        
        # split manga text if there is a distance gap
        textblock_splitted = False
        if len(blk.lines) > 1:
            if blk.language == 'ja':
                textblock_splitted = True
            elif blk.vertical:
                textblock_splitted = True
        if textblock_splitted:
            textblock_splitted, sub_blk_list = split_textblk(blk)
        else:
            sub_blk_list = [blk]
        # modify textblock to fit its textlines
        if not textblock_splitted:
            for blk in sub_blk_list:
                blk.adjust_bbox(with_bbox=True)
        final_blk_list += sub_blk_list

    # step3: merge scattered lines, sort textblocks by "grid"
    final_blk_list += merge_textlines(scattered_lines['hor'])
    final_blk_list += merge_textlines(scattered_lines['ver'])
    if sort_blklist:
        final_blk_list = sort_textblk_list(final_blk_list, im_w, im_h)

    for blk in final_blk_list:
        if blk.language == 'eng' and not blk.vertical:
            num_lines = len(blk.lines)
            if num_lines == 0:
                continue
            # blk.line_spacing = blk.bounding_rect()[3] / num_lines / blk.font_size
            expand_size = max(int(blk.font_size * 0.1), 2)
            rad = np.deg2rad(blk.angle)
            shifted_vec = np.array([[[-1, -1],[1, -1],[1, 1],[-1, 1]]])
            shifted_vec = shifted_vec * np.array([[[np.sin(rad), np.cos(rad)]]]) * expand_size
            lines = blk.lines_array() + shifted_vec
            lines[..., 0] = np.clip(lines[..., 0], 0, im_w-1)
            lines[..., 1] = np.clip(lines[..., 1], 0, im_h-1)
            blk.lines = lines.astype(np.int64).tolist()
            blk.font_size += expand_size
            
    return final_blk_list

def visualize_textblocks(canvas, blk_list:  List[TextBlock]):
    lw = max(round(sum(canvas.shape) / 2 * 0.003), 2)  # line width
    for ii, blk in enumerate(blk_list):
        bx1, by1, bx2, by2 = blk.xyxy
        cv2.rectangle(canvas, (bx1, by1), (bx2, by2), (127, 255, 127), lw)
        lines = blk.lines_array(dtype=np.int32)
        for jj, line in enumerate(lines):
            cv2.putText(canvas, str(jj), line[0], cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,127,0), 1)
            cv2.polylines(canvas, [line], True, (0,127,255), 2)
        cv2.polylines(canvas, [blk.min_rect()], True, (127,127,0), 2)
        center = [int((bx1 + bx2)/2), int((by1 + by2)/2)]
        cv2.putText(canvas, str(blk.angle), center, cv2.FONT_HERSHEY_SIMPLEX, 1, (127,127,255), 2)
        cv2.putText(canvas, str(ii), (bx1, by1 + lw + 2), 0, lw / 3, (255,127,127), max(lw-1, 1), cv2.LINE_AA)
    return canvas


```

## `textmask.py`

```py
from os import stat
from typing import List
import cv2
import numpy as np
from utils.textblock import TextBlock
from utils.imgproc_utils import draw_connected_labels, expand_textwindow, union_area

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LANG_ENG = 0
LANG_JPN = 1

REFINEMASK_INPAINT = 0
REFINEMASK_ANNOTATION = 1

def get_topk_color(color_list, bins, k=3, color_var=10, bin_tol=0.001):
    idx = np.argsort(bins * -1)
    color_list, bins = color_list[idx], bins[idx]
    top_colors = [color_list[0]]
    bin_tol = np.sum(bins) * bin_tol
    if len(color_list) > 1:
        for color, bin in zip(color_list[1:], bins[1:]):
            if np.abs(np.array(top_colors) - color).min() > color_var:
                top_colors.append(color)
            if len(top_colors) >= k or bin < bin_tol:
                break
    return top_colors

def minxor_thresh(threshed, mask, dilate=False):
    neg_threshed = 255 - threshed
    e_size = 1
    if dilate:
        element = cv2.getStructuringElement(cv2.MORPH_RECT, (2 * e_size + 1, 2 * e_size + 1),(e_size, e_size))
        neg_threshed = cv2.dilate(neg_threshed, element, iterations=1)
        threshed = cv2.dilate(threshed, element, iterations=1)
    neg_xor_sum = cv2.bitwise_xor(neg_threshed, mask).sum()
    xor_sum = cv2.bitwise_xor(threshed, mask).sum()
    if neg_xor_sum < xor_sum:
        return neg_threshed, neg_xor_sum
    else:
        return threshed, xor_sum

def get_otsuthresh_masklist(img, pred_mask, per_channel=False) -> List[np.ndarray]:
    channels = [img[..., 0], img[..., 1], img[..., 2]]
    mask_list = []
    for c in channels:
        _, threshed = cv2.threshold(c, 1, 255, cv2.THRESH_OTSU+cv2.THRESH_BINARY)
        threshed, xor_sum = minxor_thresh(threshed, pred_mask, dilate=False)
        mask_list.append([threshed, xor_sum])
    mask_list.sort(key=lambda x: x[1])
    if per_channel:
        return mask_list
    else:
        return [mask_list[0]]

def get_topk_masklist(im_grey, pred_mask):
    if len(im_grey.shape) == 3 and im_grey.shape[-1] == 3:
        im_grey = cv2.cvtColor(im_grey, cv2.COLOR_BGR2GRAY)
    msk = np.ascontiguousarray(pred_mask)
    candidate_grey_px = im_grey[np.where(cv2.erode(msk, np.ones((3,3), np.uint8), iterations=1) > 127)]
    bin, his = np.histogram(candidate_grey_px, bins=255)
    topk_color = get_topk_color(his, bin, color_var=10, k=3)
    color_range = 30
    mask_list = list()
    for ii, color in enumerate(topk_color):
        c_top = min(color+color_range, 255)
        c_bottom = c_top - 2 * color_range
        threshed = cv2.inRange(im_grey, c_bottom, c_top)
        threshed, xor_sum = minxor_thresh(threshed, msk)
        mask_list.append([threshed, xor_sum])
    return mask_list

def merge_mask_list(mask_list, pred_mask, blk: TextBlock = None, pred_thresh=30, text_window=None, filter_with_lines=False, refine_mode=REFINEMASK_INPAINT):
    mask_list.sort(key=lambda x: x[1])
    linemask = None
    if blk is not None and filter_with_lines:
        linemask = np.zeros_like(pred_mask)
        lines = blk.lines_array(dtype=np.int64)
        for line in lines:
            line[..., 0] -= text_window[0]
            line[..., 1] -= text_window[1]
            cv2.fillPoly(linemask, [line], 255)
        linemask = cv2.dilate(linemask, np.ones((3, 3), np.uint8), iterations=3)
    
    if pred_thresh > 0:
        e_size = 1
        element = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * e_size + 1, 2 * e_size + 1),(e_size, e_size))      
        pred_mask = cv2.erode(pred_mask, element, iterations=1)
        _, pred_mask = cv2.threshold(pred_mask, 60, 255, cv2.THRESH_BINARY)
    connectivity = 8
    mask_merged = np.zeros_like(pred_mask)
    for ii, (candidate_mask, xor_sum) in enumerate(mask_list):
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(candidate_mask, connectivity, cv2.CV_16U)
        for label_index, stat, centroid in zip(range(num_labels), stats, centroids):
            if label_index != 0: # skip background label
                x, y, w, h, area = stat
                if w * h < 3:
                    continue
                x1, y1, x2, y2 = x, y, x+w, y+h
                label_local = labels[y1: y2, x1: x2]
                label_coordinates = np.where(label_local==label_index)
                tmp_merged = np.zeros_like(label_local, np.uint8)
                tmp_merged[label_coordinates] = 255
                tmp_merged = cv2.bitwise_or(mask_merged[y1: y2, x1: x2], tmp_merged)
                xor_merged = cv2.bitwise_xor(tmp_merged, pred_mask[y1: y2, x1: x2]).sum()
                xor_origin = cv2.bitwise_xor(mask_merged[y1: y2, x1: x2], pred_mask[y1: y2, x1: x2]).sum()
                if xor_merged < xor_origin:
                    mask_merged[y1: y2, x1: x2] = tmp_merged

    if refine_mode == REFINEMASK_INPAINT:
        mask_merged = cv2.dilate(mask_merged, np.ones((3, 3), np.uint8), iterations=1)
    # fill holes
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(255-mask_merged, connectivity, cv2.CV_16U)
    sorted_area = np.sort(stats[:, -1])
    if len(sorted_area) > 1:
        area_thresh = sorted_area[-2]
    else:
        area_thresh = sorted_area[-1]
    for label_index, stat, centroid in zip(range(num_labels), stats, centroids):
        x, y, w, h, area = stat
        if area < area_thresh:
            x1, y1, x2, y2 = x, y, x+w, y+h
            label_local = labels[y1: y2, x1: x2]
            label_coordinates = np.where(label_local==label_index)
            tmp_merged = np.zeros_like(label_local, np.uint8)
            tmp_merged[label_coordinates] = 255
            tmp_merged = cv2.bitwise_or(mask_merged[y1: y2, x1: x2], tmp_merged)
            xor_merged = cv2.bitwise_xor(tmp_merged, pred_mask[y1: y2, x1: x2]).sum()
            xor_origin = cv2.bitwise_xor(mask_merged[y1: y2, x1: x2], pred_mask[y1: y2, x1: x2]).sum()
            if xor_merged < xor_origin:
                mask_merged[y1: y2, x1: x2] = tmp_merged
    return mask_merged


def refine_undetected_mask(img: np.ndarray, mask_pred: np.ndarray, mask_refined: np.ndarray, blk_list: List[TextBlock], refine_mode=REFINEMASK_INPAINT):
    mask_pred[np.where(mask_refined > 30)] = 0
    _, pred_mask_t = cv2.threshold(mask_pred, 30, 255, cv2.THRESH_BINARY)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(pred_mask_t, 4, cv2.CV_16U)
    valid_labels = np.where(stats[:, -1] > 50)[0]
    seg_blk_list = []
    if len(valid_labels) > 0:
        for lab_index in valid_labels[1:]:
            x, y, w, h, area = stats[lab_index]
            bx1, by1 = x, y
            bx2, by2 = x+w, y+h
            bbox = [bx1, by1, bx2, by2]
            bbox_score = -1
            for blk in blk_list:
                bbox_s = union_area(blk.xyxy, bbox)
                if bbox_s > bbox_score:
                    bbox_score = bbox_s
            if bbox_score / w / h < 0.5:
                seg_blk_list.append(TextBlock(bbox))
    if len(seg_blk_list) > 0:
        mask_refined = cv2.bitwise_or(mask_refined, refine_mask(img, mask_pred, seg_blk_list, refine_mode=refine_mode))
    return mask_refined


def refine_mask(img: np.ndarray, pred_mask: np.ndarray, blk_list: List[TextBlock], refine_mode: int = REFINEMASK_INPAINT) -> np.ndarray:
    mask_refined = np.zeros_like(pred_mask)
    for blk in blk_list:
        bx1, by1, bx2, by2 = expand_textwindow(img.shape, blk.xyxy, expand_r=16)
        im = np.ascontiguousarray(img[by1: by2, bx1: bx2])
        msk = np.ascontiguousarray(pred_mask[by1: by2, bx1: bx2])
        mask_list = get_topk_masklist(im, msk)
        mask_list += get_otsuthresh_masklist(im, msk, per_channel=False)
        mask_merged = merge_mask_list(mask_list, msk, blk=blk, text_window=[bx1, by1, bx2, by2], refine_mode=refine_mode)
        mask_refined[by1: by2, bx1: bx2] = cv2.bitwise_or(mask_refined[by1: by2, bx1: bx2], mask_merged)
    return mask_refined

```

## `weight_init.py`

```py
import torch.nn as nn
import torch

def constant_init(module, val, bias=0):
    nn.init.constant_(module.weight, val)
    if hasattr(module, 'bias') and module.bias is not None:
        nn.init.constant_(module.bias, bias)

def xavier_init(module, gain=1, bias=0, distribution='normal'):
    assert distribution in ['uniform', 'normal']
    if distribution == 'uniform':
        nn.init.xavier_uniform_(module.weight, gain=gain)
    else:
        nn.init.xavier_normal_(module.weight, gain=gain)
    if hasattr(module, 'bias') and module.bias is not None:
        nn.init.constant_(module.bias, bias)


def normal_init(module, mean=0, std=1, bias=0):
    nn.init.normal_(module.weight, mean, std)
    if hasattr(module, 'bias') and module.bias is not None:
        nn.init.constant_(module.bias, bias)


def uniform_init(module, a=0, b=1, bias=0):
    nn.init.uniform_(module.weight, a, b)
    if hasattr(module, 'bias') and module.bias is not None:
        nn.init.constant_(module.bias, bias)


def kaiming_init(module,
                 a=0,
                 is_rnn=False,
                 mode='fan_in',
                 nonlinearity='leaky_relu',
                 bias=0,
                 distribution='normal'):
    assert distribution in ['uniform', 'normal']
    if distribution == 'uniform':
        if is_rnn:
            for name, param in module.named_parameters():
                if 'bias' in name:
                    nn.init.constant_(param, bias)
                elif 'weight' in name:
                    nn.init.kaiming_uniform_(param,
                                             a=a,
                                             mode=mode,
                                             nonlinearity=nonlinearity)
        else:
            nn.init.kaiming_uniform_(module.weight,
                                     a=a,
                                     mode=mode,
                                     nonlinearity=nonlinearity)

    else:
        if is_rnn:
            for name, param in module.named_parameters():
                if 'bias' in name:
                    nn.init.constant_(param, bias)
                elif 'weight' in name:
                    nn.init.kaiming_normal_(param,
                                            a=a,
                                            mode=mode,
                                            nonlinearity=nonlinearity)
        else:
            nn.init.kaiming_normal_(module.weight,
                                    a=a,
                                    mode=mode,
                                    nonlinearity=nonlinearity)

    if not is_rnn and hasattr(module, 'bias') and module.bias is not None:
        nn.init.constant_(module.bias, bias)


def bilinear_kernel(in_channels, out_channels, kernel_size):
    factor = (kernel_size + 1) // 2
    if kernel_size % 2 == 1:
        center = factor - 1
    else:
        center = factor - 0.5
    og = (torch.arange(kernel_size).reshape(-1, 1),
          torch.arange(kernel_size).reshape(1, -1))
    filt = (1 - torch.abs(og[0] - center) / factor) * \
           (1 - torch.abs(og[1] - center) / factor)
    weight = torch.zeros((in_channels, out_channels,
                          kernel_size, kernel_size))
    weight[range(in_channels), range(out_channels), :, :] = filt
    return weight


def init_weights(m):
    # for m in modules:

    if isinstance(m, nn.Conv2d):
        kaiming_init(m)
    elif isinstance(m, (nn.BatchNorm2d, nn.GroupNorm)):
        constant_init(m, 1)
    elif isinstance(m, nn.Linear):
        xavier_init(m)
    elif isinstance(m, (nn.LSTM, nn.LSTMCell)):
        kaiming_init(m, is_rnn=True)
    # elif isinstance(m, nn.ConvTranspose2d):
    #     m.weight.data.copy_(bilinear_kernel(m.in_channels, m.out_channels, 4));

```

## `yolov5_utils.py`

```py
import math
import torch
import torch.nn as nn
import pkg_resources as pkg
import torch.nn.functional as F
import cv2
import numpy as np
import time
import torchvision

def scale_img(img, ratio=1.0, same_shape=False, gs=32):  # img(16,3,256,416)
    # scales img(bs,3,y,x) by ratio constrained to gs-multiple
    if ratio == 1.0:
        return img
    else:
        h, w = img.shape[2:]
        s = (int(h * ratio), int(w * ratio))  # new size
        img = F.interpolate(img, size=s, mode='bilinear', align_corners=False)  # resize
        if not same_shape:  # pad/crop img
            h, w = (math.ceil(x * ratio / gs) * gs for x in (h, w))
        return F.pad(img, [0, w - s[1], 0, h - s[0]], value=0.447)  # value = imagenet mean

def fuse_conv_and_bn(conv, bn):
    # Fuse convolution and batchnorm layers https://tehnokv.com/posts/fusing-batchnorm-and-conv/
    fusedconv = nn.Conv2d(conv.in_channels,
                          conv.out_channels,
                          kernel_size=conv.kernel_size,
                          stride=conv.stride,
                          padding=conv.padding,
                          groups=conv.groups,
                          bias=True).requires_grad_(False).to(conv.weight.device)

    # prepare filters
    w_conv = conv.weight.clone().view(conv.out_channels, -1)
    w_bn = torch.diag(bn.weight.div(torch.sqrt(bn.eps + bn.running_var)))
    fusedconv.weight.copy_(torch.mm(w_bn, w_conv).view(fusedconv.weight.shape))

    # prepare spatial bias
    b_conv = torch.zeros(conv.weight.size(0), device=conv.weight.device) if conv.bias is None else conv.bias
    b_bn = bn.bias - bn.weight.mul(bn.running_mean).div(torch.sqrt(bn.running_var + bn.eps))
    fusedconv.bias.copy_(torch.mm(w_bn, b_conv.reshape(-1, 1)).reshape(-1) + b_bn)

    return fusedconv

def check_anchor_order(m):
    # Check anchor order against stride order for YOLOv5 Detect() module m, and correct if necessary
    a = m.anchors.prod(-1).view(-1)  # anchor area
    da = a[-1] - a[0]  # delta a
    ds = m.stride[-1] - m.stride[0]  # delta s
    if da.sign() != ds.sign():  # same order
        m.anchors[:] = m.anchors.flip(0)

def initialize_weights(model):
    for m in model.modules():
        t = type(m)
        if t is nn.Conv2d:
            pass  # nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
        elif t is nn.BatchNorm2d:
            m.eps = 1e-3
            m.momentum = 0.03
        elif t in [nn.Hardswish, nn.LeakyReLU, nn.ReLU, nn.ReLU6, nn.SiLU]:
            m.inplace = True

def make_divisible(x, divisor):
    # Returns nearest x divisible by divisor
    if isinstance(divisor, torch.Tensor):
        divisor = int(divisor.max())  # to int
    return math.ceil(x / divisor) * divisor

def intersect_dicts(da, db, exclude=()):
    # Dictionary intersection of matching keys and shapes, omitting 'exclude' keys, using da values
    return {k: v for k, v in da.items() if k in db and not any(x in k for x in exclude) and v.shape == db[k].shape}

def check_version(current='0.0.0', minimum='0.0.0', name='version ', pinned=False, hard=False):
    # Check version vs. required version
    current, minimum = (pkg.parse_version(x) for x in (current, minimum))
    result = (current == minimum) if pinned else (current >= minimum)  # bool
    if hard:  # assert min requirements met
        assert result, f'{name}{minimum} required by YOLOv5, but {name}{current} is currently installed'
    else:
        return result

class Colors:
    # Ultralytics color palette https://ultralytics.com/
    def __init__(self):
        # hex = matplotlib.colors.TABLEAU_COLORS.values()
        hex = ('FF3838', 'FF9D97', 'FF701F', 'FFB21D', 'CFD231', '48F90A', '92CC17', '3DDB86', '1A9334', '00D4BB',
               '2C99A8', '00C2FF', '344593', '6473FF', '0018EC', '8438FF', '520085', 'CB38FF', 'FF95C8', 'FF37C7')
        self.palette = [self.hex2rgb('#' + c) for c in hex]
        self.n = len(self.palette)

    def __call__(self, i, bgr=False):
        c = self.palette[int(i) % self.n]
        return (c[2], c[1], c[0]) if bgr else c

    @staticmethod
    def hex2rgb(h):  # rgb order (PIL)
        return tuple(int(h[1 + i:1 + i + 2], 16) for i in (0, 2, 4))

def box_iou(box1, box2):
    # https://github.com/pytorch/vision/blob/master/torchvision/ops/boxes.py
    """
    Return intersection-over-union (Jaccard index) of boxes.
    Both sets of boxes are expected to be in (x1, y1, x2, y2) format.
    Arguments:
        box1 (Tensor[N, 4])
        box2 (Tensor[M, 4])
    Returns:
        iou (Tensor[N, M]): the NxM matrix containing the pairwise
            IoU values for every element in boxes1 and boxes2
    """

    def box_area(box):
        # box = 4xn
        return (box[2] - box[0]) * (box[3] - box[1])

    area1 = box_area(box1.T)
    area2 = box_area(box2.T)

    # inter(N,M) = (rb(N,M,2) - lt(N,M,2)).clamp(0).prod(2)
    inter = (torch.min(box1[:, None, 2:], box2[:, 2:]) - torch.max(box1[:, None, :2], box2[:, :2])).clamp(0).prod(2)
    return inter / (area1[:, None] + area2 - inter)  # iou = inter / (area1 + area2 - inter)

def non_max_suppression(prediction, conf_thres=0.25, iou_thres=0.45, classes=None, agnostic=False, multi_label=False,
                        labels=(), max_det=300):
    """Runs Non-Maximum Suppression (NMS) on inference results

    Returns:
         list of detections, on (n,6) tensor per image [xyxy, conf, cls]
    """

    if isinstance(prediction, np.ndarray):
        prediction = torch.from_numpy(prediction)

    nc = prediction.shape[2] - 5  # number of classes
    xc = prediction[..., 4] > conf_thres  # candidates

    # Checks
    assert 0 <= conf_thres <= 1, f'Invalid Confidence threshold {conf_thres}, valid values are between 0.0 and 1.0'
    assert 0 <= iou_thres <= 1, f'Invalid IoU {iou_thres}, valid values are between 0.0 and 1.0'

    # Settings
    min_wh, max_wh = 2, 4096  # (pixels) minimum and maximum box width and height
    max_nms = 30000  # maximum number of boxes into torchvision.ops.nms()
    time_limit = 10.0  # seconds to quit after
    redundant = True  # require redundant detections
    multi_label &= nc > 1  # multiple labels per box (adds 0.5ms/img)
    merge = False  # use merge-NMS

    t = time.time()
    output = [torch.zeros((0, 6), device=prediction.device)] * prediction.shape[0]
    for xi, x in enumerate(prediction):  # image index, image inference
        # Apply constraints
        # x[((x[..., 2:4] < min_wh) | (x[..., 2:4] > max_wh)).any(1), 4] = 0  # width-height
        x = x[xc[xi]]  # confidence

        # Cat apriori labels if autolabelling
        if labels and len(labels[xi]):
            l = labels[xi]
            v = torch.zeros((len(l), nc + 5), device=x.device)
            v[:, :4] = l[:, 1:5]  # box
            v[:, 4] = 1.0  # conf
            v[range(len(l)), l[:, 0].long() + 5] = 1.0  # cls
            x = torch.cat((x, v), 0)

        # If none remain process next image
        if not x.shape[0]:
            continue

        # Compute conf
        x[:, 5:] *= x[:, 4:5]  # conf = obj_conf * cls_conf

        # Box (center x, center y, width, height) to (x1, y1, x2, y2)
        box = xywh2xyxy(x[:, :4])

        # Detections matrix nx6 (xyxy, conf, cls)
        if multi_label:
            i, j = (x[:, 5:] > conf_thres).nonzero(as_tuple=False).T
            x = torch.cat((box[i], x[i, j + 5, None], j[:, None].float()), 1)
        else:  # best class only
            conf, j = x[:, 5:].max(1, keepdim=True)
            x = torch.cat((box, conf, j.float()), 1)[conf.view(-1) > conf_thres]

        # Filter by class
        if classes is not None:
            x = x[(x[:, 5:6] == torch.tensor(classes, device=x.device)).any(1)]

        # Apply finite constraint
        # if not torch.isfinite(x).all():
        #     x = x[torch.isfinite(x).all(1)]

        # Check shape
        n = x.shape[0]  # number of boxes
        if not n:  # no boxes
            continue
        elif n > max_nms:  # excess boxes
            x = x[x[:, 4].argsort(descending=True)[:max_nms]]  # sort by confidence

        # Batched NMS
        c = x[:, 5:6] * (0 if agnostic else max_wh)  # classes
        boxes, scores = x[:, :4] + c, x[:, 4]  # boxes (offset by class), scores
        i = torchvision.ops.nms(boxes, scores, iou_thres)  # NMS
        if i.shape[0] > max_det:  # limit detections
            i = i[:max_det]
        if merge and (1 < n < 3E3):  # Merge NMS (boxes merged using weighted mean)
            # update boxes as boxes(i,4) = weights(i,n) * boxes(n,4)
            iou = box_iou(boxes[i], boxes) > iou_thres  # iou matrix
            weights = iou * scores[None]  # box weights
            x[i, :4] = torch.mm(weights, x[:, :4]).float() / weights.sum(1, keepdim=True)  # merged boxes
            if redundant:
                i = i[iou.sum(1) > 1]  # require redundancy

        output[xi] = x[i]
        if (time.time() - t) > time_limit:
            print(f'WARNING: NMS time limit {time_limit}s exceeded')
            break  # time limit exceeded

    return output

def xywh2xyxy(x):
    # Convert nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2] where xy1=top-left, xy2=bottom-right
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[:, 0] = x[:, 0] - x[:, 2] / 2  # top left x
    y[:, 1] = x[:, 1] - x[:, 3] / 2  # top left y
    y[:, 2] = x[:, 0] + x[:, 2] / 2  # bottom right x
    y[:, 3] = x[:, 1] + x[:, 3] / 2  # bottom right y
    return y

DEFAULT_LANG_LIST = ['eng', 'ja']
def draw_bbox(pred, img, lang_list=None):
    if lang_list is None:
        lang_list = DEFAULT_LANG_LIST
    lw = max(round(sum(img.shape) / 2 * 0.003), 2)  # line width
    pred = pred.astype(np.int32)
    colors = Colors()
    img = np.copy(img)
    for ii, obj in enumerate(pred):
        p1, p2 = (obj[0], obj[1]), (obj[2], obj[3])
        label = lang_list[obj[-1]] + str(ii+1)
        cv2.rectangle(img, p1, p2, colors(obj[-1], bgr=True), lw, lineType=cv2.LINE_AA)
        t_w, t_h = cv2.getTextSize(label, 0, fontScale=lw / 3, thickness=lw)[0]
        cv2.putText(img, label, (p1[0], p1[1] + t_h + 2), 0, lw / 3, colors(obj[-1], bgr=True), max(lw-1, 1), cv2.LINE_AA)
    return img
```

## `__init__.py`

```py

```

