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