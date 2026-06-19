import unittest
import numpy as np
import cv2
from src.state_manager import AppSettings
from src.camera_engine import CameraEngine

class TestCameraEngine(unittest.TestCase):
    def setUp(self):
        self.settings = AppSettings(
            width=100,
            height=100,
            zoom_level=1.0,
            flip_horizontal=False,
            flip_vertical=False,
            brightness=0,
            contrast=0,
            saturation=0
        )
        self.engine = CameraEngine(self.settings)
        # Create a simple test frame: 100x100 BGR frame where left half is black (0) and right half is white (255)
        self.test_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        self.test_frame[:, 50:] = 255

    def test_no_transformations(self):
        # Test that original frame is unaltered when settings are default
        processed = self.engine._process_frame(self.test_frame.copy())
        self.assertTrue(np.array_equal(self.test_frame, processed))

    def test_flip_horizontal(self):
        # Mirror the frame horizontally. Left half should become white, right half black.
        self.settings.flip_horizontal = True
        processed = self.engine._process_frame(self.test_frame.copy())
        
        # Verify left pixel (0, 10) is white, right pixel (0, 90) is black
        self.assertEqual(processed[0, 10, 0], 255)
        self.assertEqual(processed[0, 90, 0], 0)

    def test_flip_vertical(self):
        # Vertical flip. For our left-right split frame, a vertical flip will look the same,
        # but let's test using a top-bottom split frame.
        self.settings.flip_vertical = True
        tb_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        tb_frame[50:, :] = 255 # bottom half white

        processed = self.engine._process_frame(tb_frame.copy())
        # Top half should now be white, bottom half black
        self.assertEqual(processed[10, 0, 0], 255)
        self.assertEqual(processed[90, 0, 0], 0)

    def test_zoom_level(self):
        # Zoom in by 2x. Let's verify dimensions remain correct (100x100)
        self.settings.zoom_level = 2.0
        processed = self.engine._process_frame(self.test_frame.copy())
        
        self.assertEqual(processed.shape, (100, 100, 3))
        # Center of original frame was splitting 50:50. Zooming 2x means the zoomed region
        # starts from x=25 to x=75. So, the new split line should still be in the middle of zoomed.
        # Let's test that the dimensions match settings.width and settings.height.
        self.assertEqual(processed.shape[0], self.settings.height)
        self.assertEqual(processed.shape[1], self.settings.width)

    def test_brightness_and_contrast(self):
        # Test brightness increase (+50)
        self.settings.brightness = 50
        processed = self.engine._process_frame(self.test_frame.copy())
        # Black pixels should become 50
        self.assertEqual(processed[0, 10, 0], 50)
        # White pixels should clip to 255
        self.assertEqual(processed[0, 90, 0], 255)

    def test_saturation(self):
        # Test saturation reduction (greyscale conversion when saturation = -100)
        self.settings.saturation = -100
        # Create a pure blue frame [255, 0, 0] in BGR
        colored_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        colored_frame[:, :] = [255, 0, 0]
        
        processed = self.engine._process_frame(colored_frame)
        # Blue should lose saturation. Let's check that channels get closer to equal (grey)
        # Note: opencv BGR to HSV to BGR with s=0 gives grey value.
        self.assertAlmostEqual(processed[0, 0, 0], processed[0, 0, 1], delta=5)
        self.assertAlmostEqual(processed[0, 0, 1], processed[0, 0, 2], delta=5)
