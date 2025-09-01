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
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            
            # 检测器参数
            "detector": {
                "input_size": 1280,
                "conf_thresh": 0.4,
                "nms_thresh": 0.35,
                "mask_thresh": 0.3,
                "allowed_languages": ["zh", "ja"]
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
import os
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        replacements = [
            (r'from utils\.', 'from src.utils.'),
            (r'from models\.', 'from src.models.'),
            (r'from src.core.basemodel import', 'from src.core.basemodel import'),
            (r'from src.core.inference import', 'from src.core.inference import'),
        ]
        
        original_content = content
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"处理 {file_path} 出错: {e}")
        return False

# 执行修复
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
    for file in files:
        if file.endswith('.py'):
            file_path = Path(root) / file
            if fix_imports_in_file(file_path):
                print(f"修复: {file_path}")

print("导入路径修复完成")
```

# `main.py`

```py
#!/usr/bin/env python3
"""
漫画文本检测器 - 主程序入口
支持命令行和GUI两种模式
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.detector import ComicTextDetector
from src.gui.app import ComicTextDetectorGUI
from config.config import Config
from src.utils.general import set_logging

def parse_arguments():
    parser = argparse.ArgumentParser(description="漫画文本检测器")
    parser.add_argument("--mode", choices=["gui", "cli"], default="gui", 
                       help="运行模式：gui(图形界面) 或 cli(命令行)")
    parser.add_argument("--image", type=str, help="输入图片路径 (CLI模式)")
    parser.add_argument("--model", type=str, help="模型文件路径")
    parser.add_argument("--output", type=str, help="输出目录")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    
    return parser.parse_args()

def run_cli_mode(args):
    """命令行模式"""
    if not args.image:
        print("错误：CLI模式需要指定 --image 参数")
        return 1
    
    # 初始化检测器
    config = Config(args.config) if args.config else Config()
    detector = ComicTextDetector(
        model_path=args.model or config.model_path,
        device=config.device,
        **config.detector_params
    )
    
    # 执行检测
    try:
        results = detector.detect(args.image)
        
        # 保存结果
        output_dir = Path(args.output) if args.output else Path("results")
        detector.save_results(results, args.image, output_dir)
        
        print(f"检测完成！结果保存到: {output_dir}")
        return 0
        
    except Exception as e:
        print(f"检测失败：{e}")
        return 1

def run_gui_mode(args):
    """GUI模式"""
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

def main():
    args = parse_arguments()
    
    # 设置日志
    set_logging(verbose=args.verbose)
    
    if args.mode == "cli":
        return run_cli_mode(args)
    else:
        return run_gui_mode(args)

if __name__ == "__main__":
    sys.exit(main())
```

# `scripts`

## `demo.py`

```py

```

## `eval.py`

```py

```

## `train.py`

```py

```

## `__init__.py`

```py

```

# `setup.py`

```py

```

# `src`

## `core`

### `basemodel.py`

```py
# 修复后的 basemodel.py - 更新所有导入路径

from src.utils.general import CUDA, DEVICE  # 修复导入路径
from src.models.yolov5.yolo import Model  # 修复导入路径
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
            device: 计算设备 ('cuda', 'cpu', 'auto')
            config: 配置对象
            **kwargs: 其他检测参数
        """
        # 配置管理
        self.config = config or Config()
        
        # 设备设置
        if device == 'auto' or device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = device
        
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
            print(f"检测器初始化成功: {self.device}, 输入尺寸: {self.input_size}")
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
        
        print(f"开始检测: {Path(image_path).name}, 尺寸: {img.shape}")
        
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

        # num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
        # _, mask = cv2.threshold(mask, 50, 255, cv2.THRESH_BINARY)
        # draw_connected_labels(num_labels, labels, stats, centroids)
        # visualize_textblocks(img, blk_list)
        # cv2.imshow('rst', img)
        # cv2.imshow('mask', mask)
        # cv2.imshow('mask_refined', mask_refined)
        # cv2.waitKey(0)

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

## `gui`

### `app.py`

