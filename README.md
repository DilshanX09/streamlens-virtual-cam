# StreamLens 🎥✨

[![StreamLens CI/CD Pipeline](https://github.com/your-username/stream-lens/actions/workflows/build.yml/badge.svg)](https://github.com/your-username/stream-lens/actions)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**StreamLens** is a high-performance, production-grade virtual camera application for Windows. It captures a camera feed at a **strict 60FPS with zero delay**, applies real-time image transformations, and outputs the processed feed to a virtual camera driver (e.g., Zoom, OBS, Microsoft Teams, Discord).

Featuring a custom frameless dark-themed GUI, robust multi-threaded synchronization, automated persistent state management, containerized test support, and integrated GitHub Actions compiling, StreamLens represents an industry-standard blueprint for camera utility software.

---

## 🏗️ System Architecture

StreamLens is built around **strict separation of concerns** and safety-critical execution rules:

1. **Dedicated Worker Thread (Camera Engine):** Offloads OpenCV (`cv2.VideoCapture`) camera polling and virtual camera frame output (`pyvirtualcam`) to a high-speed background worker (`QThread`). This prevents the UI main event loop from blocking, ensuring zero lag.
2. **Main Thread (UI Engine):** Handles the custom frameless window, user interactions, and renders incoming frame feeds through a signal-slot boundary using high-efficiency BGR-to-Pixmap rendering.
3. **State Management (State Engine):** Manages real-time preferences via JSON configuration, automatically saving adjustments (zoom, contrast, flips) and loading them seamlessly upon application bootstrap.

---

## 🌟 Key Features

- **Strict 60FPS Low-Latency Loop:** Configured natively through OpenCV's high-speed DirectShow (`cv2.CAP_DSHOW`) interface on Windows.
- **Custom Frameless UI:** A gorgeous, modern dark-themed PyQt6 window featuring smooth rounded corners, custom draggable title bar with controls, and unified control panels.
- **Real-Time Transformations:**
  - **Zoom Control:** Lossless digital cropping (1.0x to 3.0x).
  - **Flips:** Horizontal mirror preview and vertical flips.
  - **Color Grading:** Sliders adjusting Brightness, Contrast, and Saturation (via HSV color-space processing) in real-time.
- **Persistent State Management:** Instantly autosaves modified settings to `settings.json` and loads them seamlessly on relaunch.
- **Fully Containerized Verification:** Docker container configuration with simulated display framebuffers (`xvfb`) allowing headless execution of PyQt6 and OpenCV tests in CI runners.

---

## 🛠️ Prerequisites

To run StreamLens on Windows, you must install:
1. **Python 3.11+** (Ensure you check "Add Python to PATH" during installation).
2. **Virtual Camera Driver:** OBS Virtual Camera or similar virtual camera loopbacks.
   - *Quickest Setup:* Install [OBS Studio](https://obsproject.com/) and click **"Start Virtual Camera"** at least once to register the virtual device registry on your system.

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/stream-lens.git
cd stream-lens
```

### 2. Set up Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python src/main.py
```

---

## 🧪 Testing Suite

We maintain a high-quality test coverage (unit testing state serialization, OpenCV image transformations, and PyQt6 element wiring).

### Run Tests Locally
```bash
python -m unittest discover -s tests
```

### Headless Verification (Simulating CI)
To verify the tests without booting the PyQt6 interface window (runs headless offscreen):
```bash
# PowerShell
$env:QT_QPA_PLATFORM="offscreen"
python -m unittest discover -s tests
```

---

## 📦 Compilation & Packaging

StreamLens is packaged into a self-contained, high-performance Windows GUI executable using `PyInstaller`.

Run the following command in your virtual environment to bundle the application:
```bash
pyinstaller --noconfirm --onedir --windowed --add-data "src;src" --name "StreamLens" src/main.py
```
The compiled, ready-to-distribute binary will be generated under `dist/StreamLens/`.

---

## 🤝 Contributing

Contributions make the open-source community an amazing place! Check out our [CONTRIBUTING.md](CONTRIBUTING.md) to learn how to set up development, follow style conventions, and open pull requests.

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
