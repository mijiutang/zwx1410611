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
from src.ui.main_window import ComicTextDetectorGUI
from config.config import Config
from src.utils.general import set_logging

def parse_arguments():
    parser = argparse.ArgumentParser(description="漫画文本检测器 - 批量处理模式")
    parser.add_argument("--mode", choices=["gui", "cli"], default="gui", 
                       help="运行模式：gui(图形界面) 或 cli(命令行)")
    parser.add_argument("--input_dir", type=str, help="输入图片文件夹路径 (CLI模式)", required=False)  # 改为文件夹
    parser.add_argument("--model", type=str, help="模型文件路径")
    parser.add_argument("--output", type=str, help="输出目录")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--device", type=str, choices=["auto", "cpu", "cuda", "cuda:0", "cuda:1"], 
                       default="auto", help="计算设备 (auto/cpu/cuda/cuda:0/cuda:1)")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    
    return parser.parse_args()

def run_cli_mode(args):
    """命令行模式 - 批量处理"""
    if not args.input_dir:
        print("错误：CLI模式需要指定 --input_dir 参数")
        return 1
    
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"错误：输入文件夹不存在: {input_dir}")
        return 1
    
    # 检查是否有图片文件
    from src.utils.io_utils import find_all_imgs
    image_files = find_all_imgs(str(input_dir), abs_path=True)
    if not image_files:
        print(f"错误：文件夹中没有找到图片文件: {input_dir}")
        return 1
    
    # 初始化检测器
    config = Config(args.config) if args.config else Config()
    detector = ComicTextDetector(
        model_path=args.model or config.model_path,
        device=args.device,
        **config.detector_params
    )
    
    # 执行批量处理
    try:
        output_dir = Path(args.output) if args.output else Path("batch_results")
        
        print(f"开始批量处理，共 {len(image_files)} 个文件...")
        batch_results = detector.batch_process_with_ocr(image_files, output_dir)
        
        print(f"批量处理完成！结果保存到: {output_dir}")
        print(f"处理了 {len(batch_results)} 个文件")
        return 0
        
    except Exception as e:
        print(f"批量处理失败：{e}")
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