```py
"""
GUI应用主类
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

from src.core.detector import ComicTextDetector, DetectionResults
from src.gui.widgets.image_viewer import ImageViewer
from src.gui.widgets.parameter_panel import ParameterPanel
from config.config import Config


class DetectionWorker(QThread):
    """检测工作线程"""
    
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
            results = self.detector.detect(self.image_path)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class ComicTextDetectorGUI(QMainWindow):
    """漫画文本检测器GUI主窗口"""

    ASPECT_RATIO = 11 / 12  # 你想要的长宽比

    def resizeEvent(self, event):
        w = event.size().width()
        h = int(w / self.ASPECT_RATIO)
        self.resize(w, h)
        super().resizeEvent(event)
    
    def __init__(self):
        super().__init__()
        
        # 配置
        self.config = Config()
        
        # 应用状态
        self.detector: Optional[ComicTextDetector] = None
        self.current_results: Optional[DetectionResults] = None
        self.current_image_path: Optional[str] = None
        self.recent_files: List[str] = []
        
        # 工作线程
        self.detection_worker: Optional[DetectionWorker] = None
        
        # 初始化UI
        self.init_ui()
        self.init_detector()
        self.load_settings()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("漫画文本检测器 v1.0")
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
        
        # 右侧面板 - 图像显示
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 图像查看器
        self.image_viewer = ImageViewer()
        right_layout.addWidget(self.image_viewer, stretch=1)
        
        # 状态和控制栏
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 5, 0, 5)
        
        # 检测按钮
        self.detect_button = QPushButton("开始检测")
        self.detect_button.clicked.connect(self.start_detection)
        self.detect_button.setEnabled(False)
        status_layout.addWidget(self.detect_button)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # 保存按钮
        self.save_button = QPushButton("保存结果")
        self.save_button.clicked.connect(self.save_results)
        self.save_button.setEnabled(False)
        status_layout.addWidget(self.save_button)
        
        right_layout.addWidget(status_widget)
        main_layout.addWidget(right_widget, stretch=1)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        # 打开文件
        open_action = QAction('打开图片(&O)', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # 最近文件
        self.recent_menu = file_menu.addMenu('最近文件(&R)')
        self.update_recent_menu()
        
        file_menu.addSeparator()
        
        # 保存结果
        save_action = QAction('保存结果(&S)', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_results)
        file_menu.addAction(save_action)
        
        # 移除导出配置选项
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction('退出(&X)', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu('视图(&V)')
        
        # 缩放操作
        zoom_in_action = QAction('放大(&I)', self)
        zoom_in_action.setShortcut('Ctrl++')
        zoom_in_action.triggered.connect(self.image_viewer.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction('缩小(&O)', self)
        zoom_out_action.setShortcut('Ctrl+-')
        zoom_out_action.triggered.connect(self.image_viewer.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        fit_window_action = QAction('适应窗口(&F)', self)
        fit_window_action.setShortcut('Ctrl+F')
        fit_window_action.triggered.connect(self.image_viewer.fit_to_window)
        view_menu.addAction(fit_window_action)
        
        actual_size_action = QAction('实际大小(&A)', self)
        actual_size_action.setShortcut('Ctrl+1')
        actual_size_action.triggered.connect(self.image_viewer.actual_size)
        view_menu.addAction(actual_size_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        
        about_action = QAction('关于(&A)', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = self.addToolBar('主工具栏')
        
        # 打开文件
        open_action = QAction(QIcon(), '打开', self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        # 检测
        detect_action = QAction(QIcon(), '检测', self)
        detect_action.triggered.connect(self.start_detection)
        toolbar.addAction(detect_action)
        
        # 保存
        save_action = QAction(QIcon(), '保存', self)
        save_action.triggered.connect(self.save_results)
        toolbar.addAction(save_action)
    
    def init_detector(self):
        """初始化检测器"""
        try:
            model_path = self.parameter_panel.get_model_path()
            if model_path and Path(model_path).exists():
                params = self.parameter_panel.get_parameters()
                self.detector = ComicTextDetector(
                    model_path=model_path,
                    config=self.config,
                    **params
                )
                self.status_label.setText(f"检测器已加载: {Path(model_path).name}")
            else:
                self.status_label.setText("请选择模型文件")
        except Exception as e:
            QMessageBox.warning(self, "警告", f"检测器初始化失败: {e}")
            self.status_label.setText("检测器初始化失败")
    
    def open_file(self):
        """打开图片文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片文件", 
            str(self.config.examples_dir),
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        
        if file_path:
            self.load_image(file_path)
    
    def load_image(self, file_path: str):
        """加载图片"""
        try:
            # 显示图片
            self.image_viewer.load_image(file_path)
            self.current_image_path = file_path
            
            # 更新UI状态
            self.detect_button.setEnabled(self.detector is not None)
            self.save_button.setEnabled(False)
            
            # 更新最近文件
            self.add_recent_file(file_path)
            
            # 更新状态
            self.status_label.setText(f"已加载: {Path(file_path).name}")
            self.statusBar().showMessage(f"图片已加载: {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载图片: {e}")
    
    def start_detection(self):
        """开始检测"""
        if not self.current_image_path or not self.detector:
            return
        
        # 更新检测器参数
        params = self.parameter_panel.get_parameters()
        self.detector.update_parameters(**params)
        
        # 禁用按钮，显示进度
        self.detect_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        
        # 启动检测线程
        self.detection_worker = DetectionWorker(self.detector, self.current_image_path)
        self.detection_worker.finished.connect(self.on_detection_finished)
        self.detection_worker.error.connect(self.on_detection_error)
        self.detection_worker.progress.connect(self.on_detection_progress)
        self.detection_worker.start()
    
    def on_detection_finished(self, results: DetectionResults):
        """检测完成回调"""
        self.current_results = results
        
        # 显示结果图片
        self.image_viewer.set_result_image(results.result_image)
        self.image_viewer.set_detection_regions(results.text_regions)
        
        # 更新UI状态
        self.detect_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # 更新状态信息
        region_count = len(results.text_regions)
        detection_time = results.detection_time
        self.status_label.setText(f"检测完成: {region_count} 个区域, {detection_time:.2f}s")
        self.statusBar().showMessage(f"检测完成: 找到 {region_count} 个文字区域")
        
        # 更新参数面板统计信息
        self.parameter_panel.update_stats(results.to_dict())
    
    def on_detection_error(self, error_msg: str):
        """检测错误回调"""
        self.detect_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("检测失败")
        
        QMessageBox.critical(self, "检测失败", f"检测过程中发生错误: {error_msg}")
    
    def on_detection_progress(self, message: str):
        """检测进度回调"""
        self.statusBar().showMessage(message)
    
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
                QMessageBox.information(self, "成功", f"结果已保存到: {saved_dir}")
                self.statusBar().showMessage(f"结果已保存: {saved_dir}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")
    
    def on_parameters_changed(self):
        """参数变化回调"""
        if hasattr(self, 'detector') and self.detector:
            try:
                # 重新初始化检测器
                model_path = self.parameter_panel.get_model_path()
                if model_path != self.detector.model_path:
                    self.init_detector()
                else:
                    # 仅更新参数
                    params = self.parameter_panel.get_parameters()
                    self.detector.update_parameters(**params)
            except Exception as e:
                QMessageBox.warning(self, "警告", f"参数更新失败: {e}")
    
    def add_recent_file(self, file_path: str):
        """添加到最近文件"""
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        
        self.recent_files.insert(0, file_path)
        
        # 限制最近文件数量
        max_recent = self.config.gui_params.get('recent_files_count', 10)
        if len(self.recent_files) > max_recent:
            self.recent_files = self.recent_files[:max_recent]
        
        self.update_recent_menu()
    
    def update_recent_menu(self):
        """更新最近文件菜单"""
        self.recent_menu.clear()
        
        for i, file_path in enumerate(self.recent_files):
            if Path(file_path).exists():
                action = QAction(f"{i+1}. {Path(file_path).name}", self)
                action.triggered.connect(lambda checked, path=file_path: self.load_image(path))
                self.recent_menu.addAction(action)
        
        if not self.recent_files:
            action = QAction("(空)", self)
            action.setEnabled(False)
            self.recent_menu.addAction(action)
    
    def export_config(self):
        """导出配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "config.yaml", "配置文件 (*.yaml *.json)"
        )
        
        if file_path:
            try:
                self.config.save(file_path)
                QMessageBox.information(self, "成功", f"配置已导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h3>漫画文本检测器 v1.0</h3>
        <p>基于深度学习的漫画文本检测工具</p>
        <p><b>特性:</b></p>
        <ul>
        <li>支持中文和日文文本检测</li>
        <li>高精度的文本区域定位</li>
        <li>友好的图形用户界面</li>
        <li>可配置的检测参数</li>
        </ul>
        <p><b>技术支持:</b> PyQt5, PyTorch, OpenCV</p>
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
        
        # 保存窗口几何
        settings.setValue("geometry", self.saveGeometry())
        
        # 保存最近文件
        settings.setValue("recent_files", self.recent_files)
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 停止检测线程
        if self.detection_worker and self.detection_worker.isRunning():
            reply = QMessageBox.question(
                self, "确认退出", "检测正在进行中，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            
            self.detection_worker.quit()
            self.detection_worker.wait()
        
        # 保存设置
        self.save_settings()
        
        # 清理资源
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
            for i, region in enumerate(self.detection_regions):
                x1, y1, x2, y2 = region['bbox']
                
                # 设置颜色
                if i == self.selected_region:
                    color = QColor(255, 0, 0)  # 选中区域红色
                    line_width = 3
                else:
                    confidence = region.get('confidence', 1.0)
                    green_value = int(255 * min(confidence, 1.0))
                    color = QColor(0, green_value, 0)
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
                font = QFont("Arial", 9)
                painter.setFont(font)
                fm = QFontMetrics(font)
                text_rect = fm.boundingRect(label)
                text_rect.moveTopLeft(QPoint(x1, y1 - text_rect.height() - 2))
                
                painter.fillRect(text_rect.adjusted(-2, -2, 2, 2), color)
                painter.setPen(QPen(Qt.white))
                painter.drawText(text_rect, Qt.AlignCenter, label)
        
        finally:
            painter.end()
        
        return result_pixmap
    
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
            # 视图切换
            if self.result_image is not None:
                toggle_action = QAction("切换到结果图" if self.show_original else "切换到原图", self)
                toggle_action.triggered.connect(self.toggle_view)
                menu.addAction(toggle_action)
            
            # 区域显示切换
            regions_action = QAction("隐藏区域" if self.show_regions else "显示区域", self)
            regions_action.triggered.connect(self.toggle_regions)
            menu.addAction(regions_action)

            # 添加这个部分
            auto_fit_action = QAction("禁用自动适应" if self.auto_fit else "启用自动适应", self)
            auto_fit_action.triggered.connect(self.toggle_auto_fit)
            menu.addAction(auto_fit_action)

            menu.addSeparator()
            
            # 缩放选项
            zoom_in_action = QAction("放大", self)
            zoom_in_action.triggered.connect(self.zoom_in)
            menu.addAction(zoom_in_action)
            
            zoom_out_action = QAction("缩小", self)
            zoom_out_action.triggered.connect(self.zoom_out)
            menu.addAction(zoom_out_action)
            
            fit_action = QAction("适应窗口", self)
            fit_action.triggered.connect(self.fit_to_window)
            menu.addAction(fit_action)
            
            actual_action = QAction("实际大小", self)
            actual_action.triggered.connect(self.actual_size)
            menu.addAction(actual_action)
        
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
参数控制面板组件
"""

from pathlib import Path
from typing import Dict, Any

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
        self.input_size_combo = None
        self.conf_thresh_slider = None
        self.mask_thresh_slider = None
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

    def update_default_config(self):
        """更新默认配置"""
        try:
            # 获取当前参数
            current_params = self.get_parameters()
            model_path = self.get_model_path()
            
            # 更新配置对象
            if model_path:
                self.config.set('paths.default_model', str(Path(model_path).relative_to(self.config.project_root)))
            
            self.config.set('detector.input_size', current_params['input_size'])
            self.config.set('detector.conf_thresh', current_params['conf_thresh'])
            self.config.set('detector.mask_thresh', current_params['mask_thresh'])
            self.config.set('detector.allowed_languages', current_params['allowed_languages'])
            
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
    
    def create_model_group(self) -> QGroupBox:
        """创建模型选择组"""
        group = QGroupBox("模型设置")
        layout = QVBoxLayout(group)
        
        # 模型路径选择
        model_layout = QHBoxLayout()
        
        self.model_path_edit = QLineEdit()
        self.model_path_edit.setPlaceholderText("选择模型文件...")
        self.model_path_edit.textChanged.connect(self.parameters_changed.emit)
        
        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(self.browse_model)
        
        model_layout.addWidget(QLabel("模型文件:"))
        model_layout.addWidget(self.model_path_edit, 1)
        model_layout.addWidget(browse_button)
        
        layout.addLayout(model_layout)
        
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
        conf_layout = self.create_slider_layout(
            "置信度阈值:", 0.1, 0.9, 0.4, 
            lambda: self.parameters_changed.emit()
        )
        self.conf_thresh_slider = conf_layout[1]
        layout.addLayout(conf_layout[0])
        
        # 掩码阈值
        mask_layout = self.create_slider_layout(
            "掩码阈值:", 0.1, 0.8, 0.3,
            lambda: self.parameters_changed.emit()
        )
        self.mask_thresh_slider = mask_layout[1]
        layout.addLayout(mask_layout[0])
        
        return group
    
    def create_slider_layout(self, label_text: str, min_val: float, max_val: float, 
                            default_val: float, callback):
        """创建滑块布局"""
        layout = QVBoxLayout()
        
        # 标签和值显示
        header_layout = QHBoxLayout()
        label = QLabel(label_text)
        value_label = QLabel(f"{default_val:.2f}")
        header_layout.addWidget(label)
        header_layout.addStretch()
        header_layout.addWidget(value_label)
        layout.addLayout(header_layout)
        
        # 滑块
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(int(min_val * 100))
        slider.setMaximum(int(max_val * 100))
        slider.setValue(int(default_val * 100))
        
        # 连接信号
        def on_value_changed():
            val = slider.value() / 100.0
            value_label.setText(f"{val:.2f}")
            callback()
        
        slider.valueChanged.connect(on_value_changed)
        layout.addWidget(slider)
        
        return layout, slider
    
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
        """获取当前参数"""
        # 获取选中的语言
        allowed_languages = []
        for lang_code, checkbox in self.lang_checkboxes.items():
            if checkbox.isChecked():
                allowed_languages.append(lang_code)
        
        return {
            "input_size": int(self.input_size_combo.currentText()),
            "conf_thresh": self.conf_thresh_slider.value() / 100.0,
            "mask_thresh": self.mask_thresh_slider.value() / 100.0,
            "allowed_languages": allowed_languages
        }
    
    def set_parameters(self, params: Dict[str, Any]):
        """设置参数"""
        # 阻止信号发射
        self.blockSignals(True)
        
        try:
            if "input_size" in params:
                self.input_size_combo.setCurrentText(str(params["input_size"]))
            
            if "conf_thresh" in params:
                self.conf_thresh_slider.setValue(int(params["conf_thresh"] * 100))
            
            if "mask_thresh" in params:
                self.mask_thresh_slider.setValue(int(params["mask_thresh"] * 100))
            
            if "allowed_languages" in params:
                # 先取消所有选择
                for checkbox in self.lang_checkboxes.values():
                    checkbox.setChecked(False)
                
                # 然后选中指定语言
                for lang_code in params["allowed_languages"]:
                    if lang_code in self.lang_checkboxes:
                        self.lang_checkboxes[lang_code].setChecked(True)
        
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
            "allowed_languages": ["zh", "ja"]
        }
        self.set_parameters(default_params)
        self.parameters_changed.emit()
    
    def update_stats(self, stats: Dict[str, Any]):
        """更新统计信息"""
        if "stats" in stats:
            stats = stats["stats"]
        
        # 更新各项统计
        if "total_regions" in stats:
            self.stats_labels["total_regions"].setText(str(stats["total_regions"]))
        
        if "detection_time" in stats.get("parent", {}):
            time_val = stats["parent"]["detection_time"]
            self.stats_labels["detection_time"].setText(f"{time_val:.2f}s")
        elif "detection_time" in stats:
            time_val = stats["detection_time"]
            self.stats_labels["detection_time"].setText(f"{time_val:.2f}s")
        
        if "avg_confidence" in stats:
            conf_val = stats["avg_confidence"]
            self.stats_labels["avg_confidence"].setText(f"{conf_val:.3f}")
        
        if "languages" in stats:
            langs = stats["languages"]
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
输入尺寸: {params['input_size']}
置信度阈值: {params['conf_thresh']:.2f}
掩码阈值: {params['mask_thresh']:.2f}
支持语言: {', '.join(params['allowed_languages'])}"""
        
        return summary


class AdvancedParameterDialog(QDialog):
    """高级参数设置对话框"""
    
    def __init__(self, current_params: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.current_params = current_params.copy()
        self.result_params = current_params.copy()
        
        self.init_ui()
        self.load_parameters()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("高级参数设置")
        self.setModal(True)
        self.resize(400, 500)
        
        layout = QVBoxLayout(self)
        
        # 参数组
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # NMS阈值
        nms_group = QGroupBox("NMS参数")
        nms_layout = QVBoxLayout(nms_group)
        
        self.nms_thresh_spin = QDoubleSpinBox()
        self.nms_thresh_spin.setRange(0.1, 0.9)
        self.nms_thresh_spin.setSingleStep(0.05)
        self.nms_thresh_spin.setValue(0.35)
        
        nms_layout.addWidget(QLabel("NMS阈值:"))
        nms_layout.addWidget(self.nms_thresh_spin)
        scroll_layout.addWidget(nms_group)
        
        # 其他高级参数可以在这里添加
        # ...
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消") 
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def load_parameters(self):
        """加载参数"""
        if "nms_thresh" in self.current_params:
            self.nms_thresh_spin.setValue(self.current_params["nms_thresh"])
    
    def accept(self):
        """确认对话框"""
        self.result_params["nms_thresh"] = self.nms_thresh_spin.value()
        super().accept()
    
    def get_parameters(self) -> Dict[str, Any]:
        """获取参数"""
        return self.result_params


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

## `utils`

### `db_utils.py`

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

### `general.py`

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

### `imgproc_utils.py`

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

### `io_utils.py`

```py
import os
import os.path as osp
import glob
from pathlib import Path
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

