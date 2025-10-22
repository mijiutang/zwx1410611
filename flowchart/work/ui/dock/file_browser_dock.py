from PyQt5.QtWidgets import QDockWidget, QTreeView, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QFileSystemModel
from PyQt5.QtCore import Qt, pyqtSignal, QSortFilterProxyModel
import os

class ResultJsonFilterProxyModel(QSortFilterProxyModel):
    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        index = model.index(source_row, 0, source_parent)
        file_name = model.fileName(index)
        
        # Exclude files ending with _result.json
        if file_name.endswith("_result.json"):
            return False
        
        return super().filterAcceptsRow(source_row, source_parent)

class FileBrowserDock(QDockWidget):
    file_double_clicked = pyqtSignal(str)

    def __init__(self, title, target_directory, parent=None):
        super().__init__(title, parent)
        self.target_directory = target_directory
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
        self.tree_view.doubleClicked.connect(self._on_file_double_clicked)

        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self._refresh_view)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tree_view)
        main_layout.addLayout(button_layout)

        container_widget = QWidget()
        container_widget.setLayout(main_layout)
        self.setWidget(container_widget)

    def _on_file_double_clicked(self, index):
        source_index = self.proxy_model.mapToSource(index)
        file_path = self.model.filePath(source_index)
        if os.path.isfile(file_path) and file_path.endswith(".json"):
            self.file_double_clicked.emit(file_path)

    def _refresh_view(self):
        self.model.setRootPath(self.target_directory)
        self.tree_view.setRootIndex(self.proxy_model.mapFromSource(self.model.index(self.target_directory)))

