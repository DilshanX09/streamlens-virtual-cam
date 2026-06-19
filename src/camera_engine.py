import cv2
import numpy as np
import pyvirtualcam
from PyQt6.QtCore import QThread, pyqtSignal
from src.state_manager import AppSettings

class CameraEngine(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    error_occurred = pyqtSignal(str)

    def __init__(self, settings: AppSettings):
        super().__init__()
        self.settings = settings
        self._run_flag = True
        self.cap = None

    def run(self):
        try:
            # Use DSHOW for high FPS on Windows
            self.cap = cv2.VideoCapture(self.settings.camera_index, cv2.CAP_DSHOW)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.settings.fps)

            # Check if camera opened successfully
            if not self.cap.isOpened():
                self.error_occurred.emit("Could not open camera.")
                return

            with pyvirtualcam.Camera(width=self.settings.width, height=self.settings.height, fps=self.settings.fps) as cam:
                print(f'Virtual camera started: {cam.device}')
                while self._run_flag:
                    ret, frame = self.cap.read()
                    if not ret:
                        self.error_occurred.emit("Failed to capture frame.")
                        break

                    # Apply Transformations
                    processed_frame = self._process_frame(frame)

                    # Send to Virtual Camera (pyvirtualcam expects RGB)
                    rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                    cam.send(rgb_frame)
                    cam.sleep_until_next_frame()

                    # Emit for UI preview
                    self.frame_ready.emit(processed_frame)

        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            if self.cap:
                self.cap.release()

    def _process_frame(self, frame):
        # 1. Zoom
        if self.settings.zoom_level != 1.0:
            h, w = frame.shape[:2]
            new_h, new_w = int(h / self.settings.zoom_level), int(w / self.settings.zoom_level)
            start_h = (h - new_h) // 2
            start_w = (w - new_w) // 2
            frame = frame[start_h:start_h + new_h, start_w:start_w + new_w]
            frame = cv2.resize(frame, (self.settings.width, self.settings.height))

        # 2. Flips
        if self.settings.flip_horizontal:
            frame = cv2.flip(frame, 1)
        if self.settings.flip_vertical:
            frame = cv2.flip(frame, 0)

        # 3. Brightness/Contrast
        if self.settings.brightness != 0 or self.settings.contrast != 0:
            alpha = 1.0 + (self.settings.contrast / 100.0)
            beta = self.settings.brightness
            frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

        # 4. Saturation
        if self.settings.saturation != 0:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            alpha = 1.0 + (self.settings.saturation / 100.0)
            s = cv2.convertScaleAbs(s, alpha=alpha, beta=0)
            hsv = cv2.merge([h, s, v])
            frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        return frame

    def stop(self):
        self._run_flag = False
        self.wait()
