from PyQt6.QtWidgets import QDockWidget, QTreeView, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QMenu, QMessageBox
from PyQt6.QtGui import QFileSystemModel, QAction
from PyQt6.QtCore import Qt, pyqtSignal, QSortFilterProxyModel, QDir, QProcess
from PyQt6.QtGui import QContextMenuEvent
import os
import sys

class ResultJsonFilterProxyModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        index = model.index(source_row, 0, source_parent)
        file_path = model.filePath(index)
        file_name = model.fileName(index)
        
        # Exclude files ending with _result.json (we don't want to show them directly)
        if file_name.endswith("_result.json"):
            return False
        
        # Exclude "result" folder
        if file_name == "result" and os.path.isdir(file_path):
            return False
        
        return super().filterAcceptsRow(source_row, source_parent)

class FileBrowserDock(QDockWidget):
    file_double_clicked = pyqtSignal(str)

    def __init__(self, title, target_directory, parent=None):
        super().__init__(title, parent)
        self.target_directory = target_directory
        self.parent_main_window = parent  # Store reference to parent main window
        self._init_ui()

    def _init_ui(self):
        self.model = QFileSystemModel()
        self.model.setRootPath(self.target_directory)
        self.model.setNameFilters(["*.json"]) # 只显示json文件
        self.model.setNameFilterDisables(False) # Enable filtering

        self.proxy_model = ResultJsonFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.proxy_model)
        self.tree_view.setRootIndex(self.proxy_model.mapFromSource(self.model.index(self.target_directory)))
        self.tree_view.setColumnHidden(1, True) # Hide size column
        self.tree_view.setColumnHidden(2, True) # Hide type column
        self.tree_view.setColumnHidden(3, True) # Hide date modified column
        self.tree_view.setHeaderHidden(True) # Hide the header to remove "Name" label
        self.tree_view.clicked.connect(self._on_file_clicked)
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self._on_context_menu)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tree_view)

        container_widget = QWidget()
        container_widget.setLayout(main_layout)
        self.setWidget(container_widget)

    def _on_context_menu(self, position):
        """Handle context menu request"""
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return
            
        source_index = self.proxy_model.mapToSource(index)
        file_path = self.model.filePath(source_index)
        file_name = os.path.basename(file_path)
        
        # 只对.json文件显示右键菜单（排除_result.json）
        if not file_name.endswith(".json") or file_name.endswith("_result.json"):
            return
            
        # 创建右键菜单
        context_menu = QMenu(self)
        
        # 添加"回填"动作
        backfill_action = QAction("回填", self)
        backfill_action.triggered.connect(lambda: self._on_backfill_action(file_path))
        context_menu.addAction(backfill_action)
        
        # 显示菜单
        context_menu.exec(self.tree_view.viewport().mapToGlobal(position))
    
    def _on_backfill_action(self, file_path):
        """处理回填动作"""
        try:
            # 获取文件的基本名称（不带扩展名）
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # 构建result文件夹中对应的_result.json文件路径
            dir_path = os.path.dirname(file_path)
            result_dir = os.path.join(dir_path, "result")
            result_file_path = os.path.join(result_dir, f"{base_name}_result.json")
            
            # 检查result文件是否存在
            if not os.path.exists(result_file_path):
                QMessageBox.critical(self, "错误", f"找不到对应的result文件: {result_file_path}")
                return
                
            # 获取fill_form_data.py的路径
            # 从当前文件位置计算到tools目录的路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 从ui/dock目录回到flowchart根目录，然后进入tools目录
            script_dir = os.path.dirname(os.path.dirname(current_dir))
            fill_form_script = os.path.join(script_dir, "tools", "fill_form_data.py")
            
            # 检查脚本是否存在
            if not os.path.exists(fill_form_script):
                QMessageBox.critical(self, "错误", f"找不到回填脚本: {fill_form_script}")
                return
                
            # 创建进程运行脚本
            process = QProcess(self)
            
            # 构建命令
            if sys.platform == "win32":
                # Windows系统
                command = f'python "{fill_form_script}" "{result_file_path}" --no-headless'
                process.startCommand(command)
            else:
                # 其他系统
                process.start("python", [fill_form_script, result_file_path, "--no-headless"])
                
            # 等待进程启动
            if not process.waitForStarted(3000):
                QMessageBox.critical(self, "错误", "无法启动回填脚本")
                return
                
            # 成功启动，不显示提示信息
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"执行回填操作时出错: {str(e)}")

    def _on_file_clicked(self, index):
        source_index = self.proxy_model.mapToSource(index)
        file_path = self.model.filePath(source_index)
        if os.path.isfile(file_path) and file_path.endswith(".json"):
            self.file_double_clicked.emit(file_path)

    def _refresh_view(self):
        self.model.setRootPath(self.target_directory)
        self.tree_view.setRootIndex(self.proxy_model.mapFromSource(self.model.index(self.target_directory)))