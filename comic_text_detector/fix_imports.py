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