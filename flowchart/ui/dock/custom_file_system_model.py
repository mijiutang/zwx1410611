from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtCore import Qt
import os
import json

class CustomFileSystemModel(QFileSystemModel):
    """自定义文件系统模型，用于实现包含特定文本的文件高亮显示"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlight_keyword = "你"  # 默认高亮关键字
        self.highlighted_files = set()  # 存储包含关键字的文件路径
    
    def setData(self, index, value, role):
        """重写setData方法以支持文件高亮"""
        if role == Qt.ItemDataRole.ForegroundRole:
            # 设置文本颜色
            return super().setData(index, value, role)
        return super().setData(index, value, role)
    
    def data(self, index, role):
        """重写data方法以实现文件高亮显示"""
        if not index.isValid():
            return super().data(index, role)
        
        # 获取文件路径
        file_path = self.filePath(index)
        
        # 检查是否是文件并且是JSON文件
        if (role == Qt.ItemDataRole.ForegroundRole and 
            os.path.isfile(file_path) and 
            file_path.endswith('.json') and 
            file_path in self.highlighted_files):
            # 返回红色
            return QColor(Qt.GlobalColor.red)
        
        return super().data(index, role)
    
    def check_file_for_keyword(self, file_path):
        """检查文件是否包含关键字"""
        if not os.path.isfile(file_path) or not file_path.endswith('.json'):
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 递归检查JSON数据中是否包含关键字
                return self._contains_keyword(data, self.highlight_keyword)
        except (json.JSONDecodeError, UnicodeDecodeError, FileNotFoundError):
            # 如果文件无法读取或解析，返回False
            return False
    
    def _contains_keyword(self, obj, keyword):
        """递归检查对象中是否包含关键字"""
        if isinstance(obj, str):
            return keyword in obj
        elif isinstance(obj, dict):
            for key, value in obj.items():
                if (isinstance(key, str) and keyword in key) or self._contains_keyword(value, keyword):
                    return True
        elif isinstance(obj, list):
            for item in obj:
                if self._contains_keyword(item, keyword):
                    return True
        return False
    
    def update_highlighted_files(self, directory):
        """更新包含关键字的文件列表"""
        self.highlighted_files.clear()
        
        # 遍历目录中的所有JSON文件
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    if self.check_file_for_keyword(file_path):
                        self.highlighted_files.add(file_path)