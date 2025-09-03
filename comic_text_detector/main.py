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