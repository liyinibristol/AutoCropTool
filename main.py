import sys
import os
import numpy as np
import cv2
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QLabel, QPushButton, QFileDialog, QSlider,
                             QMessageBox, QScrollArea, QGridLayout, QGroupBox, QLineEdit)

from ImgWidget import *
from map_method import *

class ImageCropper(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ImageCropPro - 4-Window Analysis Tool")
        self.setGeometry(200, 0, 2000, 1200)

        # 图像属性
        self.noisy_image_path = None
        self.gt_image_path = None
        self.noisy_image = None
        self.gt_image = None
        self.original_noisy = None
        self.original_gt = None
        self.save_folder = os.getcwd()
        self.noisy_img_folder = os.getcwd()
        self.GT_img_folder = os.getcwd()
        self.noisy_img_num = 0
        self.gt_img_num = 0
        self.frm_idx = 0
        self.display_frm_num = 0

        # 裁剪属性
        self.crop_rect = [0, 0, 1920, 1080]
        self.zoom_factor = 1.0

        # 创建四个图像窗口实例
        self.setup_image_windows()

        # UI 设置
        self.setup_ui()

    def setup_image_windows(self):
        """创建和配置四个图像显示窗口"""
        # 左上：噪声图像（显示裁剪框）
        self.noisy_display = Canvas("Noisy Image", show_crop_rect=True)
        self.noisy_display.crop_rect_sync.connect(self.update_crop_rect)
        self.noisy_display.zoom_sync.connect(self.update_zoom)
        self.noisy_display.mov_sync.connect(self.update_offset)

        # 右上：真实值图像（显示裁剪框）
        self.gt_display = Canvas("Ground Truth Image", show_crop_rect=True)
        self.gt_display.crop_rect_sync.connect(self.update_crop_rect)
        self.gt_display.zoom_sync.connect(self.update_zoom)
        self.gt_display.mov_sync.connect(self.update_offset)

        # 左下：重叠图像（不显示裁剪框）
        self.overlay_display = Canvas("Overlay Image", show_crop_rect=False)
        self.overlay_display.zoom_sync.connect(self.update_zoom)
        self.overlay_display.mov_sync.connect(self.update_offset)

        # 右下：映射图像（不显示裁剪框）
        self.mapped_display = Canvas("Mapped Overlay Image", show_crop_rect=False)
        self.mapped_display.zoom_sync.connect(self.update_zoom)
        self.mapped_display.mov_sync.connect(self.update_offset)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 顶部：图像区域和控制面板（水平排列）
        content_layout = QHBoxLayout()

        # 左侧：2x2 网格布局
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)

        # 左上：噪声图像
        noisy_group = self.create_display_group("Noisy Image", self.noisy_display)
        grid_layout.addWidget(noisy_group, 0, 0)

        # 右上：真实值图像
        gt_group = self.create_display_group("Ground Truth Image", self.gt_display)
        grid_layout.addWidget(gt_group, 0, 1)

        # 左下：重叠图像
        overlay_group = self.create_display_group("Overlay Image", self.overlay_display)
        grid_layout.addWidget(overlay_group, 1, 0)

        # 右下：映射图像
        mapped_group = self.create_display_group("Mapped Overlay Image", self.mapped_display)
        grid_layout.addWidget(mapped_group, 1, 1)

        content_layout.addWidget(grid_widget, 4)  # 图像区域占4/5宽度

        # 右侧：控制面板
        control_panel = self.setup_control_panel()
        content_layout.addWidget(control_panel, 1)  # 控制面板占1/5宽度

        # 将水平布局添加到主垂直布局
        main_layout.addLayout(content_layout)

        # 底部：Slider Bar - 现在应该在整个窗口底部
        self.setup_bottom_slider_bar(main_layout)

    def setup_bottom_slider_bar(self, main_layout):
        """在底部添加Slider控制栏"""
        slider_group = QGroupBox()
        slider_layout = QHBoxLayout(slider_group)

        # 添加标签
        slider_layout.addWidget(QLabel("Frame:"))

        # 主Slider
        self.frame_slider = ClickableSlider(Qt.Horizontal)
        self.frame_slider.setRange(0, 0)
        self.frame_slider.setValue(0)
        self.frame_slider.valueChanged.connect(self.on_frame_slider_changed)
        slider_layout.addWidget(self.frame_slider)
        self.frame_slider.setPageStep(100)

        self.curr_frm_idx_edit = QLineEdit()
        positive_int_validator = QRegExpValidator(QRegExp("[0-9]*"))
        self.curr_frm_idx_edit.setValidator(positive_int_validator)
        self.curr_frm_idx_edit.setText("0")
        self.curr_frm_idx_edit.setMaximumWidth(100)
        self.curr_frm_idx_edit.setStyleSheet("""
                                QLineEdit {
                                    background-color: #f8f8f8;
                                    border: 1px solid #ccc;
                                    padding: 5px;
                                    border-radius: 3px;
                                }
                            """)
        slider_layout.addWidget(self.curr_frm_idx_edit)

        # 当前帧显示
        self.frame_label = QLabel("/0")
        self.frame_label.setMinimumWidth(80)
        slider_layout.addWidget(self.frame_label)

        # 播放控制按钮
        self.btn_play = QPushButton("Set Frame")
        self.btn_play.clicked.connect(self.toggle_play)
        slider_layout.addWidget(self.btn_play)

        self.btn_prev = QPushButton("◀")
        self.btn_prev.clicked.connect(self.prev_frame)
        self.btn_prev.setMaximumWidth(40)
        slider_layout.addWidget(self.btn_prev)

        self.btn_next = QPushButton("▶")
        self.btn_next.clicked.connect(self.next_frame)
        self.btn_next.setMaximumWidth(40)
        slider_layout.addWidget(self.btn_next)

        main_layout.addWidget(slider_group)  # Slider栏占1/5高度

    def on_frame_slider_changed(self, value):
        # if value != self.frm_idx:
        self.frm_idx = value
        self.curr_frm_idx_edit.setText(str(self.frm_idx))
        self.noisy_display.set_image_via_idx(self.frm_idx)
        self.gt_display.set_image_via_idx(self.frm_idx)
        self.noisy_image = self.noisy_display.original_image
        self.gt_image = self.gt_display.original_image
        self.update_overlay()


    def toggle_play(self):
        input_idx = int(self.curr_frm_idx_edit.text())

        if input_idx >= self.display_frm_num:
            self.frame_slider.setValue(self.display_frm_num - 1)
            self.curr_frm_idx_edit.setText(str(self.display_frm_num - 1))

        else:
            self.frame_slider.setValue(input_idx)


    def prev_frame(self):
        """上一帧"""
        current_value = self.frame_slider.value()
        if current_value > 0:
            self.frame_slider.setValue(current_value - 1)

    def next_frame(self):
        """下一帧"""
        current_value = self.frame_slider.value()
        if current_value < self.frame_slider.maximum():
            self.frame_slider.setValue(current_value + 1)

    def create_display_group(self, title, display_widget):
        """创建带标题的图像显示组"""
        group = QGroupBox(title)
        layout = QVBoxLayout(group)

        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(display_widget)

        layout.addWidget(scroll)
        return group

    def setup_control_panel(self):
        """设置右侧控制面板"""
        control_panel = QWidget()
        # control_panel.setMaximumWidth(350)
        layout = QVBoxLayout(control_panel)

        # Load Noisy Img folder
        noisy_folder_group = QGroupBox("Load Noisy Img Folder")
        noisy_folder_layout = QHBoxLayout(noisy_folder_group)

        # Noisy Img folder
        self.noisy_folder_path_edit = QLineEdit()
        self.noisy_folder_path_edit.setText(self.noisy_img_folder)
        self.noisy_folder_path_edit.setReadOnly(True)  # 只读，只能通过按钮选择
        self.noisy_folder_path_edit.setStyleSheet("""
                        QLineEdit {
                            background-color: #f8f8f8;
                            border: 1px solid #ccc;
                            padding: 5px;
                            border-radius: 3px;
                        }
                    """)
        noisy_folder_layout.addWidget(self.noisy_folder_path_edit)

        # 选择文件夹按钮
        self.btn_load_noisy = QPushButton("...")
        self.btn_load_noisy.setToolTip("Select Save Folder")
        self.btn_load_noisy.setMaximumWidth(30)
        self.btn_load_noisy.clicked.connect(self.load_noisy_image)
        noisy_folder_layout.addWidget(self.btn_load_noisy)

        layout.addWidget(noisy_folder_group)

        # Load GT Img folder
        GT_folder_group = QGroupBox("Load GT Img Folder")
        GT_folder_layout = QHBoxLayout(GT_folder_group)

        # GT Img folder
        self.GT_folder_path_edit = QLineEdit()
        self.GT_folder_path_edit.setText(self.GT_img_folder)
        self.GT_folder_path_edit.setReadOnly(True)  # 只读，只能通过按钮选择
        self.GT_folder_path_edit.setStyleSheet("""
                                QLineEdit {
                                    background-color: #f8f8f8;
                                    border: 1px solid #ccc;
                                    padding: 5px;
                                    border-radius: 3px;
                                }
                            """)
        GT_folder_layout.addWidget(self.GT_folder_path_edit)

        # 选择文件夹按钮
        self.btn_load_gt = QPushButton("...")
        self.btn_load_gt.setToolTip("Select Save Folder")
        self.btn_load_gt.setMaximumWidth(30)
        self.btn_load_gt.clicked.connect(self.load_gt_image)
        GT_folder_layout.addWidget(self.btn_load_gt)

        layout.addWidget(GT_folder_group)

        # 保存文件夹选择 - 水平布局
        save_group = QGroupBox("Save Folder")
        folder_selection_layout = QHBoxLayout(save_group)

        # 路径显示框（长条对话框）
        self.folder_path_edit = QLineEdit()
        self.folder_path_edit.setText(self.save_folder)
        self.folder_path_edit.setReadOnly(True)  # 只读，只能通过按钮选择
        self.folder_path_edit.setStyleSheet("""
                QLineEdit {
                    background-color: #f8f8f8;
                    border: 1px solid #ccc;
                    padding: 5px;
                    border-radius: 3px;
                }
            """)
        folder_selection_layout.addWidget(self.folder_path_edit)

        # 选择文件夹按钮
        self.btn_select_folder = QPushButton("...")
        self.btn_select_folder.setToolTip("Select Save Folder")
        self.btn_select_folder.setMaximumWidth(30)
        self.btn_select_folder.clicked.connect(self.select_save_folder)
        folder_selection_layout.addWidget(self.btn_select_folder)

        layout.addWidget(save_group)

        # 缩放控制组
        zoom_group = QGroupBox("Zoom Controls")
        zoom_layout = QVBoxLayout(zoom_group)

        zoom_info = QHBoxLayout()
        zoom_info.addWidget(QLabel("Zoom Level:"))
        self.zoom_label = QLabel("100%")
        zoom_info.addWidget(self.zoom_label)
        zoom_layout.addLayout(zoom_info)

        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 500)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.zoom_slider_changed)
        zoom_layout.addWidget(self.zoom_slider)

        self.btn_reset_zoom = QPushButton("Reset Zoom to 100%")
        self.btn_reset_zoom.clicked.connect(self.reset_zoom)
        zoom_layout.addWidget(self.btn_reset_zoom)

        layout.addWidget(zoom_group)

        # 重叠控制组
        overlay_group = QGroupBox("Overlay Controls")
        overlay_layout = QVBoxLayout(overlay_group)

        overlay_info = QHBoxLayout()
        overlay_info.addWidget(QLabel("Transparency:"))
        self.alpha_label = QLabel("50%")
        overlay_info.addWidget(self.alpha_label)
        overlay_layout.addLayout(overlay_info)

        self.overlay_alpha_slider = QSlider(Qt.Horizontal)
        self.overlay_alpha_slider.setRange(0, 100)
        self.overlay_alpha_slider.setValue(50)
        self.overlay_alpha_slider.valueChanged.connect(self.update_overlay)
        overlay_layout.addWidget(self.overlay_alpha_slider)

        layout.addWidget(overlay_group)

        # 映射控制组
        mapping_group = QGroupBox("Mapping Controls")
        mapping_layout = QVBoxLayout(mapping_group)

        self.btn_apply_mapping = QPushButton("Apply Mapping")
        self.btn_apply_mapping.clicked.connect(self.apply_mapping)
        self.btn_apply_mapping.setEnabled(False)
        mapping_layout.addWidget(self.btn_apply_mapping)

        # self.mapping_info = QLabel("Current: Simple Overlay")
        # self.mapping_info.setWordWrap(True)
        # mapping_layout.addWidget(self.mapping_info)

        layout.addWidget(mapping_group)

        # 裁剪控制组
        crop_group = QGroupBox("Crop Controls")
        crop_layout = QVBoxLayout(crop_group)

        # crop_info = QLabel("Drag the red HD box to select crop area")
        # crop_info.setWordWrap(True)
        # crop_layout.addWidget(crop_info)

        self.btn_crop = QPushButton("Crop All Images")
        self.btn_crop.clicked.connect(self.crop_images)
        self.btn_crop.setEnabled(False)
        crop_layout.addWidget(self.btn_crop)

        layout.addWidget(crop_group)

        # 状态组
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        self.status_label = QLabel("Please load noisy and ground truth images")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        layout.addWidget(status_group)

        layout.addStretch()
        return control_panel

    def select_save_folder(self):
        """选择保存文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Save Folder",
            self.save_folder,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        if folder:
            self.save_folder = folder
            self.folder_path_edit.setText(self.save_folder)
            self.status_label.setText(f"Save folder set to: {self.save_folder}")

    def load_noisy_image(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Load Noisy Img Folder",
            self.noisy_img_folder,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        try:
            self.noisy_img_folder = folder
            self.noisy_folder_path_edit.setText(self.noisy_img_folder)
            self.noisy_img_num = self.noisy_display.init_img_folder(self.noisy_img_folder)
            self.status_label.setText(f"Load {self.noisy_img_num} noisy img from folder: {self.noisy_img_folder}")
            self.noisy_image = self.noisy_display.original_image
            self.update_overlay()
            self.update_frm_slider()
        except:
            QMessageBox.critical(self, "Error", "Failed to load noisy image")

    def load_gt_image(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Load GT Img Folder",
            self.GT_img_folder,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )

        try:
            self.GT_img_folder = folder
            self.GT_folder_path_edit.setText(self.GT_img_folder)
            self.gt_img_num = self.gt_display.init_img_folder(self.GT_img_folder)
            self.status_label.setText(f"Load {self.gt_img_num} noisy img from folder: {self.GT_img_folder}")
            self.gt_image = self.gt_display.original_image
            self.update_overlay()
            self.update_frm_slider()
        except:
            QMessageBox.critical(self, "Error", "Failed to load GT image")

    # def initialize_images(self, window, in_img):
    #     """初始化所有图像显示"""
    #     try:
    #         # 初始化裁剪区域
    #         # height, width = in_img.shape[:2]
    #         # hd_width, hd_height = 1920, 1080
    #         # x = (width - hd_width) // 2
    #         # y = (height - hd_height) // 2
    #         # self.crop_rect = [x, y, hd_width, hd_height]
    #
    #         # 设置图像到各个窗口
    #         window.set_image(in_img)
    #         window.set_crop_rect(self.crop_rect)
    #
    #         self.status_label.setText("Images loaded successfully!")
    #
    #     except Exception as e:
    #         QMessageBox.critical(self, "Error", f"Failed to initialize images: {str(e)}")

    def update_frm_slider(self):
        self.frm_idx = 0
        self.display_frm_num = min(self.noisy_img_num, self.gt_img_num)
        self.curr_frm_idx_edit.setText(f"{self.frm_idx}")
        self.frame_label.setText(f"/{max(self.display_frm_num-1,0)}")
        self.frame_slider.setRange(0, max(self.display_frm_num-1,0))
        self.frame_slider.setValue(self.frm_idx)

    def update_overlay(self):
        """更新重叠图像显示"""
        if self.noisy_image is not None and self.gt_image is not None:
            alpha = self.overlay_alpha_slider.value() / 100.0
            self.alpha_label.setText(f"{self.overlay_alpha_slider.value()}%")

            # 创建重叠图像
            overlay_image = self.create_overlay_image(alpha)
            self.overlay_display.set_image(overlay_image)

        if self.noisy_display.show_crop_rect and self.gt_display.show_crop_rect is True:
            # 启用按钮
            self.btn_crop.setEnabled(True)
            self.btn_apply_mapping.setEnabled(True)

    def create_overlay_image(self, alpha):
        """创建重叠图像 - 在(0,0)处对齐，不调整尺寸"""
        h1, w1 = self.noisy_image.shape[:2]
        h2, w2 = self.gt_image.shape[:2]

        # 取较大的尺寸作为画布大小
        canvas_height = max(h1, h2)
        canvas_width = max(w1, w2)

        # 创建画布
        overlay = np.zeros((canvas_height, canvas_width, 3), dtype=np.float64)

        # 分别叠加两张图像
        overlay[:h1, :w1] += self.noisy_image * alpha
        overlay[:h2, :w2] += self.gt_image * (1 - alpha)

        return overlay.astype(np.uint8)

    def apply_mapping(self):
        if self.noisy_image is not None and self.gt_image is not None:
            try:
                # 创建映射后的图像
                mapped_image = self.create_mapped_image()
                self.mapped_display.set_image(mapped_image)
                self.status_label.setText("Mapping applied successfully!")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to apply mapping: {str(e)}")

    def create_mapped_image(self):
        """创建映射图像（占位符）"""
        x, y, w, h = self.crop_rect
        src = self.noisy_image[y:y + h, x:x + w]
        dst = self.gt_image[y:y + h, x:x + w]

        mtx = mapping_feature_pts(src, dst)

        # Coordinate scaling
        h_org, w_org = self.noisy_image.shape[:2]
        # scale_h = h_org / (h)
        # scale_w = w_org / (w)
        S = np.array([
            [1, 0, x],
            [0, 1, y],
            [0, 0, 1]
        ])
        # 构建逆缩放矩阵
        S_inv = np.array([
            [1, 0, -x],
            [0, 1, -y],
            [0, 0, 1]
        ])
        mtx_scale = S @ mtx @ S_inv
        # mtx_scale = mtx

        warpped_gt_image = cv2.warpPerspective(self.gt_image, mtx_scale, (w_org, h_org))

        alpha = self.overlay_alpha_slider.value() / 100.0

        h1, w1 = self.noisy_image.shape[:2]
        h2, w2 = self.gt_image.shape[:2]

        if h1 != h2 or w1 != w2:
            min_h, min_w = min(h1, h2), min(w1, w2)
            noisy_resized = cv2.resize(self.noisy_image, (min_w, min_h))
            warpped_gt_image = cv2.resize(warpped_gt_image, (min_w, min_h))
        else:
            noisy_resized = self.noisy_image
            warpped_gt_image = warpped_gt_image

        mapped = cv2.addWeighted(noisy_resized, alpha, warpped_gt_image, 1 - alpha, 0)
        return mapped

    def update_crop_rect(self, rect):
        """更新裁剪区域"""
        self.crop_rect = rect
        self.noisy_display.set_crop_rect(rect)
        self.gt_display.set_crop_rect(rect)

    def update_offset(self, offset):
        self.noisy_display.set_offset(offset)
        self.gt_display.set_offset(offset)
        self.overlay_display.set_offset(offset)
        self.mapped_display.set_offset(offset)

    def update_zoom(self, zoom_factor):
        self.zoom_factor = zoom_factor
        self.zoom_slider.setValue(int(self.zoom_factor * 100))

    def zoom_slider_changed(self, value):
        """缩放滑块变化"""
        self.zoom_factor = value / 100.0
        self.zoom_label.setText(f"{value}%")
        self.apply_zoom_to_all()

    def reset_zoom(self):
        """重置缩放"""
        self.zoom_slider.setValue(100)

    def apply_zoom_to_all(self):
        """应用缩放到所有窗口"""
        self.noisy_display.set_zoom(self.zoom_factor)
        self.gt_display.set_zoom(self.zoom_factor)
        self.overlay_display.set_zoom(self.zoom_factor)
        self.mapped_display.set_zoom(self.zoom_factor)

    def crop_images(self):
        # """裁剪所有图像"""
        # if self.noisy_image is None or self.gt_image is None:
        #     return
        #
        # try:
        #     x, y, w, h = self.crop_rect
        #
        #     # 裁剪图像
        #     noisy_cropped = self.noisy_image[y:y + h, x:x + w]
        #     gt_cropped = self.gt_image[y:y + h, x:x + w]
        #
        #     # 保存图像
        #     noisy_output = self.get_output_path(self.noisy_image_path, "cropped")
        #     gt_output = self.get_output_path(self.gt_image_path, "cropped")
        #
        #     noisy_cropped_bgr = cv2.cvtColor(noisy_cropped, cv2.COLOR_RGB2BGR)
        #     gt_cropped_bgr = cv2.cvtColor(gt_cropped, cv2.COLOR_RGB2BGR)
        #
        #     cv2.imwrite(noisy_output, noisy_cropped_bgr)
        #     cv2.imwrite(gt_output, gt_cropped_bgr)
        #
        #     QMessageBox.information(self, "Success",
        #                             f"Images cropped successfully!\nOutput size: {w}x{h}")
        #
        # except Exception as e:
        #     QMessageBox.critical(self, "Error", f"Failed to crop images: {str(e)}")
        print("frm_idx:", self.frm_idx)

    def get_output_path(self, input_path, suffix):
        """生成输出路径"""
        dir_name = os.path.dirname(input_path)
        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        return os.path.join(dir_name, f"{name}_{suffix}{ext}")




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageCropper()
    window.show()
    sys.exit(app.exec_())