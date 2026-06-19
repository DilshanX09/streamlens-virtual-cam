import sys
import numpy as np
import cv2
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSlider, QCheckBox, QComboBox, QGroupBox, 
    QFormLayout, QScrollArea, QGraphicsDropShadowEffect, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QPoint, pyqtSlot, QSize
from PyQt6.QtGui import QImage, QPixmap, QColor, QIcon, QMouseEvent

from src.state_manager import StateManager
from src.camera_engine import CameraEngine

class CustomTitleBar(QWidget):
    """Custom frameless window title bar supporting dragging and window control."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 10, 0)
        layout.setSpacing(10)
        
        # Logo and Title
        self.title_label = QLabel("StreamLens - Virtual Camera")
        self.title_label.setStyleSheet("color: #E2E8F0; font-weight: bold; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px;")
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        # Minimize Button
        self.btn_minimize = QPushButton("—")
        self.btn_minimize.setFixedSize(28, 28)
        self.btn_minimize.setStyleSheet(self._button_style("#4A5568", "#2D3748"))
        self.btn_minimize.clicked.connect(self.parent.showMinimized)
        layout.addWidget(self.btn_minimize)
        
        # Close Button
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.setStyleSheet(self._button_style("#E53E3E", "#C53030"))
        self.btn_close.clicked.connect(self.parent.close)
        layout.addWidget(self.btn_close)
        
        # Dragging variables
        self.drag_position = QPoint()

    def _button_style(self, hover_color, press_color):
        return f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
                color: #A0AEC0;
                font-family: Arial, sans-serif;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                color: white;
            }}
            QPushButton:pressed {{
                background-color: {press_color};
            }}
        """

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.parent.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()


