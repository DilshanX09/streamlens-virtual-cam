import sys
import unittest
from unittest.mock import MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.state_manager import StateManager
from src.ui_main import StreamLensUI, CustomTitleBar

# Ensure QApplication is initialized for the testing session
# Since we run unit tests, a single application instance is needed
app = QApplication.instance()
if app is None:
    # Set headless offscreen platform for reliable CLI test execution
    import os
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication(sys.argv)

class TestStreamLensUI(unittest.TestCase):
    def setUp(self):
        self.state_manager = StateManager(config_path="dummy_settings.json")
        # Ensure we delete dummy config if created
        if os.path.exists("dummy_settings.json"):
            try:
                os.remove("dummy_settings.json")
            except OSError:
                pass
                
        self.ui = StreamLensUI(self.state_manager)

    def tearDown(self):
        self.ui.close()
        if os.path.exists("dummy_settings.json"):
            try:
                os.remove("dummy_settings.json")
            except OSError:
                pass

    def test_ui_components_exist(self):
        # Verify essential UI elements are created and configured correctly
        self.assertIsNotNone(self.ui.title_bar)
        self.assertIsNotNone(self.ui.preview_label)
        self.assertIsNotNone(self.ui.cb_camera)
        self.assertIsNotNone(self.ui.chk_flip_h)
        self.assertIsNotNone(self.ui.chk_flip_v)
        self.assertIsNotNone(self.ui.slider_zoom)
        self.assertIsNotNone(self.ui.slider_bright)

    def test_ui_syncs_with_state_manager(self):
        # Verify that altering UI controls successfully propagates settings back to StateManager
        # 1. Flip horizontal
        self.ui.chk_flip_h.setChecked(True)
        self.assertTrue(self.state_manager.settings.flip_horizontal)

        # 2. Brightness slider
        self.ui.slider_bright.setValue(45)
        self.assertEqual(self.state_manager.settings.brightness, 45)

        # 3. Zoom slider
        self.ui.slider_zoom.setValue(25) # 2.5x
        self.assertEqual(self.state_manager.settings.zoom_level, 2.5)

    def test_reset_controls(self):
        # 1. Mess up controls
        self.ui.chk_flip_h.setChecked(True)
        self.ui.slider_bright.setValue(50)
        self.ui.slider_zoom.setValue(20)

        # 2. Reset
        self.ui._reset_controls()

        # 3. Verify defaults
        self.assertFalse(self.ui.chk_flip_h.isChecked())
        self.assertEqual(self.ui.slider_bright.value(), 0)
        self.assertEqual(self.ui.slider_zoom.value(), 10) # 1.0x

    def test_title_bar_buttons(self):
        # Check CustomTitleBar close and minimize properties exist and connect correctly
        title_bar = self.ui.title_bar
        self.assertIsInstance(title_bar, CustomTitleBar)
        self.assertEqual(title_bar.btn_close.text(), "✕")
        self.assertEqual(title_bar.btn_minimize.text(), "—")

import os