### `textblock.py`

```py
from typing import List
import numpy as np
from shapely.geometry import Polygon
import math
import copy
from src.utils.imgproc_utils import union_area, xywh2xyxypoly, rotate_polygons
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
        # cv2.imshow('region'+str(idx), region)
        # cv2.waitKey(0)
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

### `textmask.py`

```py
from os import stat
from typing import List
import cv2
import numpy as np
from .textblock import TextBlock
from .imgproc_utils import draw_connected_labels, expand_textwindow, union_area

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

# def extract_textballoon(img, pred_textmsk=None, global_mask=None):
#     if len(img.shape) > 2 and img.shape[2] == 3:
#         img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     im_h, im_w = img.shape[0], img.shape[1]
#     hyp_textmsk = np.zeros((im_h, im_w), np.uint8)
#     thresh_val, threshed = cv2.threshold(img, 1, 255, cv2.THRESH_OTSU+cv2.THRESH_BINARY)
#     xormap_sum = cv2.bitwise_xor(threshed, pred_textmsk).sum()
#     neg_threshed = 255 - threshed
#     neg_xormap_sum = cv2.bitwise_xor(neg_threshed, pred_textmsk).sum()
#     neg_thresh = neg_xormap_sum < xormap_sum
#     if neg_thresh:
#         threshed = neg_threshed
#     thresh_info = {'thresh_val': thresh_val,'neg_thresh': neg_thresh}
#     connectivity = 8
#     num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(threshed, connectivity, cv2.CV_16U)
#     label_unchanged = np.copy(labels)
#     if global_mask is not None:
#         labels[np.where(global_mask==0)] = 0
#     text_labels = []
#     if pred_textmsk is not None:
#         text_score_thresh = 0.5
#         textbbox_map = np.zeros_like(pred_textmsk)
#         for label_index, stat, centroid in zip(range(num_labels), stats, centroids):
#             if label_index != 0: # skip background label
#                 x, y, w, h, area = stat
#                 area *= 255
#                 x1, y1, x2, y2 = x, y, x+w, y+h
#                 label_local = labels[y1: y2, x1: x2]
#                 label_coordinates = np.where(label_local==label_index)
#                 tmp_merged = np.zeros((h, w), np.uint8)
#                 tmp_merged[label_coordinates] = 255
#                 andmap = cv2.bitwise_and(tmp_merged, pred_textmsk[y1: y2, x1: x2])
#                 text_score = andmap.sum() / area
#                 if text_score > text_score_thresh:
#                     text_labels.append(label_index)
#                     hyp_textmsk[y1: y2, x1: x2][label_coordinates] = 255
#     labels = label_unchanged
#     bubble_msk = np.zeros((img.shape[0], img.shape[1]), np.uint8)
#     bubble_msk[np.where(labels==0)] = 255
#     # if lang == LANG_JPN:
#     bubble_msk = cv2.erode(bubble_msk, (3, 3), iterations=1)
#     line_thickness = 2
#     cv2.rectangle(bubble_msk, (0, 0), (im_w, im_h), BLACK, line_thickness, cv2.LINE_8)
#     contours, hiers = cv2.findContours(bubble_msk, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)

