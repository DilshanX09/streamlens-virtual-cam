import cv2
import numpy as np
import pyvirtualcam
import threading
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from src.state_manager import AppSettings


class CameraEngine(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)

    def __init__(self, settings: AppSettings):
        super().__init__()
        self.settings = settings
        self._run_flag = True
        self.cap = None
        self.lock = threading.Lock()  # Protect settings reads and writes across threads

        # Pre-allocate processing buffers
        self.output_size = (self.settings.width, self.settings.height)
        self.rgb_buffer = np.zeros(
            (self.settings.height, self.settings.width, 3), dtype=np.uint8
        )

    @pyqtSlot(str, object)
    def update_setting(self, key: str, value: object):
        """Thread-safe slot to dynamically update setting attributes from the UI thread."""
        with self.lock:
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)


    def run(self):
        try:
            # Hardware Initialization: Exactly once in the background worker
            # Use DSHOW for high FPS and low latency on Windows
            self.cap = cv2.VideoCapture(self.settings.camera_index, cv2.CAP_DSHOW)

            # Optimization: Set properties once
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.settings.fps)

            if not self.cap.isOpened():
                self.error_occurred.emit(
                    f"Could not open camera {self.settings.camera_index}"
                )
                return

            # Virtual Camera Initialization: Use defaults to safely pick up available driver (OBS, etc.)
            with pyvirtualcam.Camera(
                width=self.settings.width,
                height=self.settings.height,
                fps=self.settings.fps,
            ) as cam:
                print(f"Virtual Camera Active: {cam.device}")

                while self._run_flag:
                    ret, frame = self.cap.read()
                    if not ret:
                        self.error_occurred.emit("Failed to capture frame.")
                        break

                    # 1. Processing Pipeline
                    processed_frame = self._process_frame(frame)

                    # 2. Virtual Camera Output (Optimized buffer reuse)
                    cv2.cvtColor(
                        processed_frame, cv2.COLOR_BGR2RGB, dst=self.rgb_buffer
                    )
                    cam.send(self.rgb_buffer)
                    cam.sleep_until_next_frame()

                    # 3. UI Notification
                    self.frame_ready.emit(processed_frame)

        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            if self.cap:
                self.cap.release()
                self.cap = None

    def _process_frame(self, frame):
        # Optimized processing pipeline
        
        # Read settings variables thread-safely
        with self.lock:
            zoom_level = self.settings.zoom_level
            flip_horizontal = self.settings.flip_horizontal
            flip_vertical = self.settings.flip_vertical
            brightness = self.settings.brightness
            contrast = self.settings.contrast
            saturation = self.settings.saturation

        # 1. Zoom (Only resize if necessary)
        if abs(zoom_level - 1.0) > 0.01:
            h, w = frame.shape[:2]
            new_h, new_w = int(h / zoom_level), int(w / zoom_level)
            start_h = (h - new_h) // 2
            start_w = (w - new_w) // 2
            frame = frame[start_h : start_h + new_h, start_w : start_w + new_w]
            frame = cv2.resize(frame, self.output_size, interpolation=cv2.INTER_LINEAR)

        # 2. Flips
        if flip_horizontal and flip_vertical:
            frame = cv2.flip(frame, -1)
        elif flip_horizontal:
            frame = cv2.flip(frame, 1)
        elif flip_vertical:
            frame = cv2.flip(frame, 0)

        # 3. Brightness/Contrast/Saturation Optimization
        # Use convertScaleAbs for combined brightness and contrast
        if brightness != 0 or contrast != 0:
            alpha = 1.0 + (contrast / 100.0)
            beta = brightness
            frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

        # 4. Saturation (HSV space)
        if saturation != 0:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            # In-place modification of saturation channel
            s_channel = hsv[:, :, 1].astype(np.float32)
            s_channel *= 1.0 + (saturation / 100.0)
            hsv[:, :, 1] = np.clip(s_channel, 0, 255).astype(np.uint8)
            frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        return frame

    def stop(self):
        self._run_flag = False
        self.wait()
