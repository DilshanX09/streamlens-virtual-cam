import sys
import os

# Dynamically add the project root directory to sys.path to resolve 'src' imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from src.state_manager import StateManager
from src.ui_main import StreamLensUI

def main():
    # 1. Enable High-DPI Scaling for crisp visuals on modern displays
    # In PyQt6, High-DPI scaling is enabled by default, but we ensure proper handling of scaling ratios
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    # 2. Initialize QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("StreamLens")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("StreamLens")
    
    # 3. Initialize State Manager
    # This automatically loads persistent settings from 'settings.json' or falls back to defaults
    state_manager = StateManager()
    
    # 4. Set Application Icon (with safe fallback if icon is missing)
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # 5. Initialize & Show Main UI
    window = StreamLensUI(state_manager)
    window.show()
    
    # 6. Start event loop and exit securely
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
