from PyQt6.QtWidgets import QStyledItemDelegate, QTextEdit, QMessageBox, QStyle
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextDocument, QPainter


class RichTextDelegate(QStyledItemDelegate):
    """支持富文本显示的自定义委托"""
    
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        # 获取单元格文本
        text = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        
        # 检查是否是富文本
        is_rich_text = index.model().data(index, Qt.ItemDataRole.UserRole) == "rich_text"
        
        if text:
            # 创建QTextDocument用于富文本渲染
            doc = QTextDocument()
            doc.setDefaultFont(option.font)
            
            # 如果是富文本或包含HTML标签，则使用HTML格式
            if is_rich_text or ("<" in text and ">" in text):
                doc.setHtml(text)
            else:
                doc.setPlainText(text)
            
            # 设置文档大小
            doc.setTextWidth(option.rect.width())
            
            # 绘制单元格背景
            painter.save()
            painter.fillRect(option.rect, option.palette.highlight() if option.state & QStyle.StateFlag.State_Selected else option.palette.base())
            painter.restore()
            
            # 绘制富文本内容
            painter.save()
            painter.translate(option.rect.topLeft())
            # 设置裁剪区域，防止文本溢出
            painter.setClipRect(option.rect.translated(-option.rect.topLeft()))
            doc.drawContents(painter)
            painter.restore()
        else:
            # 如果没有文本，使用默认绘制
            super().paint(painter, option, index)

    def sizeHint(self, option, index):
        # 获取文本内容
        text = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        
        # 检查是否是富文本
        is_rich_text = index.model().data(index, Qt.ItemDataRole.UserRole) == "rich_text"
        
        if text:
            # 创建QTextDocument计算所需大小
            doc = QTextDocument()
            doc.setDefaultFont(option.font)
            
            # 如果是富文本或包含HTML标签，则使用HTML格式
            if is_rich_text or ("<" in text and ">" in text):
                doc.setHtml(text)
            else:
                doc.setPlainText(text)
                
            doc.setTextWidth(option.rect.width())
            # 返回文档大小
            return doc.size().toSize()
        else:
            # 使用默认大小提示
            return super().sizeHint(option, index)

    def createEditor(self, parent, option, index):
        # 创建QTextEdit作为编辑器以支持富文本编辑
        editor = QTextEdit(parent)
        # 设置编辑器样式，确保与表格一致
        editor.setStyleSheet("border: none; background-color: transparent;")
        return editor

    def setEditorData(self, editor, index):
        # 设置编辑器的数据
        if isinstance(editor, QTextEdit):
            value = index.model().data(index, Qt.ItemDataRole.DisplayRole)
            # 检查是否是富文本
            is_rich_text = index.model().data(index, Qt.ItemDataRole.UserRole) == "rich_text"
            
            # 如果是富文本或包含HTML标签，则使用HTML格式
            if is_rich_text or ("<" in str(value) and ">" in str(value)):
                editor.setHtml(str(value))
            else:
                editor.setPlainText(str(value))
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        # 保存编辑器的数据到模型
        if isinstance(editor, QTextEdit):
            # 获取编辑器的纯文本内容
            plain_text = editor.toPlainText()
            
            # 检查是否包含"你"字
            if "你" in plain_text:
                # 如果包含"你"字，则使用HTML格式保存
                html_content = plain_text.replace("你", "<span style='color: red; font-weight: bold;'>你</span>")
                model.setData(index, html_content, Qt.ItemDataRole.EditRole)
                # 同时更新UserRole数据，确保富文本标记得以保留
                model.setData(index, "rich_text", Qt.ItemDataRole.UserRole)
            else:
                # 如果不包含"你"字，则保存纯文本
                model.setData(index, plain_text, Qt.ItemDataRole.EditRole)
                # 清除富文本标记
                model.setData(index, None, Qt.ItemDataRole.UserRole)
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        # 更新编辑器的几何位置
        editor.setGeometry(option.rect)