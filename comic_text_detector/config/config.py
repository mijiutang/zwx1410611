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
        self.config_file = config_file
        
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
        
        if self.config_file and Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    if self.config_file.endswith('.yaml') or self.config_file.endswith('.yml'):
                        user_config = yaml.safe_load(f)
                    else:
                        user_config = json.load(f)
                
                # 递归更新配置
                config = self._deep_update(config, user_config)
                
            except Exception as e:
                print(f"警告：无法加载配置文件 {self.config_file}: {e}")
        
        return config
    
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
            file_path = self.config_file or "config.yaml"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            else:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    # 便捷属性
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


# 创建默认配置文件
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
    
    # 创建默认配置文件
    create_default_config()