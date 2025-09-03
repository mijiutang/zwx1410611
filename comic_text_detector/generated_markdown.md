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
            },
            
            # 日志配置
            "logging": {
                "level": "INFO",
                "file": "logs/app.log",
                "max_file_size": "10MB",
                "backup_count": 3
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
            self.project_root / "logs"
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

# `fix_imports.py`

```py
import cv2
import numpy as np
import json
import os
from pathlib import Path

def extract_text_regions_from_json(json_file_path, output_dir="output_text_blocks"):
    """
    根据JSON文件中的文本行坐标提取文本区域：
    1. 原图文字行以外部分涂白
    2. 按 bbox 裁剪每个文本块，保存到指定文件夹
    """
    
    # 读取JSON文件
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 获取原图路径和图片名
    image_path = data['image_path']
    image_name = data['image_name']
    
    # 检查原图是否存在
    if not os.path.exists(image_path):
        print(f"原图不存在: {image_path}")
        return
    
    # 读取原图
    original_img = cv2.imread(image_path)
    if original_img is None:
        print(f"无法读取图像: {image_path}")
        return
    
    height, width = original_img.shape[:2]
    
    # 创建白色背景图像
    result_img = np.full((height, width, 3), 255, dtype=np.uint8)
    
    # 创建掩码
    mask = np.zeros((height, width), dtype=np.uint8)
    
    # 创建输出文件夹
    os.makedirs(output_dir, exist_ok=True)
    
    # 处理每个文本区域
    for idx, region in enumerate(data['text_regions']):
        lines = region['lines']
        
        # 处理每条文本行
        for line in lines:
            points = np.array(line, dtype=np.int32)
            cv2.fillPoly(mask, [points], 255)
        
        # 按 bbox 裁剪文本块
        x1, y1, x2, y2 = region['bbox']
        cropped = original_img[y1:y2, x1:x2]
        
        crop_filename = f"{image_name}_{idx}.jpg"
        crop_path = os.path.join(output_dir, crop_filename)
        cv2.imwrite(crop_path, cropped)
    
    # 将原图中的文本区域复制到白底图像
    result_img[mask == 255] = original_img[mask == 255]
    
    # 保存涂白结果
    output_full_path = os.path.join(os.getcwd(), f"{image_name}_text_only.jpg")
    cv2.imwrite(output_full_path, result_img)
    
    print(f"文本区域涂白结果已保存到: {output_full_path}")
    print(f"按 bbox 裁剪的文本块已保存到: {output_dir}")
    
    # 打印统计信息
    total_regions = data['stats']['total_regions']
    avg_confidence = data['stats']['avg_confidence']
    print(f"处理了 {total_regions} 个文本区域，平均置信度: {avg_confidence:.3f}")


if __name__ == "__main__":
    json_file = r"comic_text_detector\data\results\132_result.json"  # 请修改为实际的JSON文件路径
    
    if os.path.exists(json_file):
        extract_text_regions_from_json(json_file)
    else:
        print(f"JSON文件不存在: {json_file}")

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

from src.ui.main_window import ComicTextDetectorGUI
from config.config import Config
from src.utils.general import set_logging

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

# `src`

## `core`

### `basemodel.py`

```py
# 修复后的 basemodel.py - 更新所有导入路径

from ..utils.general import CUDA, DEVICE
from ..models.yolov5.yolo import Model
import torch
import cv2
import numpy as np
from src.models.yolov5.yolo import load_yolov5_ckpt  # 修复导入路径
from src.utils.yolov5_utils import fuse_conv_and_bn  # 修复导入路径
import glob
import torch.nn as nn
from src.utils.weight_init import init_weights  # 修复导入路径
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

### `detector.py`

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
    
    def get_project_ocr_results(self) -> Dict[str, str]:
        """获取整个项目的OCR结果"""
        project_ocr = {}
        for result in self.detection_results:
            if result.has_ocr_results:
                # 合并每张图片的OCR文本
                all_texts = []
                for region_key, text in result.ocr_results.items():
                    if text.strip():
                        all_texts.append(text.strip())
                combined_text = " ".join(all_texts)
                project_ocr[result.image_name] = combined_text
            else:
                project_ocr[result.image_name] = ""
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
            if any(text.strip() for text in project_ocr.values()):
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
        
        Args:
            image_files: 图片文件路径列表
            project_name: 项目名称
            output_dir: 输出目录
            include_ocr: 是否包含OCR处理
            progress_callback: 进度回调函数 (current, total, message) -> None
            
        Returns:
            ProjectResults: 项目结果对象
        """
        project_results = ProjectResults(project_name)
        total_files = len(image_files)
        
        print(f"开始批量处理项目: {project_name} ({total_files} 个文件)")
        
        for i, image_path in enumerate(image_files, 1):
            try:
                file_name = Path(image_path).name
                
                if progress_callback:
                    progress_callback(i, total_files, f"正在检测: {file_name}")
                
                # 执行检测
                results = self.detect_only(image_path)
                
                # 如果需要OCR，执行OCR
                if include_ocr:
                    if progress_callback:
                        progress_callback(i, total_files, f"正在OCR: {file_name}")
                    results = self.run_ocr_on_results(results)
                
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
        
        # 保存项目结果
        output_project_dir = project_results.save_to_directory(output_dir, self.config.output_params)
        
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
        from src.utils.io_utils import find_all_imgs
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

### `inference.py`

```py
import json
from src.core.basemodel import TextDetBase, TextDetBaseDNN  # 修复导入路径
import os.path as osp
from tqdm import tqdm
import numpy as np
import cv2
import torch
from pathlib import Path
import torch
from src.utils.yolov5_utils import non_max_suppression  # 修复导入路径
from src.utils.db_utils import SegDetectorRepresenter  # 修复导入路径
from src.utils.io_utils import imread, imwrite, find_all_imgs, NumpyEncoder  # 修复导入路径
from src.utils.imgproc_utils import letterbox, xyxy2yolo, get_yololabel_strings  # 修复导入路径
from src.utils.textblock import TextBlock, group_output, visualize_textblocks  # 修复导入路径
from src.utils.textmask import refine_mask, refine_undetected_mask, REFINEMASK_INPAINT, REFINEMASK_ANNOTATION  # 修复导入路径
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

### `__init__.py`

```py

```

## `models`

### `yolov5`

#### `common.py`

```py
# YOLOv5 🚀 by Ultralytics, GPL-3.0 license
"""
Common modules
"""

import json
import math
import platform
import warnings
from collections import OrderedDict, namedtuple
from copy import copy
from pathlib import Path

import cv2
import numpy as np
import requests
import torch
import torch.nn as nn
from PIL import Image
from torch.cuda import amp

# 修复导入路径
from src.utils.yolov5_utils import make_divisible, initialize_weights, check_anchor_order, check_version, fuse_conv_and_bn

def autopad(k, p=None):  # kernel, padding
    # Pad to 'same'
    if p is None:
        p = k // 2 if isinstance(k, int) else [x // 2 for x in k]  # auto-pad
    return p

class Conv(nn.Module):
    # Standard convolution
    def __init__(self, c1, c2, k=1, s=1, p=None, g=1, act=True):  # ch_in, ch_out, kernel, stride, padding, groups
        super().__init__()
        self.conv = nn.Conv2d(c1, c2, k, s, autopad(k, p), groups=g, bias=False)
        self.bn = nn.BatchNorm2d(c2)
        if isinstance(act, bool):
            self.act = nn.SiLU() if act is True else (act if isinstance(act, nn.Module) else nn.Identity())
        elif isinstance(act, str):
            if act == 'leaky':
                self.act = nn.LeakyReLU(0.1, inplace=True)
            elif act == 'relu':
                self.act = nn.ReLU(inplace=True)
            else:
                self.act = None
    def forward(self, x):
        return self.act(self.bn(self.conv(x)))

    def forward_fuse(self, x):
        return self.act(self.conv(x))


class DWConv(Conv):
    # Depth-wise convolution class
    def __init__(self, c1, c2, k=1, s=1, act=True):  # ch_in, ch_out, kernel, stride, padding, groups
        super().__init__(c1, c2, k, s, g=math.gcd(c1, c2), act=act)


class TransformerLayer(nn.Module):
    # Transformer layer https://arxiv.org/abs/2010.11929 (LayerNorm layers removed for better performance)
    def __init__(self, c, num_heads):
        super().__init__()
        self.q = nn.Linear(c, c, bias=False)
        self.k = nn.Linear(c, c, bias=False)
        self.v = nn.Linear(c, c, bias=False)
        self.ma = nn.MultiheadAttention(embed_dim=c, num_heads=num_heads)
        self.fc1 = nn.Linear(c, c, bias=False)
        self.fc2 = nn.Linear(c, c, bias=False)

    def forward(self, x):
        x = self.ma(self.q(x), self.k(x), self.v(x))[0] + x
        x = self.fc2(self.fc1(x)) + x
        return x


class TransformerBlock(nn.Module):
    # Vision Transformer https://arxiv.org/abs/2010.11929
    def __init__(self, c1, c2, num_heads, num_layers):
        super().__init__()
        self.conv = None
        if c1 != c2:
            self.conv = Conv(c1, c2)
        self.linear = nn.Linear(c2, c2)  # learnable position embedding
        self.tr = nn.Sequential(*(TransformerLayer(c2, num_heads) for _ in range(num_layers)))
        self.c2 = c2

    def forward(self, x):
        if self.conv is not None:
            x = self.conv(x)
        b, _, w, h = x.shape
        p = x.flatten(2).permute(2, 0, 1)
        return self.tr(p + self.linear(p)).permute(1, 2, 0).reshape(b, self.c2, w, h)


class Bottleneck(nn.Module):
    # Standard bottleneck
    def __init__(self, c1, c2, shortcut=True, g=1, e=0.5, act=True):  # ch_in, ch_out, shortcut, groups, expansion
        super().__init__()
        c_ = int(c2 * e)  # hidden channels
        self.cv1 = Conv(c1, c_, 1, 1, act=act)
        self.cv2 = Conv(c_, c2, 3, 1, g=g, act=act)
        self.add = shortcut and c1 == c2

    def forward(self, x):
        return x + self.cv2(self.cv1(x)) if self.add else self.cv2(self.cv1(x))


class BottleneckCSP(nn.Module):
    # CSP Bottleneck https://github.com/WongKinYiu/CrossStagePartialNetworks
    def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5):  # ch_in, ch_out, number, shortcut, groups, expansion
        super().__init__()
        c_ = int(c2 * e)  # hidden channels
        self.cv1 = Conv(c1, c_, 1, 1)
        self.cv2 = nn.Conv2d(c1, c_, 1, 1, bias=False)
        self.cv3 = nn.Conv2d(c_, c_, 1, 1, bias=False)
        self.cv4 = Conv(2 * c_, c2, 1, 1)
        self.bn = nn.BatchNorm2d(2 * c_)  # applied to cat(cv2, cv3)
        self.act = nn.SiLU()
        self.m = nn.Sequential(*(Bottleneck(c_, c_, shortcut, g, e=1.0) for _ in range(n)))

    def forward(self, x):
        y1 = self.cv3(self.m(self.cv1(x)))
        y2 = self.cv2(x)
        return self.cv4(self.act(self.bn(torch.cat((y1, y2), dim=1))))


class C3(nn.Module):
    # CSP Bottleneck with 3 convolutions
    def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5, act=True):  # ch_in, ch_out, number, shortcut, groups, expansion
        super().__init__()
        c_ = int(c2 * e)  # hidden channels
        self.cv1 = Conv(c1, c_, 1, 1, act=act)
        self.cv2 = Conv(c1, c_, 1, 1, act=act)
        self.cv3 = Conv(2 * c_, c2, 1, act=act)  # act=FReLU(c2)
        self.m = nn.Sequential(*(Bottleneck(c_, c_, shortcut, g, e=1.0, act=act) for _ in range(n)))
        # self.m = nn.Sequential(*[CrossConv(c_, c_, 3, 1, g, 1.0, shortcut) for _ in range(n)])

    def forward(self, x):
        return self.cv3(torch.cat((self.m(self.cv1(x)), self.cv2(x)), dim=1))


class C3TR(C3):
    # C3 module with TransformerBlock()
    def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5):
        super().__init__(c1, c2, n, shortcut, g, e)
        c_ = int(c2 * e)
        self.m = TransformerBlock(c_, c_, 4, n)


class C3SPP(C3):
    # C3 module with SPP()
    def __init__(self, c1, c2, k=(5, 9, 13), n=1, shortcut=True, g=1, e=0.5):
        super().__init__(c1, c2, n, shortcut, g, e)
        c_ = int(c2 * e)
        self.m = SPP(c_, c_, k)


class C3Ghost(C3):
    # C3 module with GhostBottleneck()
    def __init__(self, c1, c2, n=1, shortcut=True, g=1, e=0.5):
        super().__init__(c1, c2, n, shortcut, g, e)
        c_ = int(c2 * e)  # hidden channels
        self.m = nn.Sequential(*(GhostBottleneck(c_, c_) for _ in range(n)))


class SPP(nn.Module):
    # Spatial Pyramid Pooling (SPP) layer https://arxiv.org/abs/1406.4729
    def __init__(self, c1, c2, k=(5, 9, 13)):
        super().__init__()
        c_ = c1 // 2  # hidden channels
        self.cv1 = Conv(c1, c_, 1, 1)
        self.cv2 = Conv(c_ * (len(k) + 1), c2, 1, 1)
        self.m = nn.ModuleList([nn.MaxPool2d(kernel_size=x, stride=1, padding=x // 2) for x in k])

    def forward(self, x):
        x = self.cv1(x)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')  # suppress torch 1.9.0 max_pool2d() warning
            return self.cv2(torch.cat([x] + [m(x) for m in self.m], 1))


class SPPF(nn.Module):
    # Spatial Pyramid Pooling - Fast (SPPF) layer for YOLOv5 by Glenn Jocher
    def __init__(self, c1, c2, k=5):  # equivalent to SPP(k=(5, 9, 13))
        super().__init__()
        c_ = c1 // 2  # hidden channels
        self.cv1 = Conv(c1, c_, 1, 1)
        self.cv2 = Conv(c_ * 4, c2, 1, 1)
        self.m = nn.MaxPool2d(kernel_size=k, stride=1, padding=k // 2)

    def forward(self, x):
        x = self.cv1(x)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')  # suppress torch 1.9.0 max_pool2d() warning
            y1 = self.m(x)
            y2 = self.m(y1)
            return self.cv2(torch.cat([x, y1, y2, self.m(y2)], 1))


class Focus(nn.Module):
    # Focus wh information into c-space
    def __init__(self, c1, c2, k=1, s=1, p=None, g=1, act=True):  # ch_in, ch_out, kernel, stride, padding, groups
        super().__init__()
        self.conv = Conv(c1 * 4, c2, k, s, p, g, act)
        # self.contract = Contract(gain=2)

    def forward(self, x):  # x(b,c,w,h) -> y(b,4c,w/2,h/2)
        return self.conv(torch.cat([x[..., ::2, ::2], x[..., 1::2, ::2], x[..., ::2, 1::2], x[..., 1::2, 1::2]], 1))
        # return self.conv(self.contract(x))


class GhostConv(nn.Module):
    # Ghost Convolution https://github.com/huawei-noah/ghostnet
    def __init__(self, c1, c2, k=1, s=1, g=1, act=True):  # ch_in, ch_out, kernel, stride, groups
        super().__init__()
        c_ = c2 // 2  # hidden channels
        self.cv1 = Conv(c1, c_, k, s, None, g, act)
        self.cv2 = Conv(c_, c_, 5, 1, None, c_, act)

    def forward(self, x):
        y = self.cv1(x)
        return torch.cat([y, self.cv2(y)], 1)


class GhostBottleneck(nn.Module):
    # Ghost Bottleneck https://github.com/huawei-noah/ghostnet
    def __init__(self, c1, c2, k=3, s=1):  # ch_in, ch_out, kernel, stride
        super().__init__()
        c_ = c2 // 2
        self.conv = nn.Sequential(GhostConv(c1, c_, 1, 1),  # pw
                                  DWConv(c_, c_, k, s, act=False) if s == 2 else nn.Identity(),  # dw
                                  GhostConv(c_, c2, 1, 1, act=False))  # pw-linear
        self.shortcut = nn.Sequential(DWConv(c1, c1, k, s, act=False),
                                      Conv(c1, c2, 1, 1, act=False)) if s == 2 else nn.Identity()

    def forward(self, x):
        return self.conv(x) + self.shortcut(x)


class Contract(nn.Module):
    # Contract width-height into channels, i.e. x(1,64,80,80) to x(1,256,40,40)
    def __init__(self, gain=2):
        super().__init__()
        self.gain = gain

    def forward(self, x):
        b, c, h, w = x.size()  # assert (h / s == 0) and (W / s == 0), 'Indivisible gain'
        s = self.gain
        x = x.view(b, c, h // s, s, w // s, s)  # x(1,64,40,2,40,2)
        x = x.permute(0, 3, 5, 1, 2, 4).contiguous()  # x(1,2,2,64,40,40)
        return x.view(b, c * s * s, h // s, w // s)  # x(1,256,40,40)


class Expand(nn.Module):
    # Expand channels into width-height, i.e. x(1,64,80,80) to x(1,16,160,160)
    def __init__(self, gain=2):
        super().__init__()
        self.gain = gain

    def forward(self, x):
        b, c, h, w = x.size()  # assert C / s ** 2 == 0, 'Indivisible gain'
        s = self.gain
        x = x.view(b, s, s, c // s ** 2, h, w)  # x(1,2,2,16,80,80)
        x = x.permute(0, 3, 4, 1, 5, 2).contiguous()  # x(1,16,80,2,80,2)
        return x.view(b, c // s ** 2, h * s, w * s)  # x(1,16,160,160)


class Concat(nn.Module):
    # Concatenate a list of tensors along dimension
    def __init__(self, dimension=1):
        super().__init__()
        self.d = dimension

    def forward(self, x):
        return torch.cat(x, self.d)


class Classify(nn.Module):
    # Classification head, i.e. x(b,c1,20,20) to x(b,c2)
    def __init__(self, c1, c2, k=1, s=1, p=None, g=1):  # ch_in, ch_out, kernel, stride, padding, groups
        super().__init__()
        self.aap = nn.AdaptiveAvgPool2d(1)  # to x(b,c1,1,1)
        self.conv = nn.Conv2d(c1, c2, k, s, autopad(k, p), groups=g)  # to x(b,c2,1,1)
        self.flat = nn.Flatten()

    def forward(self, x):
        z = torch.cat([self.aap(y) for y in (x if isinstance(x, list) else [x])], 1)  # cat if list
        return self.flat(self.conv(z))  # flatten to x(b,c2)
```

#### `yolo.py`

```py
from operator import mod
from cv2 import imshow
from src.utils.yolov5_utils import scale_img  # 修复导入路径
from copy import deepcopy
from .common import *

class Detect(nn.Module):
    stride = None  # strides computed during build
    onnx_dynamic = False  # ONNX export parameter

    def __init__(self, nc=80, anchors=(), ch=(), inplace=True):  # detection layer
        super().__init__()
        self.nc = nc  # number of classes
        self.no = nc + 5  # number of outputs per anchor
        self.nl = len(anchors)  # number of detection layers
        self.na = len(anchors[0]) // 2  # number of anchors
        self.grid = [torch.zeros(1)] * self.nl  # init grid
        self.anchor_grid = [torch.zeros(1)] * self.nl  # init anchor grid
        self.register_buffer('anchors', torch.tensor(anchors).float().view(self.nl, -1, 2))  # shape(nl,na,2)
        self.m = nn.ModuleList(nn.Conv2d(x, self.no * self.na, 1) for x in ch)  # output conv
        self.inplace = inplace  # use in-place ops (e.g. slice assignment)

    def forward(self, x):
        z = []  # inference output
        for i in range(self.nl):
            x[i] = self.m[i](x[i])  # conv
            bs, _, ny, nx = x[i].shape  # x(bs,255,20,20) to x(bs,3,20,20,85)
            x[i] = x[i].view(bs, self.na, self.no, ny, nx).permute(0, 1, 3, 4, 2).contiguous()

            if not self.training:  # inference
                if self.onnx_dynamic or self.grid[i].shape[2:4] != x[i].shape[2:4]:
                    self.grid[i], self.anchor_grid[i] = self._make_grid(nx, ny, i)

                y = x[i].sigmoid()
                if self.inplace:
                    y[..., 0:2] = (y[..., 0:2] * 2 - 0.5 + self.grid[i]) * self.stride[i]  # xy
                    y[..., 2:4] = (y[..., 2:4] * 2) ** 2 * self.anchor_grid[i]  # wh
                else:  # for YOLOv5 on AWS Inferentia https://github.com/ultralytics/yolov5/pull/2953
                    xy = (y[..., 0:2] * 2 - 0.5 + self.grid[i]) * self.stride[i]  # xy
                    wh = (y[..., 2:4] * 2) ** 2 * self.anchor_grid[i]  # wh
                    y = torch.cat((xy, wh, y[..., 4:]), -1)
                z.append(y.view(bs, -1, self.no))

        return x if self.training else (torch.cat(z, 1), x)

    def _make_grid(self, nx=20, ny=20, i=0):
        d = self.anchors[i].device
        if check_version(torch.__version__, '1.10.0'):  # torch>=1.10.0 meshgrid workaround for torch>=0.7 compatibility
            yv, xv = torch.meshgrid([torch.arange(ny, device=d), torch.arange(nx, device=d)], indexing='ij')
        else:
            yv, xv = torch.meshgrid([torch.arange(ny, device=d), torch.arange(nx, device=d)])
        grid = torch.stack((xv, yv), 2).expand((1, self.na, ny, nx, 2)).float()
        anchor_grid = (self.anchors[i].clone() * self.stride[i]) \
            .view((1, self.na, 1, 1, 2)).expand((1, self.na, ny, nx, 2)).float()
        return grid, anchor_grid

class Model(nn.Module):
    def __init__(self, cfg='yolov5s.yaml', ch=3, nc=None, anchors=None):  # model, input channels, number of classes
        super().__init__()
        self.out_indices = None
        if isinstance(cfg, dict):
            self.yaml = cfg  # model dict
        else:  # is *.yaml
            import yaml  # for torch hub
            self.yaml_file = Path(cfg).name
            with open(cfg, encoding='ascii', errors='ignore') as f:
                self.yaml = yaml.safe_load(f)  # model dict

        # Define model
        ch = self.yaml['ch'] = self.yaml.get('ch', ch)  # input channels
        if nc and nc != self.yaml['nc']:
            # LOGGER.info(f"Overriding model.yaml nc={self.yaml['nc']} with nc={nc}")
            self.yaml['nc'] = nc  # override yaml value
        if anchors:
            # LOGGER.info(f'Overriding model.yaml anchors with anchors={anchors}')
            self.yaml['anchors'] = round(anchors)  # override yaml value
        self.model, self.save = parse_model(deepcopy(self.yaml), ch=[ch])  # model, savelist
        self.names = [str(i) for i in range(self.yaml['nc'])]  # default names
        self.inplace = self.yaml.get('inplace', True)

        # Build strides, anchors
        m = self.model[-1]  # Detect()
        # with torch.no_grad():
        if isinstance(m, Detect):
            s = 256  # 2x min stride
            m.inplace = self.inplace
            m.stride = torch.tensor([s / x.shape[-2] for x in self.forward(torch.zeros(1, ch, s, s))])  # forward
            m.anchors /= m.stride.view(-1, 1, 1)
            check_anchor_order(m)
            self.stride = m.stride
            self._initialize_biases()  # only run once

        # Init weights, biases
        initialize_weights(self)

    def forward(self, x, augment=False, profile=False, visualize=False, detect=False):
        if augment:
            return self._forward_augment(x)  # augmented inference, None
        return self._forward_once(x, profile, visualize, detect=detect)  # single-scale inference, train

    def _forward_augment(self, x):
        img_size = x.shape[-2:]  # height, width
        s = [1, 0.83, 0.67]  # scales
        f = [None, 3, None]  # flips (2-ud, 3-lr)
        y = []  # outputs
        for si, fi in zip(s, f):
            xi = scale_img(x.flip(fi) if fi else x, si, gs=int(self.stride.max()))
            yi = self._forward_once(xi)[0]  # forward
            # cv2.imwrite(f'img_{si}.jpg', 255 * xi[0].cpu().numpy().transpose((1, 2, 0))[:, :, ::-1])  # save
            yi = self._descale_pred(yi, fi, si, img_size)
            y.append(yi)
        y = self._clip_augmented(y)  # clip augmented tails
        return torch.cat(y, 1), None  # augmented inference, train

    def _forward_once(self, x, profile=False, visualize=False, detect=False):
        y, dt = [], []  # outputs
        z = []
        for ii, m in enumerate(self.model):
            if m.f != -1:  # if not from previous layer
                x = y[m.f] if isinstance(m.f, int) else [x if j == -1 else y[j] for j in m.f]  # from earlier layers
            if profile:
                self._profile_one_layer(m, x, dt)
            x = m(x)  # run
            y.append(x if m.i in self.save else None)  # save output
            if self.out_indices is not None:
                if m.i in self.out_indices:
                    z.append(x)
        if self.out_indices is not None:
            if detect:
                return x, z
            else:
                return z
        else:
            return x

    def _descale_pred(self, p, flips, scale, img_size):
        # de-scale predictions following augmented inference (inverse operation)
        if self.inplace:
            p[..., :4] /= scale  # de-scale
            if flips == 2:
                p[..., 1] = img_size[0] - p[..., 1]  # de-flip ud
            elif flips == 3:
                p[..., 0] = img_size[1] - p[..., 0]  # de-flip lr
        else:
            x, y, wh = p[..., 0:1] / scale, p[..., 1:2] / scale, p[..., 2:4] / scale  # de-scale
            if flips == 2:
                y = img_size[0] - y  # de-flip ud
            elif flips == 3:
                x = img_size[1] - x  # de-flip lr
            p = torch.cat((x, y, wh, p[..., 4:]), -1)
        return p

    def _clip_augmented(self, y):
        # Clip YOLOv5 augmented inference tails
        nl = self.model[-1].nl  # number of detection layers (P3-P5)
        g = sum(4 ** x for x in range(nl))  # grid points
        e = 1  # exclude layer count
        i = (y[0].shape[1] // g) * sum(4 ** x for x in range(e))  # indices
        y[0] = y[0][:, :-i]  # large
        i = (y[-1].shape[1] // g) * sum(4 ** (nl - 1 - x) for x in range(e))  # indices
        y[-1] = y[-1][:, i:]  # small
        return y

    def _profile_one_layer(self, m, x, dt):
        c = isinstance(m, Detect)  # is final layer, copy input as inplace fix
        for _ in range(10):
            m(x.copy() if c else x)


    def _initialize_biases(self, cf=None):  # initialize biases into Detect(), cf is class frequency
        # https://arxiv.org/abs/1708.02002 section 3.3
        # cf = torch.bincount(torch.tensor(np.concatenate(dataset.labels, 0)[:, 0]).long(), minlength=nc) + 1.
        m = self.model[-1]  # Detect() module
        for mi, s in zip(m.m, m.stride):  # from
            b = mi.bias.view(m.na, -1)  # conv.bias(255) to (3,85)
            b.data[:, 4] += math.log(8 / (640 / s) ** 2)  # obj (8 objects per 640 image)
            b.data[:, 5:] += math.log(0.6 / (m.nc - 0.999999)) if cf is None else torch.log(cf / cf.sum())  # cls
            mi.bias = torch.nn.Parameter(b.view(-1), requires_grad=True)

    def _print_biases(self):
        m = self.model[-1]  # Detect() module
        for mi in m.m:  # from
            b = mi.bias.detach().view(m.na, -1).T  # conv.bias(255) to (3,85)

    def fuse(self):  # fuse model Conv2d() + BatchNorm2d() layers
        for m in self.model.modules():
            if isinstance(m, (Conv, DWConv)) and hasattr(m, 'bn'):
                m.conv = fuse_conv_and_bn(m.conv, m.bn)  # update conv
                delattr(m, 'bn')  # remove batchnorm
                m.forward = m.forward_fuse  # update forward
        # self.info()
        return self

    # def info(self, verbose=False, img_size=640):  # print model information
    #     model_info(self, verbose, img_size)

    def _apply(self, fn):
        # Apply to(), cpu(), cuda(), half() to model tensors that are not parameters or registered buffers
        self = super()._apply(fn)
        m = self.model[-1]  # Detect()
        if isinstance(m, Detect):
            m.stride = fn(m.stride)
            m.grid = list(map(fn, m.grid))
            if isinstance(m.anchor_grid, list):
                m.anchor_grid = list(map(fn, m.anchor_grid))
        return self

def parse_model(d, ch):  # model_dict, input_channels(3)
    # LOGGER.info(f"\n{'':>3}{'from':>18}{'n':>3}{'params':>10}  {'module':<40}{'arguments':<30}")
    anchors, nc, gd, gw = d['anchors'], d['nc'], d['depth_multiple'], d['width_multiple']
    na = (len(anchors[0]) // 2) if isinstance(anchors, list) else anchors  # number of anchors
    no = na * (nc + 5)  # number of outputs = anchors * (classes + 5)

    layers, save, c2 = [], [], ch[-1]  # layers, savelist, ch out
    for i, (f, n, m, args) in enumerate(d['backbone'] + d['head']):  # from, number, module, args
        m = eval(m) if isinstance(m, str) else m  # eval strings
        for j, a in enumerate(args):
            try:
                args[j] = eval(a) if isinstance(a, str) else a  # eval strings
            except NameError:
                pass

        n = n_ = max(round(n * gd), 1) if n > 1 else n  # depth gain
        if m in [Conv, GhostConv, Bottleneck, GhostBottleneck, SPP, SPPF, DWConv, Focus,
                 BottleneckCSP, C3, C3TR, C3SPP, C3Ghost]:
            c1, c2 = ch[f], args[0]
            if c2 != no:  # if not output
                c2 = make_divisible(c2 * gw, 8)

            args = [c1, c2, *args[1:]]
            if m in [BottleneckCSP, C3, C3TR, C3Ghost]:
                args.insert(2, n)  # number of repeats
                n = 1
        elif m is nn.BatchNorm2d:
            args = [ch[f]]
        elif m is Concat:
            c2 = sum(ch[x] for x in f)
        elif m is Detect:
            args.append([ch[x] for x in f])
            if isinstance(args[1], int):  # number of anchors
                args[1] = [list(range(args[1] * 2))] * len(f)
        elif m is Contract:
            c2 = ch[f] * args[0] ** 2
        elif m is Expand:
            c2 = ch[f] // args[0] ** 2
        else:
            c2 = ch[f]

        m_ = nn.Sequential(*(m(*args) for _ in range(n))) if n > 1 else m(*args)  # module
        t = str(m)[8:-2].replace('__main__.', '')  # module type
        np = sum(x.numel() for x in m_.parameters())  # number params
        m_.i, m_.f, m_.type, m_.np = i, f, t, np  # attach index, 'from' index, type, number params
        # LOGGER.info(f'{i:>3}{str(f):>18}{n_:>3}{np:10.0f}  {t:<40}{str(args):<30}')  # print
        save.extend(x % i for x in ([f] if isinstance(f, int) else f) if x != -1)  # append to savelist
        layers.append(m_)
        if i == 0:
            ch = []
        ch.append(c2)
    return nn.Sequential(*layers), sorted(save)

def load_yolov5(weights, map_location='cuda', fuse=True, inplace=True, out_indices=[1, 3, 5, 7, 9]):
    if isinstance(weights, str):
        ckpt = torch.load(weights, map_location=map_location)  # load
    else:
        ckpt = weights
    
    if fuse:
        model = ckpt['model'].float().fuse().eval()  # FP32 model
    else:
        model = ckpt['model'].float().eval()  # without layer fuse

    # Compatibility updates
    for m in model.modules():
        if type(m) in [nn.Hardswish, nn.LeakyReLU, nn.ReLU, nn.ReLU6, nn.SiLU, Detect, Model]:
            m.inplace = inplace  # pytorch 1.7.0 compatibility
            if type(m) is Detect:
                if not isinstance(m.anchor_grid, list):  # new Detect Layer compatibility
                    delattr(m, 'anchor_grid')
                    setattr(m, 'anchor_grid', [torch.zeros(1)] * m.nl)
        elif type(m) is Conv:
            m._non_persistent_buffers_set = set()  # pytorch 1.6.0 compatibility
    model.out_indices = out_indices
    return model

@torch.no_grad()
def load_yolov5_ckpt(weights, map_location='cpu', fuse=True, inplace=True, out_indices=[1, 3, 5, 7, 9]):
    if isinstance(weights, str):
        ckpt = torch.load(weights, map_location=map_location)  # load
    else:
        ckpt = weights
    
    model = Model(ckpt['cfg'])
    model.load_state_dict(ckpt['weights'], strict=True)
    
    if fuse:
        model = model.float().fuse().eval()  # FP32 model
    else:
        model = model.float().eval()  # without layer fuse

    # Compatibility updates
    for m in model.modules():
        if type(m) in [nn.Hardswish, nn.LeakyReLU, nn.ReLU, nn.ReLU6, nn.SiLU, Detect, Model]:
            m.inplace = inplace  # pytorch 1.7.0 compatibility
            if type(m) is Detect:
                if not isinstance(m.anchor_grid, list):  # new Detect Layer compatibility
                    delattr(m, 'anchor_grid')
                    setattr(m, 'anchor_grid', [torch.zeros(1)] * m.nl)
        elif type(m) is Conv:
            m._non_persistent_buffers_set = set()  # pytorch 1.6.0 compatibility
    model.out_indices = out_indices
    return model
```

#### `__init__.py`

```py

```

### `__init__.py`

```py

```

## `ui`

### `main_window.py`

```py
"""
GUI应用主类 - 分离版本（检测和OCR独立）- 适配新的项目结构
"""

import sys
import json
from pathlib import Path
from typing import Optional, List

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
except ImportError:
    raise ImportError("PyQt5未安装，请运行：pip install PyQt5")

from src.core.detector import ComicTextDetector, DetectionResults, ProjectResults
from src.ui.widgets.image_viewer import ImageViewer
from src.ui.widgets.parameter_panel import ParameterPanel
from config.config import Config


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


class ComicTextDetectorGUI(QMainWindow):
    """漫画文本检测器GUI主窗口 - 分离版本"""
    
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
        
        # 工作线程
        self.detection_worker: Optional[DetectionWorker] = None
        self.ocr_worker: Optional[OCRWorker] = None
        self.batch_worker: Optional[BatchProcessWorker] = None
        
        # 初始化UI
        self.init_ui()
        self.init_detector()
        self.load_settings()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("漫画文本检测器 v1.0 (项目结构优化版)")
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
        self.parameter_panel.parameters_changed.connect(self.on_parameters_changed)
        main_layout.addWidget(self.parameter_panel, stretch=0)
        
        # 右侧面板 - 图像显示和控制
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 控制按钮区域
        control_widget = QWidget()
        control_layout = QHBoxLayout(control_widget)
        control_layout.setContentsMargins(5, 5, 5, 5)
        
        # 检测按钮
        self.detect_button = QPushButton("🔍 开始检测")
        self.detect_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.detect_button.clicked.connect(self.start_detection)
        self.detect_button.setEnabled(False)
        control_layout.addWidget(self.detect_button)
        
        # OCR按钮
        self.ocr_button = QPushButton("📝 OCR识别")
        self.ocr_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.ocr_button.clicked.connect(self.start_ocr)
        self.ocr_button.setEnabled(False)
        control_layout.addWidget(self.ocr_button)
        
        # 保存按钮
        self.save_button = QPushButton("💾 保存结果")
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.save_button.clicked.connect(self.save_results)
        self.save_button.setEnabled(False)
        control_layout.addWidget(self.save_button)
        
        control_layout.addStretch()
        right_layout.addWidget(control_widget)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)
        
        # 图像查看器
        self.image_viewer = ImageViewer()
        right_layout.addWidget(self.image_viewer, stretch=1)
        
        # 导航和状态栏
        nav_status_widget = QWidget()
        nav_status_layout = QHBoxLayout(nav_status_widget)
        nav_status_layout.setContentsMargins(0, 5, 0, 5)

        # 导航按钮
        self.prev_button = QPushButton("⬅️ 上一张")
        self.prev_button.clicked.connect(self.prev_image)
        self.prev_button.setEnabled(False)
        nav_status_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("下一张 ➡️")
        self.next_button.clicked.connect(self.next_image)
        self.next_button.setEnabled(False)
        nav_status_layout.addWidget(self.next_button)
        
        nav_status_layout.addStretch()
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #666666; font-size: 12px;")
        nav_status_layout.addWidget(self.status_label)

        right_layout.addWidget(nav_status_widget)
        
        main_layout.addWidget(right_widget, stretch=1)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        # 打开项目文件夹
        open_action = QAction('打开项目文件夹(&O)', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_project_folder)
        file_menu.addAction(open_action)
        
        # 最近项目菜单
        self.recent_menu = file_menu.addMenu('最近项目(&R)')
        self.update_recent_menu()
        
        file_menu.addSeparator()
        
        # 批量处理
        batch_action = QAction('批量处理（仅检测）(&B)', self)
        batch_action.triggered.connect(self.start_batch_detection)
        file_menu.addAction(batch_action)
        
        # 批量处理（包含OCR）
        batch_ocr_action = QAction('批量处理（含OCR）(&M)', self)
        batch_ocr_action.triggered.connect(self.start_batch_with_ocr)
        file_menu.addAction(batch_ocr_action)
        
        # 保存结果
        save_action = QAction('保存结果(&S)', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_results)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction('退出(&X)', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 视图菜单
        view_menu = menubar.addMenu('视图(&V)')
        
        # 显示检测区域
        self.toggle_regions_action = QAction('显示检测区域(&R)', self)
        self.toggle_regions_action.setShortcut('Ctrl+R')
        self.toggle_regions_action.setCheckable(True)
        self.toggle_regions_action.setChecked(True)
        self.toggle_regions_action.triggered.connect(self.toggle_detection_regions)
        view_menu.addAction(self.toggle_regions_action)

        # 显示文本行
        self.toggle_lines_action = QAction('显示文本行(&L)', self)
        self.toggle_lines_action.setShortcut('Ctrl+L')
        self.toggle_lines_action.setCheckable(True)
        self.toggle_lines_action.setChecked(True)
        self.toggle_lines_action.triggered.connect(self.toggle_text_lines)
        view_menu.addAction(self.toggle_lines_action)

        # 显示文本块
        self.toggle_blocks_action = QAction('显示文本块(&B)', self)
        self.toggle_blocks_action.setShortcut('Ctrl+Shift+B')
        self.toggle_blocks_action.setCheckable(True)
        self.toggle_blocks_action.setChecked(True)
        self.toggle_blocks_action.triggered.connect(self.toggle_text_blocks)
        view_menu.addAction(self.toggle_blocks_action)

        # 处理菜单
        process_menu = menubar.addMenu('处理(&P)')
        
        # 开始检测
        detect_action = QAction('开始检测(&D)', self)
        detect_action.setShortcut('F5')
        detect_action.triggered.connect(self.start_detection)
        process_menu.addAction(detect_action)
        
        # OCR识别
        ocr_action = QAction('OCR识别(&O)', self)
        ocr_action.setShortcut('F6')
        ocr_action.triggered.connect(self.start_ocr)
        process_menu.addAction(ocr_action)

        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        
        about_action = QAction('关于(&A)', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def open_project_folder(self):
        """打开项目文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "选择项目文件夹", 
            str(self.config.examples_dir)
        )
        
        if folder_path:
            self.load_project_folder(folder_path)

    def load_project_folder(self, folder_path: str):
        """加载项目文件夹"""
        try:
            from src.utils.io_utils import find_all_imgs
            
            # 检查文件夹中的图片
            image_files = find_all_imgs(folder_path, abs_path=True)
            if not image_files:
                QMessageBox.warning(self, "警告", f"文件夹中没有找到图片文件: {folder_path}")
                return
            
            # 保存当前项目信息
            self.current_project_folder = folder_path
            self.current_image_files = image_files
            self.current_image_index = 0
            
            # 显示第一张图片
            self.image_viewer.load_image(image_files[0])
            self.current_image_path = image_files[0]
            
            # 更新按钮状态
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(len(image_files) > 1)
            self.detect_button.setEnabled(True)
            
            # 清空之前的结果
            self.current_results = None
            self.ocr_button.setEnabled(False)
            self.save_button.setEnabled(False)
            
            # 更新最近文件夹
            self.add_recent_folder(folder_path)
            
            # 更新状态
            self.statusBar().showMessage(f"项目已加载: {folder_path} ({len(image_files)} 个文件)")
            self.status_label.setText(f"已加载 {len(image_files)} 个文件")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载项目文件夹: {e}")

    def prev_image(self):
        """切换到上一张图片"""
        if self.current_image_files and self.current_image_index > 0:
            self.current_image_index -= 1
            self.load_current_image()

    def next_image(self):
        """切换到下一张图片"""
        if self.current_image_files and self.current_image_index < len(self.current_image_files) - 1:
            self.current_image_index += 1
            self.load_current_image()

    def load_current_image(self):
        """加载当前索引的图片"""
        if not self.current_image_files:
            return
            
        current_image = self.current_image_files[self.current_image_index]
        self.image_viewer.load_image(current_image)
        self.current_image_path = current_image
        
        # 清空之前的结果
        self.current_results = None
        self.ocr_button.setEnabled(False)
        self.save_button.setEnabled(False)
        
        # 更新按钮状态
        self.prev_button.setEnabled(self.current_image_index > 0)
        self.next_button.setEnabled(self.current_image_index < len(self.current_image_files) - 1)
        
        # 更新状态显示
        image_name = Path(current_image).name
        total_count = len(self.current_image_files)
        self.statusBar().showMessage(f"图片: {image_name} ({self.current_image_index + 1}/{total_count})")
        self.status_label.setText(f"图片 {self.current_image_index + 1}/{total_count}: {image_name}")

    def start_detection(self):
        """开始文字检测"""
        if not self.current_image_path or not self.detector:
            QMessageBox.information(self, "提示", "请先选择图片并确保检测器已加载")
            return
        
        # 更新检测器参数
        params = self.parameter_panel.get_parameters()
        self.detector.update_parameters(**params)
        
        # 禁用按钮
        self.detect_button.setEnabled(False)
        self.ocr_button.setEnabled(False)
        self.save_button.setEnabled(False)
        
        # 显示进度
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.status_label.setText("正在检测...")
        
        # 启动检测线程
        self.detection_worker = DetectionWorker(self.detector, self.current_image_path)
        self.detection_worker.finished.connect(self.on_detection_finished)
        self.detection_worker.error.connect(self.on_detection_error)
        self.detection_worker.progress.connect(self.on_detection_progress)
        self.detection_worker.start()

    def start_ocr(self):
        """开始OCR识别"""
        if not self.current_results or not self.detector:
            QMessageBox.information(self, "提示", "请先完成文字检测")
            return
        
        if self.current_results.has_ocr_results:
            reply = QMessageBox.question(
                self, "确认", "该图片已有OCR结果，是否重新识别？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # 禁用按钮
        self.detect_button.setEnabled(False)
        self.ocr_button.setEnabled(False)
        self.save_button.setEnabled(False)
        
        # 显示进度
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("正在OCR识别...")
        
        # 启动OCR线程
        self.ocr_worker = OCRWorker(self.detector, self.current_results)
        self.ocr_worker.finished.connect(self.on_ocr_finished)
        self.ocr_worker.error.connect(self.on_ocr_error)
        self.ocr_worker.progress.connect(self.on_ocr_progress)
        self.ocr_worker.start()

    def on_detection_progress(self, message: str):
        """检测进度更新"""
        self.status_label.setText(message)

    def on_detection_finished(self, results: DetectionResults):
        """检测完成回调"""
        self.current_results = results
        
        # 显示结果图片
        self.image_viewer.set_result_image(results.result_image)
        self.image_viewer.set_detection_regions(results.text_regions)
        
        # 更新状态信息
        region_count = len(results.text_regions)
        detection_time = results.detection_time
        self.statusBar().showMessage(f"检测完成: 找到 {region_count} 个文字区域, 耗时 {detection_time:.2f}s")
        self.status_label.setText(f"检测完成: {region_count} 个区域")
        
        # 更新参数面板统计信息
        self.parameter_panel.update_stats(results.to_dict())
        
        # 恢复按钮状态
        self.detect_button.setEnabled(True)
        self.ocr_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.progress_bar.setVisible(False)

    def on_detection_error(self, error_msg: str):
        """检测错误回调"""
        self.statusBar().showMessage("检测失败")
        self.status_label.setText("检测失败")
        QMessageBox.critical(self, "检测失败", f"检测过程中发生错误: {error_msg}")
        
        # 恢复按钮状态
        self.detect_button.setEnabled(True)
        self.progress_bar.setVisible(False)

    def on_ocr_progress(self, message: str):
        """OCR进度更新"""
        self.status_label.setText(message)

    def on_ocr_finished(self, results: DetectionResults):
        """OCR完成回调"""
        self.current_results = results
        
        # 更新显示（现在包含OCR文本）
        self.image_viewer.set_result_image(results.result_image)
        self.image_viewer.set_detection_regions(results.text_regions)
        
        # 更新状态信息
        ocr_time = results.ocr_time
        total_text_length = sum(len(text) for text in results.ocr_results.values())
        self.statusBar().showMessage(f"OCR完成: 识别了 {total_text_length} 个字符, 耗时 {ocr_time:.2f}s")
        self.status_label.setText(f"OCR完成: {total_text_length} 个字符")
        
        # 更新参数面板统计信息
        self.parameter_panel.update_stats(results.to_dict())
        
        # 恢复按钮状态
        self.detect_button.setEnabled(True)
        self.ocr_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.progress_bar.setVisible(False)

    def on_ocr_error(self, error_msg: str):
        """OCR错误回调"""
        self.statusBar().showMessage("OCR识别失败")
        self.status_label.setText("OCR失败")
        QMessageBox.critical(self, "OCR失败", f"OCR过程中发生错误: {error_msg}")
        
        # 恢复按钮状态
        self.detect_button.setEnabled(True)
        self.ocr_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def save_results(self):
        """保存检测结果"""
        if not self.current_results:
            QMessageBox.information(self, "提示", "没有检测结果可保存")
            return
        
        # 选择保存目录
        output_dir = QFileDialog.getExistingDirectory(
            self, "选择保存目录", str(self.config.results_dir)
        )
        
        if output_dir:
            try:
                saved_dir = self.detector.save_results(self.current_results, output_dir)
                
                # 构建保存信息
                save_info = f"结果已保存到: {saved_dir}\n\n包含内容:\n"
                save_info += f"- 检测结果图片\n"
                save_info += f"- 文字掩码\n" 
                save_info += f"- JSON格式结果\n"
                if self.current_results.has_ocr_results:
                    save_info += f"- OCR识别结果"
                
                QMessageBox.information(self, "成功", save_info)
                self.statusBar().showMessage(f"结果已保存: {saved_dir}")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def toggle_text_lines(self):
        """切换文本行显示"""
        self.image_viewer.toggle_lines()
        if self.image_viewer.show_lines:
            self.toggle_lines_action.setText('隐藏文本行(&L)')
        else:
            self.toggle_lines_action.setText('显示文本行(&L)')

    def toggle_text_blocks(self):
        """切换文本块显示"""
        self.image_viewer.toggle_blocks()
        if self.image_viewer.show_blocks:
            self.toggle_blocks_action.setText('隐藏文本块(&B)')
        else:
            self.toggle_blocks_action.setText('显示文本块(&B)')

    def toggle_detection_regions(self):
        """切换检测区域显示"""
        self.image_viewer.toggle_regions()
        if self.image_viewer.show_regions:
            self.toggle_regions_action.setText('隐藏检测区域(&R)')
        else:
            self.toggle_regions_action.setText('显示检测区域(&R)')
    
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
    
    def add_recent_folder(self, folder_path: str):
        """添加到最近项目文件夹"""
        if folder_path in self.recent_files:
            self.recent_files.remove(folder_path)
        
        self.recent_files.insert(0, folder_path)
        
        # 限制最近文件数量
        max_recent = self.config.gui_params.get('recent_files_count', 10)
        if len(self.recent_files) > max_recent:
            self.recent_files = self.recent_files[:max_recent]
        
        self.update_recent_menu()
    
    def update_recent_menu(self):
        """更新最近项目文件夹菜单"""
        self.recent_menu.clear()
        
        for i, folder_path in enumerate(self.recent_files):
            if Path(folder_path).exists():
                # 显示文件夹名 + 上级目录，避免路径过长
                folder_name = Path(folder_path).name
                parent_name = Path(folder_path).parent.name
                display_name = f"{parent_name}/{folder_name}" if parent_name != folder_name else folder_name
                
                action = QAction(f"{i+1}. {display_name}", self)
                # 设置工具提示显示完整路径
                action.setToolTip(folder_path)
                action.triggered.connect(lambda checked, path=folder_path: self.load_project_folder(path))
                self.recent_menu.addAction(action)
        
        if not self.recent_files:
            action = QAction("(空)", self)
            action.setEnabled(False)
            self.recent_menu.addAction(action)

    def start_batch_detection(self):
        """开始批量检测（不含OCR）"""
        self._start_batch_processing(include_ocr=False)

    def start_batch_with_ocr(self):
        """开始批量处理（含OCR）"""
        self._start_batch_processing(include_ocr=True)

    def _start_batch_processing(self, include_ocr: bool = True):
        """开始批量处理 - 使用新的项目结构"""
        if not self.current_image_files or not self.detector:
            QMessageBox.information(self, "提示", "请先选择项目文件夹并确保检测器已加载")
            return
        
        # 获取项目名称
        if self.current_project_folder:
            default_project_name = Path(self.current_project_folder).name
        else:
            default_project_name = f"project_{int(time.time())}"
        
        project_name, ok = QInputDialog.getText(
            self, '项目名称', 
            f'请输入项目名称（用于创建输出文件夹）:',
            text=default_project_name
        )
        
        if not ok or not project_name.strip():
            return
        
        project_name = project_name.strip()
        
        # 选择输出目录
        output_dir = QFileDialog.getExistingDirectory(
            self, "选择输出目录", str(self.config.results_dir)
        )
        
        if not output_dir:
            return
        
        # 更新检测器参数
        params = self.parameter_panel.get_parameters()
        self.detector.update_parameters(**params)
        
        # 显示进度
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self.current_image_files))
        
        # 禁用控件
        self.detect_button.setEnabled(False)
        self.ocr_button.setEnabled(False)
        self.save_button.setEnabled(False)
        
        operation_name = "批量处理（含OCR）" if include_ocr else "批量检测"
        self.status_label.setText(f"正在{operation_name}...")
        
        # 启动批量处理线程
        self.batch_worker = BatchProcessWorker(
            self.detector, 
            self.current_image_files, 
            project_name,
            output_dir,
            include_ocr=include_ocr
        )
        self.batch_worker.finished.connect(self.on_batch_finished)
        self.batch_worker.error.connect(self.on_batch_error)
        self.batch_worker.progress.connect(self.on_batch_progress)
        self.batch_worker.start()

    def on_batch_progress(self, current, total, message):
        """批量处理进度回调"""
        self.progress_bar.setValue(current)
        self.statusBar().showMessage(f"批量处理进度: {current}/{total} - {message}")
        self.status_label.setText(f"处理中: {current}/{total}")

    def on_batch_finished(self, project_results: ProjectResults):
        """批量处理完成回调 - 适配新的ProjectResults"""
        total_files = len(project_results.detection_results)
        successful = sum(1 for result in project_results.detection_results if len(result.text_regions) > 0)
        
        self.statusBar().showMessage(f"批量处理完成: {successful}/{total_files} 成功")
        self.status_label.setText(f"批量完成: {successful}/{total_files}")
        
        # 获取项目统计信息
        project_stats = project_results.get_project_detection_results()['stats']
        
        completion_msg = f"项目 '{project_results.project_name}' 批量处理完成！\n\n"
        completion_msg += f"处理统计:\n"
        completion_msg += f"• 总文件数: {total_files}\n"
        completion_msg += f"• 检测成功: {successful}\n"
        completion_msg += f"• 总文字区域: {project_stats['total_regions']}\n"
        completion_msg += f"• OCR处理: {project_stats['images_with_ocr']}/{total_files}\n"
        completion_msg += f"• 总处理时间: {project_stats['total_detection_time']:.1f}s\n"
        
        if project_stats['total_ocr_time'] > 0:
            completion_msg += f"• OCR总时间: {project_stats['total_ocr_time']:.1f}s\n"
        
        completion_msg += f"\n输出目录已按项目结构组织，便于管理。"
        
        QMessageBox.information(self, "批量处理完成", completion_msg)
        
        # 恢复控件状态
        self.detect_button.setEnabled(True)
        self.ocr_button.setEnabled(self.current_results is not None)
        self.save_button.setEnabled(self.current_results is not None)
        self.progress_bar.setVisible(False)

    def on_batch_error(self, error_msg: str):
        """批量处理错误回调"""
        self.statusBar().showMessage("批量处理失败")
        self.status_label.setText("批量处理失败")
        QMessageBox.critical(self, "批量处理失败", f"处理过程中发生错误: {error_msg}")
        
        # 恢复控件状态
        self.detect_button.setEnabled(True)
        self.ocr_button.setEnabled(self.current_results is not None)
        self.save_button.setEnabled(self.current_results is not None)
        self.progress_bar.setVisible(False)

    def show_about(self):
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
        QMessageBox.about(self, "关于", about_text)
    
    def load_settings(self):
        """加载设置"""
        settings = QSettings("ComicTextDetector", "MainWindow")
        
        # 恢复窗口几何
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # 恢复最近文件
        recent_files = settings.value("recent_files", [])
        if isinstance(recent_files, list):
            self.recent_files = recent_files
            self.update_recent_menu()
    
    def save_settings(self):
        """保存设置"""
        settings = QSettings("ComicTextDetector", "MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("recent_files", self.recent_files)
    
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
        self.save_settings()
        
        if self.detector:
            del self.detector
        
        event.accept()


if __name__ == "__main__":
    import time  # 添加import
    
    app = QApplication(sys.argv)
    app.setApplicationName("漫画文本检测器")
    app.setApplicationVersion("1.0")
    
    window = ComicTextDetectorGUI()
    window.show()
    
    sys.exit(app.exec_())
```

### `widgets`

#### `image_viewer.py`

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

#### `parameter_panel.py`

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
        self.stats_labels = {}
        
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
        
        # 统计信息组
        stats_group = self.create_stats_group()
        layout.addWidget(stats_group)
        
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
    
    def create_stats_group(self) -> QGroupBox:
        """创建统计信息组"""
        group = QGroupBox("统计信息")
        layout = QVBoxLayout(group)
        
        stats_items = [
            ("total_regions", "检测区域:"),
            ("detection_time", "检测耗时:"),
            ("avg_confidence", "平均置信度:"),
            ("languages", "检测语言:")
        ]
        
        for key, label_text in stats_items:
            item_layout = QHBoxLayout()
            
            label = QLabel(label_text)
            value_label = QLabel("-")
            value_label.setAlignment(Qt.AlignRight)
            
            item_layout.addWidget(label)
            item_layout.addWidget(value_label)
            
            self.stats_labels[key] = value_label
            layout.addLayout(item_layout)
        
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
    
    def update_stats(self, stats: Dict[str, Any]):
        """更新统计信息"""
        if "stats" in stats:
            stats_data = stats["stats"]
        else:
            stats_data = stats
        
        # 更新各项统计
        if "total_regions" in stats_data:
            self.stats_labels["total_regions"].setText(str(stats_data["total_regions"]))
        
        # 检测时间
        detection_time = None
        if "detection_time" in stats_data:
            detection_time = stats_data["detection_time"]
        elif "detection_time" in stats:
            detection_time = stats["detection_time"]
            
        if detection_time is not None:
            self.stats_labels["detection_time"].setText(f"{detection_time:.2f}s")
        
        # 平均置信度
        if "avg_confidence" in stats_data:
            conf_val = stats_data["avg_confidence"]
            self.stats_labels["avg_confidence"].setText(f"{conf_val:.3f}")
        
        # 检测语言
        if "languages" in stats_data:
            langs = stats_data["languages"]
            lang_str = ", ".join(langs) if langs else "无"
            self.stats_labels["languages"].setText(lang_str)
    
    def clear_stats(self):
        """清空统计信息"""
        for label in self.stats_labels.values():
            label.setText("-")
    
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

#### `__init__.py`

```py

```

### `__init__.py`

```py

```

## `__init__.py`

```py

```