class StreamLensUI(QMainWindow):
    def __init__(self, state_manager: StateManager):
        super().__init__()
        self.state_manager = state_manager
        self.settings = state_manager.settings
        self.engine = None
        
        # Setup window behavior
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowSystemMenuHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Window size
        self.resize(1100, 720)
        self.setMinimumSize(950, 600)
        
        # Central widget and layout
        self.central_widget = QWidget(self)
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)
        
        # Stylized wrapper to achieve rounded corners and drop shadow
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(10, 10, 10, 10)
        
        self.main_container = QWidget(self.central_widget)
        self.main_container.setObjectName("MainContainer")
        self.main_container.setStyleSheet("""
            QWidget#MainContainer {
                background-color: #1A202C;
                border: 1px solid #2D3748;
                border-radius: 12px;
            }
        """)
        
        # Add drop shadow to main container
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 4)
        self.main_container.setGraphicsEffect(shadow)
        
        self.central_layout.addWidget(self.main_container)
        
        # Inner layout of main container
        self.container_layout = QVBoxLayout(self.main_container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        
        # Add Custom Title Bar
        self.title_bar = CustomTitleBar(self)
        self.container_layout.addWidget(self.title_bar)
        
        # Content Layout (Preview + Sidebar)
        self.content_widget = QWidget(self.main_container)
        self.content_layout = QHBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(15, 10, 15, 15)
        self.content_layout.setSpacing(15)
        self.container_layout.addWidget(self.content_widget)
        
        # 1. Preview Layout (Left)
        self.preview_container = QFrame()
        self.preview_container.setStyleSheet("""
            QFrame {
                background-color: #0F172A;
                border: 2px solid #2D3748;
                border-radius: 8px;
            }
        """)
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_label = QLabel("Camera Stream Inactive")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("color: #718096; font-size: 16px; font-family: 'Segoe UI', sans-serif;")
        self.preview_layout.addWidget(self.preview_label)
        self.content_layout.addWidget(self.preview_container, stretch=3)
        
        # 2. Sidebar Layout (Right)
        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #2D3748;
                width: 8px;
                margin: 0px 0px 0px 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #4A5568;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setObjectName("Sidebar")
        self.sidebar_widget.setStyleSheet("""
            QWidget#Sidebar {
                background-color: #1A202C;
            }
            QGroupBox {
                border: 1px solid #2D3748;
                border-radius: 8px;
                margin-top: 15px;
                font-weight: bold;
                font-size: 12px;
                color: #CBD5E0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLabel {
                color: #A0AEC0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #2D3748;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #3182CE;
                width: 14px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #4299E1;
            }
            QCheckBox {
                color: #A0AEC0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #4A5568;
                background-color: #2D3748;
            }
            QCheckBox::indicator:checked {
                background-color: #3182CE;
                border-color: #3182CE;
            }
            QComboBox {
                background-color: #2D3748;
                border: 1px solid #4A5568;
                border-radius: 4px;
                padding: 5px;
                color: #E2E8F0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox::drop-down {
                border: none;
            }
            QPushButton#ActionBtn {
                background-color: #3182CE;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }
            QPushButton#ActionBtn:hover {
                background-color: #4299E1;
            }
            QPushButton#ActionBtn:pressed {
                background-color: #2B6CB0;
            }
            QPushButton#DangerBtn {
                background-color: #E53E3E;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }
            QPushButton#DangerBtn:hover {
                background-color: #FC8181;
            }
            QPushButton#DangerBtn:pressed {
                background-color: #C53030;
            }
        """)
        
        self.sidebar_layout = QVBoxLayout(self.sidebar_widget)
        self.sidebar_layout.setContentsMargins(0, 0, 5, 0)
        self.sidebar_layout.setSpacing(15)
        
        # 2a. Group: Device Settings
        self.gp_device = QGroupBox("Camera Device")
        self.gp_device_layout = QFormLayout(self.gp_device)
        self.gp_device_layout.setContentsMargins(10, 20, 10, 10)
        
        self.cb_camera = QComboBox()
        self._populate_camera_list()
        self.cb_camera.currentIndexChanged.connect(self._on_camera_changed)
        self.gp_device_layout.addRow(QLabel("Camera Device:"), self.cb_camera)
        
        self.sidebar_layout.addWidget(self.gp_device)
        
        # 2b. Group: Transformations
        self.gp_transform = QGroupBox("Transformations")
        self.gp_transform_layout = QVBoxLayout(self.gp_transform)
        self.gp_transform_layout.setContentsMargins(10, 20, 10, 10)
        self.gp_transform_layout.setSpacing(12)
        
        self.chk_flip_h = QCheckBox("Flip Horizontal (Mirror)")
        self.chk_flip_h.setChecked(self.settings.flip_horizontal)
        self.chk_flip_h.stateChanged.connect(self._on_flip_h_changed)
        self.gp_transform_layout.addWidget(self.chk_flip_h)
        
        self.chk_flip_v = QCheckBox("Flip Vertical")
        self.chk_flip_v.setChecked(self.settings.flip_vertical)
        self.chk_flip_v.stateChanged.connect(self._on_flip_v_changed)
        self.gp_transform_layout.addWidget(self.chk_flip_v)
        
        # Zoom Slider
        zoom_hbox = QHBoxLayout()
        self.lbl_zoom_val = QLabel(f"{self.settings.zoom_level:.1f}x")
        self.lbl_zoom_val.setFixedWidth(30)
        self.slider_zoom = QSlider(Qt.Orientation.Horizontal)
        self.slider_zoom.setMinimum(10) # 1.0x
        self.slider_zoom.setMaximum(30) # 3.0x
        self.slider_zoom.setValue(int(self.settings.zoom_level * 10))
        self.slider_zoom.valueChanged.connect(self._on_zoom_changed)
        zoom_hbox.addWidget(self.slider_zoom)
        zoom_hbox.addWidget(self.lbl_zoom_val)
        
        self.gp_transform_layout.addWidget(QLabel("Zoom Level:"))
        self.gp_transform_layout.addLayout(zoom_hbox)
        
        self.sidebar_layout.addWidget(self.gp_transform)
        
        # 2c. Group: Color Adjustments
        self.gp_color = QGroupBox("Color Adjustments")
        self.gp_color_layout = QVBoxLayout(self.gp_color)
        self.gp_color_layout.setContentsMargins(10, 20, 10, 10)
        self.gp_color_layout.setSpacing(12)
        
        # Brightness Slider
        bright_hbox = QHBoxLayout()
        self.lbl_bright_val = QLabel(str(self.settings.brightness))
        self.lbl_bright_val.setFixedWidth(30)
        self.slider_bright = QSlider(Qt.Orientation.Horizontal)
        self.slider_bright.setMinimum(-100)
        self.slider_bright.setMaximum(100)
        self.slider_bright.setValue(self.settings.brightness)
        self.slider_bright.valueChanged.connect(self._on_brightness_changed)
        bright_hbox.addWidget(self.slider_bright)
        bright_hbox.addWidget(self.lbl_bright_val)
        self.gp_color_layout.addWidget(QLabel("Brightness:"))
        self.gp_color_layout.addLayout(bright_hbox)
        
        # Contrast Slider
        contrast_hbox = QHBoxLayout()
        self.lbl_contrast_val = QLabel(str(self.settings.contrast))
        self.lbl_contrast_val.setFixedWidth(30)
        self.slider_contrast = QSlider(Qt.Orientation.Horizontal)
        self.slider_contrast.setMinimum(-100)
        self.slider_contrast.setMaximum(100)
        self.slider_contrast.setValue(self.settings.contrast)
        self.slider_contrast.valueChanged.connect(self._on_contrast_changed)
        contrast_hbox.addWidget(self.slider_contrast)
        contrast_hbox.addWidget(self.lbl_contrast_val)
        self.gp_color_layout.addWidget(QLabel("Contrast:"))
        self.gp_color_layout.addLayout(contrast_hbox)
        
        # Saturation Slider
        sat_hbox = QHBoxLayout()
        self.lbl_sat_val = QLabel(str(self.settings.saturation))
        self.lbl_sat_val.setFixedWidth(30)
        self.slider_sat = QSlider(Qt.Orientation.Horizontal)
        self.slider_sat.setMinimum(-100)
        self.slider_sat.setMaximum(100)
        self.slider_sat.setValue(self.settings.saturation)
        self.slider_sat.valueChanged.connect(self._on_saturation_changed)
        sat_hbox.addWidget(self.slider_sat)
        sat_hbox.addWidget(self.lbl_sat_val)
        self.gp_color_layout.addWidget(QLabel("Saturation (Hue/Sat):"))
        self.gp_color_layout.addLayout(sat_hbox)
        
        self.sidebar_layout.addWidget(self.gp_color)
        
        # Action Buttons
        self.btn_toggle_stream = QPushButton("Start Virtual Camera")
        self.btn_toggle_stream.setObjectName("ActionBtn")
        self.btn_toggle_stream.clicked.connect(self._toggle_stream)
        self.sidebar_layout.addWidget(self.btn_toggle_stream)
        
        # Reset Defaults Button
        self.btn_reset = QPushButton("Reset Controls")
        self.btn_reset.setObjectName("DangerBtn")
        self.btn_reset.clicked.connect(self._reset_controls)
        self.sidebar_layout.addWidget(self.btn_reset)
        
        self.sidebar_layout.addStretch()
        
        self.sidebar_scroll.setWidget(self.sidebar_widget)
        self.content_layout.addWidget(self.sidebar_scroll, stretch=1)

    def _populate_camera_list(self):
        # High quality auto discovery of camera indexes on Windows
        # Add a couple indexes. Standard webcam is usually 0.
        for i in range(4):
            self.cb_camera.addItem(f"Camera Device {i}", i)
        
        # Select matching camera index
        idx = self.cb_camera.findData(self.settings.camera_index)
        if idx != -1:
            self.cb_camera.setCurrentIndex(idx)

    # UI Slots
    def _on_camera_changed(self, index):
        cam_idx = self.cb_camera.currentData()
        if cam_idx is not None:
            self.state_manager.update_setting("camera_index", cam_idx)
            # Re-initialize camera engine if running
            if self.engine and self.engine.isRunning():
                self._stop_engine()
                self._start_engine()

    def _on_flip_h_changed(self, state):
        val = state == Qt.CheckState.Checked.value or state == 2
        self.state_manager.update_setting("flip_horizontal", val)

    def _on_flip_v_changed(self, state):
        val = state == Qt.CheckState.Checked.value or state == 2
        self.state_manager.update_setting("flip_vertical", val)

    def _on_zoom_changed(self, value):
        zoom_val = value / 10.0
        self.lbl_zoom_val.setText(f"{zoom_val:.1f}x")
        self.state_manager.update_setting("zoom_level", zoom_val)

    def _on_brightness_changed(self, value):
        self.lbl_bright_val.setText(str(value))
        self.state_manager.update_setting("brightness", value)

    def _on_contrast_changed(self, value):
        self.lbl_contrast_val.setText(str(value))
        self.state_manager.update_setting("contrast", value)

    def _on_saturation_changed(self, value):
        self.lbl_sat_val.setText(str(value))
        self.state_manager.update_setting("saturation", value)

    def _reset_controls(self):
        # Reset UI controls to defaults
        self.chk_flip_h.setChecked(False)
        self.chk_flip_v.setChecked(False)
        self.slider_zoom.setValue(10)
        self.slider_bright.setValue(0)
        self.slider_contrast.setValue(0)
        self.slider_sat.setValue(0)

    # Core Threading Operations
    def _toggle_stream(self):
        if self.engine and self.engine.isRunning():
            self._stop_engine()
            self.btn_toggle_stream.setText("Start Virtual Camera")
            self.btn_toggle_stream.setStyleSheet("")
            self.preview_label.setText("Camera Stream Inactive")
        else:
            self.btn_toggle_stream.setText("Stop Virtual Camera")
            self.btn_toggle_stream.setStyleSheet("background-color: #E53E3E; font-weight: bold;")
            self._start_engine()

    def _start_engine(self):
        self.preview_label.setText("Starting camera stream...")
        self.engine = CameraEngine(self.settings)
        self.engine.frame_ready.connect(self._on_frame_ready)
        self.engine.error_occurred.connect(self._on_engine_error)
        self.engine.start()

    def _stop_engine(self):
        if self.engine:
            self.engine.stop()
            self.engine.frame_ready.disconnect()
            self.engine.error_occurred.disconnect()
            self.engine = None

    @pyqtSlot(np.ndarray)
    def _on_frame_ready(self, frame):
        # High performance rendering
        # Convert BGR (OpenCV) to RGB QImage
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_BGR888)
        
        # Render image and scale keeping aspect ratio
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(
            self.preview_container.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled_pixmap)

    @pyqtSlot(str)
    def _on_engine_error(self, error_msg):
        print(f"Camera Engine Error: {error_msg}")
        self.preview_label.setText(f"Error: {error_msg}")
        self._stop_engine()
        self.btn_toggle_stream.setText("Start Virtual Camera")
        self.btn_toggle_stream.setStyleSheet("")

    def closeEvent(self, event):
        # Secure resource cleanup on close
        self._stop_engine()
        super().closeEvent(event)
