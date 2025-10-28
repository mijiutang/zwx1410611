#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
约束配置编辑器启动脚本
"""

import sys
import os

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 导入并运行约束编辑器
from constraint_editor import main

if __name__ == "__main__":
    main()