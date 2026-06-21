# Project Specification: StreamLens (Virtual Camera Software)

## 1. Project Overview

Develop a high-performance, production-grade virtual camera software for Windows. The application captures the built-in webcam feed at a strict 60FPS with zero delay, applies real-time image transformations, and outputs the feed to a virtual camera driver (usable in Zoom, OBS, Teams). It features a custom frameless UI, persistent state management, automated CI/CD builds, and a Dockerized testing environment.

## 2. Core Technologies

- **Language:** Python 3.11+
- **Camera Processing:** `opencv-python` (Strictly using `cv2.CAP_DSHOW` for high FPS/low latency)
- **Virtual Camera Output:** `pyvirtualcam`
- **GUI Framework:** `PyQt6` (Frameless window with custom title bar and rounded corners)
- **Array Manipulation:** `numpy`
- **Packaging & DevOps:** `PyInstaller`, `Inno Setup`, GitHub Actions, Docker    

## 3. System Architecture & Constraints

- **Strict Multi-threading:** The camera processing (`cv2.VideoCapture` and `pyvirtualcam` streaming) MUST run on a dedicated background worker thread. The UI MUST run on the main thread. Blocking the main UI thread with camera loops is strictly prohibited.
- **Performance:** The target is a stable 60FPS.
- **State Management:** All user preferences (flip state, zoom level, color adjustments) must be automatically saved to a `settings.json` file and reloaded upon the next launch.
- **Quality Standard:** The code must be production-grade, highly modular, and follow "Quality Over Everything" principles.

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
```

7. Phase 7: Light Theme UI, Hardware Integration & Deep Optimization
Reference Designs: Strictly follow the UI images in the dev-resource directory for the layout.

Light Theme Redesign: Overhaul the PyQt6 UI to a premium Light Theme. Floating overlay panels must be white/off-white with subtle drop shadows. Text, icons, and sliders must be high-contrast dark gray/black.

Camera States & Toggle Logic: >   * Camera Off State: Display a centered, minimalist avatar placeholder silhouette. The hardware camera must be completely released to save RAM and CPU.

Camera On State: The edge-to-edge live video feed replaces the placeholder.

Toggle Button: The bottom-left camera icon must act as a hard ON/OFF toggle. The dropdown arrow next to it opens the camera selection list.

Real Hardware Device Naming: Replace generic OpenCV indices (0, 1, 2) in the UI dropdown with actual hardware friendly names (e.g., 'WSC 1.0 Built-in Camera'). Use Windows APIs or suitable packages to fetch these names dynamically.

Hardware Initialization (Double-Blink Fix): Refactor cv2.VideoCapture initialization. The camera must be initialized exactly once in the background worker thread. Prevent any redundant open/release cycles to eliminate the hardware flashlight double-blink issue.

Virtual Camera Branding: Ensure the virtual camera output stream is globally identified exactly as 'StreamLens' in third-party applications (Zoom, Teams, OBS). Config virtual camera backend appropriately.

Low-End PC Optimization: Aggressively optimize RAM usage and frame processing. Pre-allocate OpenCV matrices and ensure the PyQt6 event loop is completely unblocked for ultra-smooth 60FPS performance on low-end hardware.
