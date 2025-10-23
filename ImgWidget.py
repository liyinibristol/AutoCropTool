import sys
import os
import numpy as np
import cv2
from glob import glob
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QLabel, QPushButton, QFileDialog, QSlider,
                             QMessageBox, QScrollArea, QGridLayout, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QRect, QRegExp
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QWheelEvent, QRegExpValidator


class Canvas(QWidget):
    """
    抽象的图像显示窗口类
    基于 QWidget，支持缩放、裁剪框显示、鼠标交互等功能
    """
    crop_rect_sync = pyqtSignal(list)
    zoom_sync = pyqtSignal(float)
    mov_sync = pyqtSignal(list)

    def __init__(self, title="Image Display", show_crop_rect=True):
        super().__init__()
        self.title = title
        self.show_crop_rect = show_crop_rect

        # 文件属性
        self.img_folder = None
        self.img_files_path = []
        self.img_current_path = None
        self.frm_idx = 0


        # 图像属性
        self.original_image = None
        self.display_image = None
        self.pixmap = None

        # 拖拽相关属性
        self.image_dragging = False  # 是否正在拖拽图像
        self.image_position = [0, 0]  # 图像在窗口中的位置（用于拖拽）

        # 交互属性
        self.crop_rect = [0, 0, 1920, 1080]
        self.rect_dragging = False
        self.drag_start = None
        self.zoom_factor = 0.5
        self.image_offset = [0, 0]  # 图像在窗口中的偏移量

        # 设置窗口属性
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)

    def init_img_folder(self, folder):
        self.img_folder = folder

        self.img_files_path = glob(os.path.join(folder, "*.png"))
        self.img_files_path += glob(os.path.join(folder, "*.jpg"))
        self.img_files_path += glob(os.path.join(folder, "*.tiff"))
        self.img_files_path += glob(os.path.join(folder, "*.tif"))
        self.img_files_path.sort()

        self.img_current_path = self.img_files_path[self.frm_idx]

        if self.img_current_path:
            original_image = cv2.imread(self.img_current_path)
            if original_image is not None:
                display_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
                if display_image.shape[0] < 1080 or display_image.shape[1] < 1920:
                    QMessageBox.warning(self, "Warning", "The image size is smaller than 1080x1920.")
                    self.show_crop_rect = False
                else:
                    self.show_crop_rect = True
                self.set_image(display_image)
                self.set_crop_rect(self.crop_rect)
        else:
            QMessageBox.critical(self, "Error", "Failed to image from: {}".format(self.img_current_path))

        return len(self.img_files_path)

    def set_image_via_idx(self, frm_idx):
        self.frm_idx = frm_idx
        self.img_current_path = self.img_files_path[self.frm_idx]

        if self.img_current_path:
            original_image = cv2.imread(self.img_current_path)
            if original_image is not None:
                display_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
                if display_image.shape[0] < 1080 or display_image.shape[1] < 1920:
                    QMessageBox.warning(self, "Warning", "The image size is smaller than 1080x1920.")
                    self.show_crop_rect = False
                else:
                    self.show_crop_rect = True
                self.set_image(display_image)

        else:
            QMessageBox.critical(self, "Error", "Failed to image from: {}".format(self.img_current_path))

    def set_image(self, image):
        """设置图像"""
        if image is not None:
            self.original_image = image
            self.display_image = image.copy()
            self.update_display()

    def set_offset(self, offset):
        self.image_offset = offset
        if self.original_image is not None:
            self.update()

    def set_zoom(self, zoom_factor):
        """设置缩放比例"""
        self.zoom_factor = zoom_factor
        if self.original_image is not None:
            self.update_display()

    def update_display(self):
        """更新显示"""
        if self.original_image is not None:
            # 应用缩放
            if self.zoom_factor != 1.0:
                new_width = int(self.original_image.shape[1] * self.zoom_factor)
                new_height = int(self.original_image.shape[0] * self.zoom_factor)
                self.display_image = cv2.resize(self.original_image, (new_width, new_height))
            else:
                self.display_image = self.original_image.copy()

            # 转换为 QPixmap
            height, width = self.display_image.shape[:2]
            bytes_per_line = 3 * width

            q_img = QImage(self.display_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            self.pixmap = QPixmap.fromImage(q_img)

            # 更新显示
            self.update()

    def set_crop_rect(self, rect):
        """设置裁剪区域"""
        self.crop_rect = rect
        # print(rect)
        self.update()

    def get_current_image(self):
        """获取当前显示的图像"""
        return self.display_image if self.display_image is not None else self.original_image

    def paintEvent(self, event):
        """绘制事件 - 绘制图像和覆盖物"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 填充背景
        painter.fillRect(self.rect(), QColor(250, 250, 250))

        if self.pixmap and not self.pixmap.isNull():
            # 计算图像在窗口中的位置（居中显示）
            # pixmap_rect = self.pixmap.rect()
            # window_rect = self.rect()

            # 计算居中位置
            # x = (window_rect.width() - pixmap_rect.width()) // 2
            # y = (window_rect.height() - pixmap_rect.height()) // 2
            # self.image_offset = [x, y]

            x, y = self.image_offset

            # 绘制图像
            painter.drawPixmap(x, y, self.pixmap)

            # 绘制裁剪框（如果启用）
            if self.show_crop_rect and self.original_image is not None:
                self.draw_crop_rect(painter)

            # 绘制标题和缩放信息
            # painter.setPen(QPen(QColor(0, 255, 0), 1))
            # info_text = f"{self.title} - Zoom: {self.zoom_factor:.1f}x"
            # painter.drawText(10, 20, info_text)

        else:
            # 没有图像时显示提示文本
            painter.drawText(self.rect(), Qt.AlignCenter,
                             f"{self.title}\n\nNo image loaded\n")

        # 绘制窗口边框
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))


    def draw_crop_rect(self, painter):
        """绘制裁剪矩形"""
        if not self.show_crop_rect or self.original_image is None:
            return

        # 计算裁剪矩形的显示坐标
        display_x = self.crop_rect[0] * self.zoom_factor + self.image_offset[0]
        display_y = self.crop_rect[1] * self.zoom_factor + self.image_offset[1]
        display_w = self.crop_rect[2] * self.zoom_factor
        display_h = self.crop_rect[3] * self.zoom_factor

        # 绘制裁剪矩形边框
        pen = QPen(QColor(0, 255, 0), 3)
        painter.setPen(pen)
        painter.drawRect(int(display_x), int(display_y), int(display_w), int(display_h))

        # 绘制半透明填充
        painter.fillRect(int(display_x), int(display_y), int(display_w), int(display_h),
                         QColor(255, 255, 255, 35))


    def wheelEvent(self, event):
        """鼠标滚轮事件 - 缩放"""
        if self.original_image is not None:
            degrees = event.angleDelta().y() / 8
            steps = degrees / 15

            new_zoom = self.zoom_factor + (steps * self.zoom_factor * 0.1)
            new_zoom = max(0.1, min(5.0, new_zoom))

            self.zoom_factor = new_zoom
            self.set_zoom(self.zoom_factor)
            # 发送事件
            self.zoom_sync.emit(self.zoom_factor)

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if self.original_image is not None and event.button() == Qt.LeftButton:
            if self.show_crop_rect:
            # 检查是否点击在裁剪框内
                display_x = self.crop_rect[0] * self.zoom_factor + self.image_offset[0]
                display_y = self.crop_rect[1] * self.zoom_factor + self.image_offset[1]
                display_w = self.crop_rect[2] * self.zoom_factor
                display_h = self.crop_rect[3] * self.zoom_factor

                crop_rect_display = QRect(int(display_x), int(display_y), int(display_w), int(display_h))

                if crop_rect_display.contains(event.pos()):
                    self.image_dragging = False
                    self.rect_dragging = True
                    self.drag_start = event.pos()
                    return

            # 点击在裁剪框外或裁剪框关闭 - 开始拖拽图像
            self.image_dragging = True
            self.rect_dragging = True
            self.drag_start = event.pos()


    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖动裁剪框"""
        if self.original_image is not None:
            if self.image_dragging and self.drag_start:
                dx = event.x() - self.drag_start.x()
                dy = event.y() - self.drag_start.y()

                # 更新图像位置
                x_bund_min = min(0, self.size().width() - self.display_image.shape[1])
                x_bund_max = max(0, self.size().width() - self.display_image.shape[1])
                y_bund_min = min(0, self.size().height() - self.display_image.shape[0])
                y_bund_max = max(0, self.size().height() - self.display_image.shape[0])
                new_offset_x = np.clip(self.image_offset[0] + dx, x_bund_min, x_bund_max)
                new_offset_y = np.clip(self.image_offset[1] + dy, y_bund_min, y_bund_max)

                self.image_offset[0] = new_offset_x
                self.image_offset[1] = new_offset_y
                self.drag_start = event.pos()

                self.mov_sync.emit(self.image_offset)
                self.update()  # 触发重绘

            if self.rect_dragging and self.drag_start and self.show_crop_rect:
                # 计算移动距离（原始图像坐标系）
                dx = event.x() - self.drag_start.x()
                dy = event.y() - self.drag_start.y()

                dx_original = int(dx / self.zoom_factor)
                dy_original = int(dy / self.zoom_factor)

                # 更新裁剪矩形位置
                new_x = max(0, self.crop_rect[0] + dx_original)
                new_y = max(0, self.crop_rect[1] + dy_original)

                # 确保在边界内
                if self.original_image is not None:
                    new_x = min(new_x, self.original_image.shape[1] - self.crop_rect[2])
                    new_y = min(new_y, self.original_image.shape[0] - self.crop_rect[3])

                self.crop_rect[0] = new_x
                self.crop_rect[1] = new_y

                self.drag_start = event.pos()
                self.crop_rect_sync.emit(self.crop_rect)
                self.update()


    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.image_dragging = False
            self.rect_dragging = False
            self.drag_start = None


class ClickableSlider(QSlider):
    def __init__(self, orientation=Qt.Horizontal):
        super().__init__(orientation)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            value = self._pixel_pos_to_range_value(event.pos())
            self.setValue(value)
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            value = self._pixel_pos_to_range_value(event.pos())
            self.setValue(value)
            event.accept()
        super().mouseMoveEvent(event)

    def _pixel_pos_to_range_value(self, pos):
        if self.orientation() == Qt.Horizontal:
            pos_value = pos.x()
            slider_length = self.width()
        else:
            pos_value = pos.y()
            slider_length = self.height()

        value = (pos_value / slider_length) * (self.maximum() - self.minimum()) + self.minimum()
        value = max(self.minimum(), min(self.maximum(), int(value)))
        return value

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Canvas()
    window.show()
    sys.exit(app.exec_())