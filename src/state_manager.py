import json
import os
from dataclasses import dataclass, asdict, field

@dataclass
class AppSettings:
    flip_horizontal: bool = False
    flip_vertical: bool = False
    zoom_level: float = 1.0
    brightness: int = 0
    contrast: int = 0
    saturation: int = 0
    camera_index: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 60

class StateManager:
    def __init__(self, config_path="settings.json"):
        self.config_path = config_path
        self.settings = self.load_settings()

    def load_settings(self) -> AppSettings:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    return AppSettings(**data)
            except Exception as e:
                print(f"Error loading settings: {e}")
        return AppSettings()

    def save_settings(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(asdict(self.settings), f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def update_setting(self, key, value):
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            self.save_settings()