#     brect_area_thresh = im_h * im_w * 0.4
#     min_brect_area = np.inf
#     ballon_index = -1
#     maximum_pixsum = -1
#     for ii, contour in enumerate(contours):
#         brect = cv2.boundingRect(contours[ii])
#         brect_area = brect[2] * brect[3]
#         if brect_area > brect_area_thresh and brect_area < min_brect_area:
#             tmp_ballonmsk = np.zeros_like(bubble_msk)
#             tmp_ballonmsk = cv2.drawContours(tmp_ballonmsk, contours, ii, WHITE, cv2.FILLED)
#             andmap_sum = cv2.bitwise_and(tmp_ballonmsk, hyp_textmsk).sum()
#             if andmap_sum > maximum_pixsum:
#                 maximum_pixsum = andmap_sum
#                 min_brect_area = brect_area
#                 ballon_index = ii
#     if ballon_index != -1:
#         bubble_msk = np.zeros_like(bubble_msk)
#         bubble_msk = cv2.drawContours(bubble_msk, contours, ballon_index, WHITE, cv2.FILLED)
#     hyp_textmsk = cv2.bitwise_and(hyp_textmsk, bubble_msk)
#     return hyp_textmsk, bubble_msk, thresh_info, (num_labels, label_unchanged, stats, centroids, text_labels)

