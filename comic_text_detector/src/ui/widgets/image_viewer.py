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
        self.show_lines = True
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
            # 原有的文本块绘制代码保持不变
            if self.show_regions:
                for i, region in enumerate(self.detection_regions):
                    x1, y1, x2, y2 = region['bbox']
                    
                    # 设置颜色
                    if i == self.selected_region:
                        color = QColor(255, 0, 0)  # 选中区域红色
                        line_width = 3
                    else:
                        confidence = region.get('confidence', 1.0)
                        blue_value = int(255 * min(confidence, 1.0))
                        color = QColor(50, 100, blue_value)  # 蓝色方框，根据置信度调整蓝色强度
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
                    font = QFont("Arial", 16)
                    painter.setFont(font)
                    fm = QFontMetrics(font)
                    text_rect = fm.boundingRect(label)
                    text_rect.moveTopLeft(QPoint(x1, y1 - text_rect.height() - 2))
                    
                    painter.fillRect(text_rect.adjusted(-2, -2, 2, 2), color)
                    painter.setPen(QPen(Qt.white))
                    painter.drawText(text_rect, Qt.AlignCenter, label)
            
            # 新增：绘制文本行
            if self.show_lines:
                cyan_color = QColor(0, 255, 255)  # 青色
                pen = QPen(cyan_color, 1)
                painter.setPen(pen)
                
                for i, region in enumerate(self.detection_regions):
                    # 从TextBlock对象获取文本行数据
                    if hasattr(region, 'lines') and region.lines:
                        lines = region.lines
                    elif 'lines' in region and region['lines']:
                        lines = region['lines']
                    else:
                        continue
                    
                    # 绘制每个文本行
                    for line_idx, line_coords in enumerate(lines):
                        if len(line_coords) >= 4:  # 确保有足够的坐标点
                            # line_coords 应该是 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] 格式
                            points = []
                            for coord in line_coords:
                                if len(coord) >= 2:
                                    points.append(QPoint(int(coord[0]), int(coord[1])))
                            
                            if len(points) >= 3:  # 至少需要3个点来绘制多边形
                                polygon = QPolygon(points)
                                painter.drawPolygon(polygon)
        
        finally:
            painter.end()
        
        return result_pixmap    
    
    def toggle_lines(self):
        """切换文本行显示"""
        self.show_lines = not self.show_lines
        self.update_display()

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
            # 只保留视图切换功能（如果有结果图的话）
            if self.result_image is not None:
                toggle_action = QAction("切换到结果图" if self.show_original else "切换到原图", self)
                toggle_action.triggered.connect(self.toggle_view)
                menu.addAction(toggle_action)
            
            # 如果菜单不为空才显示
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