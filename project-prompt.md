# Project Specification: StreamLens (Virtual Camera Software)

## 1. Project Overview
Develop a high-performance, production-grade virtual camera software for Windows. The application captures the built-in webcam feed at a strict 60FPS with zero delay, applies real-time image transformations, and outputs the feed to a virtual camera driver (usable in Zoom, OBS, Teams). It features a custom frameless UI, persistent state management, automated CI/CD builds, and a Dockerized testing environment.

## 2. Core Technologies
* **Language:** Python 3.11+
* **Camera Processing:** `opencv-python` (Strictly using `cv2.CAP_DSHOW` for high FPS/low latency)
* **Virtual Camera Output:** `pyvirtualcam`
* **GUI Framework:** `PyQt6` (Frameless window with custom title bar and rounded corners)
* **Array Manipulation:** `numpy`
* **Packaging & DevOps:** `PyInstaller`, `Inno Setup`, GitHub Actions, Docker

## 3. System Architecture & Constraints
* **Strict Multi-threading:** The camera processing (`cv2.VideoCapture` and `pyvirtualcam` streaming) MUST run on a dedicated background worker thread. The UI MUST run on the main thread. Blocking the main UI thread with camera loops is strictly prohibited.
* **Performance:** The target is a stable 60FPS. 
* **State Management:** All user preferences (flip state, zoom level, color adjustments) must be automatically saved to a `settings.json` file and reloaded upon the next launch.
* **Quality Standard:** The code must be production-grade, highly modular, and follow "Quality Over Everything" principles.

## 4. Directory Structure to Generate
```text
StreamLens/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── camera_engine.py        # Threaded OpenCV & Virtual Cam logic
│   ├── ui_main.py              # PyQt6 frameless window and styling
│   └── state_manager.py        # JSON configuration handling
├── assets/
│   └── icon.ico                # App icon
├── .github/
│   └── workflows/
│       └── build.yml           # GitHub Actions CI/CD Pipeline
├── Dockerfile                  # Containerized environment for testing/logic validation
├── tests/
├── requirements.txt            # All dependencies
├── README.md                   # High-level overview and run instructions
└── CONTRIBUTING.md             # Guidelines for open-source contributors