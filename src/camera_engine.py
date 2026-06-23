import cv2
import numpy as np
import pyvirtualcam
import threading
import time
from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage
from src.state_manager import AppSettings


class CameraEngine(QThread):
    frame_ready = pyqtSignal(QImage)
    error_occurred = pyqtSignal(str)

    def __init__(self, settings: AppSettings):
        super().__init__()
        self.settings = settings
        self._run_flag = True
        self.cap = None
        self.lock = threading.Lock()  # Protect settings reads and writes across threads

        # State for frame rate control and backpressure
        self.ui_ready = True
        self.preview_size = (640, 480)

        # Pre-allocate processing buffers
        self.output_size = (self.settings.width, self.settings.height)
        self.rgb_buffer = np.zeros(
            (self.settings.height, self.settings.width, 3), dtype=np.uint8
        )
        self.sat_lut = None
        self.last_sat_val = None
        self._update_sat_lut()

    def _update_sat_lut(self):
        # Assumes lock is held by caller if running, or called in init
        sat = self.settings.saturation
        self.sat_lut = np.clip(
            np.arange(256) * (1.0 + sat / 100.0), 0, 255
        ).astype(np.uint8)
        self.last_sat_val = sat

    @pyqtSlot(str, object)
    def update_setting(self, key: str, value: object):
        """Thread-safe slot to dynamically update setting attributes from the UI thread."""
        with self.lock:
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
                if key == "saturation":
                    self._update_sat_lut()

    def update_preview_size(self, width: int, height: int):
        """Update the preview size dynamically based on UI size."""
        with self.lock:
            self.preview_size = (max(16, width), max(16, height))

    def acknowledge_frame(self):
        """UI thread calls this to signal it has finished processing the last frame."""
        with self.lock:
            self.ui_ready = True

    def run(self):
        try:
            # Check run flag before initializing
            with self.lock:
                if not self._run_flag:
                    return
                # Hardware Initialization
                self.cap = cv2.VideoCapture(self.settings.camera_index, cv2.CAP_DSHOW)
                curr_w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                curr_h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                curr_fps = self.cap.get(cv2.CAP_PROP_FPS)

                if curr_w != self.settings.width:
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.width)
                if curr_h != self.settings.height:
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.height)
                if curr_fps != self.settings.fps:
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
                    # Check cap is valid under lock
                    with self.lock:
                        cap_device = self.cap

                    if cap_device is None:
                        break

                    ret, frame = cap_device.read()
                    if not ret:
                        print("[CameraEngine] Capture failed. Attempting camera recovery...")
                        # Release current cap
                        with self.lock:
                            if self.cap:
                                self.cap.release()
                                self.cap = None

                        reconnected = False
                        while self._run_flag and not reconnected:
                            # Send a black placeholder frame to virtual camera to keep connection active
                            placeholder = np.zeros((self.settings.height, self.settings.width, 3), dtype=np.uint8)
                            cv2.putText(
                                placeholder,
                                "Camera Disconnected - Retrying...",
                                (50, self.settings.height // 2),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.8,
                                (255, 255, 255),
                                2
                            )
                            cv2.cvtColor(placeholder, cv2.COLOR_BGR2RGB, dst=self.rgb_buffer)
                            cam.send(self.rgb_buffer)
                            cam.sleep_until_next_frame()

                            # Sleep 2.0s checking run flag
                            for _ in range(20):
                                if not self._run_flag:
                                    break
                                time.sleep(0.1)

                            if not self._run_flag:
                                break

                            print("[CameraEngine] Attempting reconnection...")
                            new_cap = cv2.VideoCapture(self.settings.camera_index, cv2.CAP_DSHOW)
                            curr_w = new_cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                            curr_h = new_cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                            curr_fps = new_cap.get(cv2.CAP_PROP_FPS)

                            if curr_w != self.settings.width:
                                new_cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.width)
                            if curr_h != self.settings.height:
                                new_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.height)
                            if curr_fps != self.settings.fps:
                                new_cap.set(cv2.CAP_PROP_FPS, self.settings.fps)

                            if new_cap.isOpened():
                                with self.lock:
                                    self.cap = new_cap
                                reconnected = True
                                print("[CameraEngine] Reconnection successful!")
                            else:
                                new_cap.release()

                        if not reconnected:
                            break
                        continue  # Re-run loop with new self.cap

                    # 1. Processing Pipeline (In-place optimizations applied inside)
                    processed_frame = self._process_frame(frame)

                    # 2. Resolution Safety Check and Correction
                    h, w = processed_frame.shape[:2]
                    target_w, target_h = self.settings.width, self.settings.height
                    if w != target_w or h != target_h:
                        processed_frame = cv2.resize(
                            processed_frame, (target_w, target_h), interpolation=cv2.INTER_LINEAR
                        )

                    # 3. Virtual Camera Output (Optimized buffer reuse)
                    cv2.cvtColor(
                        processed_frame, cv2.COLOR_BGR2RGB, dst=self.rgb_buffer
                    )
                    cam.send(self.rgb_buffer)
                    cam.sleep_until_next_frame()

                    # 4. UI Notification with backpressure & offloaded scaling
                    with self.lock:
                        ui_ready = self.ui_ready
                        preview_size = self.preview_size

                    if ui_ready:
                        with self.lock:
                            self.ui_ready = False

                        # Scale on background thread to offload UI thread
                        preview_frame = cv2.resize(
                            processed_frame, preview_size, interpolation=cv2.INTER_LINEAR
                        )
                        ph, pw, pch = preview_frame.shape
                        q_img = QImage(
                            preview_frame.data, pw, ph, pch * pw, QImage.Format.Format_BGR888
                        ).copy()  # Make a deep copy to ensure thread safety of the memory
                        self.frame_ready.emit(q_img)

        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            with self.lock:
                if self.cap:
                    self.cap.release()
                    self.cap = None

    def _process_frame(self, frame):
        # Read settings variables thread-safely
        with self.lock:
            zoom_level = self.settings.zoom_level
            flip_horizontal = self.settings.flip_horizontal
            flip_vertical = self.settings.flip_vertical
            brightness = self.settings.brightness
            contrast = self.settings.contrast
            saturation = self.settings.saturation
            
            # Lazily/dynamically update LUT if changed externally (e.g. from tests)
            if self.sat_lut is None or self.last_sat_val != saturation:
                self.sat_lut = np.clip(
                    np.arange(256) * (1.0 + saturation / 100.0), 0, 255
                ).astype(np.uint8)
                self.last_sat_val = saturation
            sat_lut = self.sat_lut

        # 1. Zoom (Only resize if necessary)
        if abs(zoom_level - 1.0) > 0.01:
            h, w = frame.shape[:2]
            new_h, new_w = int(h / zoom_level), int(w / zoom_level)
            start_h = (h - new_h) // 2
            start_w = (w - new_w) // 2
            frame = frame[start_h : start_h + new_h, start_w : start_w + new_w]
            frame = cv2.resize(frame, self.output_size, interpolation=cv2.INTER_LINEAR)

        # 2. Flips (In-place)
        if flip_horizontal and flip_vertical:
            cv2.flip(frame, -1, dst=frame)
        elif flip_horizontal:
            cv2.flip(frame, 1, dst=frame)
        elif flip_vertical:
            cv2.flip(frame, 0, dst=frame)

        # 3. Brightness/Contrast Optimization (In-place)
        if brightness != 0 or contrast != 0:
            alpha = 1.0 + (contrast / 100.0)
            beta = brightness
            cv2.convertScaleAbs(frame, dst=frame, alpha=alpha, beta=beta)

        # 4. Saturation (HSV space using lookup table to avoid float allocations)
        if saturation != 0 and sat_lut is not None:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hsv[:, :, 1] = cv2.LUT(hsv[:, :, 1], sat_lut)
            frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        return frame

    def stop(self):
        self._run_flag = False
        with self.lock:
            if self.cap:
                self.cap.release()
                # Do not set to None here to prevent None reference errors in run loop
                # since we check cap_device = self.cap, but it will exit loop when read fails
        self.wait(2000)  # Wait up to 2 seconds for worker thread to exit securely