# def extract_textballoon_channelwise(img, pred_textmsk, test_grey=True, global_mask=None):
#     c_list = [img[:, :, i] for i in range(3)]
#     if test_grey:
#         c_list.append(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
#     best_xorpix_sum = np.inf
#     best_cindex = best_hyptextmsk = best_bubblemsk = best_thresh_info = best_component_stats = None
#     for c_index, channel in enumerate(c_list):
#         hyp_textmsk, bubble_msk, thresh_info, component_stats = extract_textballoon(channel, pred_textmsk, global_mask=global_mask)
#         pixor_sum = cv2.bitwise_xor(hyp_textmsk, pred_textmsk).sum()
#         if pixor_sum < best_xorpix_sum:
#             best_xorpix_sum = pixor_sum
#             best_cindex = c_index
#             best_hyptextmsk, best_bubblemsk, best_thresh_info, best_component_stats = hyp_textmsk, bubble_msk, thresh_info, component_stats
#     return best_hyptextmsk, best_bubblemsk, best_component_stats

# def refine_textmask(img, pred_mask, channel_wise=True, find_leaveouts=True, global_mask=None):
#     hyp_textmsk, bubble_msk, component_stats = extract_textballoon_channelwise(img, pred_mask, global_mask=global_mask)
#     num_labels, labels, stats, centroids, text_labels = component_stats
#     stats = np.array(stats)
#     text_stats = stats[text_labels]
#     if find_leaveouts and len(text_stats) > 0:
#         median_h = np.median(text_stats[:, 3])
#         for label, label_h in zip(range(num_labels), stats[:, 3]):
#             if label == 0 or label in text_labels:
#                 continue
#             if label_h > 0.5 * median_h and label_h < 1.5 * median_h:
#                 hyp_textmsk[np.where(labels==label)] = 255
#         hyp_textmsk = cv2.bitwise_and(hyp_textmsk, bubble_msk)
#         if global_mask is not None:
#             hyp_textmsk = cv2.bitwise_and(hyp_textmsk, global_mask)
#     return hyp_textmsk, bubble_msk
```

### `weight_init.py`

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

### `yolov5_utils.py`

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

### `__init__.py`

```py

```

## `__init__.py`

```py

```

