<div align="center">

<pre>
 ____ _                               _                    
/ ___| |_ _ __ ___  __ _ _ __ ___    | |    ___ _ __  ___  
\___ \ __| '__/ _ \/ _` | '_ ` _ \   | |   / _ \ '_ \/ __| 
 ___) | |_| | |  __/ (_| | | | | | |  | |__|  __/ | | \__ \ 
|____/ \__|_|  \___|\__,_|_| |_| |_|  |_____\___|_| |_|___/ 
</pre>

<h1>StreamLens Virtual Camera</h1>

A high-performance, 60FPS virtual camera for Windows featuring real-time image transformations and a premium frameless UI.

<br />

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.5+-00C000?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![PyVirtualCam](https://img.shields.io/badge/PyVirtualCam-0.11+-FF6F61?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/letmaik/pyvirtualcam)
[![PyInstaller](https://img.shields.io/badge/PyInstaller-5.13+-FFD700?style=for-the-badge&logo=python&logoColor=black)](https://pyinstaller.org/)

</div>

---

## Features

- **Strict 60FPS DirectShow Stream:** Low-latency video capture leveraging OpenCV's native DirectShow (`cv2.CAP_DSHOW`) backend.

* **Premium Frameless UI:** A fully custom dark-themed GUI designed with PyQt6, featuring smooth rounded window corners, custom draggable title bar, drop shadows, and high-fidelity rendering.
* **Real-Time Transformations:**
  - **Zoom & Crop:** Lossless digital zoom slider (1.0x to 3.0x).
  - **Flips:** Live horizontal mirror previews and vertical mirror feeds.
  - **Color Correction:** Real-time Brightness, Contrast, and Saturation adjustments using high-performance HSV color-space scaling.
* **Automatic Persistence:** Instant JSON serialization/deserialization to preserve parameters across program restarts.
* **Full DevOps & CI/CD Tooling:** Automated multi-platform lint checkups, headless offscreen testing support, and native Windows PyInstaller packaging configurations.

---

## Architecture

StreamLens follows a rigorous, production-grade **multithreaded architectural paradigm** built on strict separation of concerns:

```text
               +-------------------------------------------+
               |                 Main GUI Thread           |
               |  - PyQt6 Event Loop                       |
               |  - Custom Frameless Control Windows       |
               +---------------------+---------------------+
                                     ^
                         Signal/Slot | (Frame Buffers)
                                     v
               +---------------------+---------------------+
               |             Background Worker QThread     |
               |  - OpenCV Camera Processing (DirectShow)  |
               |  - Image Filter/Grading Transformations   |
               |  - PyVirtualCam output stream loop        |
               +-------------------------------------------+
```

1. **GUI Main Thread:** Drives the layout, listens to user control inputs, writes immediately to the local `StateManager`, and uses high-performance signal boundaries to receive frame matrices for paint events.
2. **Background Camera Engine:** Run continuously on a dedicated background worker (`QThread`). Operates the camera capturing and transformation pipeline, formats frames to RGB, and channels frames natively to `pyvirtualcam`'s camera registers.

---

## Quick Start

### 1. Clone & Initialize

```bash
git clone https://github.com/DilshanX09/streamlens-virtual-cam
cd stream-lens
```

### 2. Set up Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Requirements

Ensure you have registered a virtual camera driver (e.g. OBS Studio Virtual Camera) on your machine, then run:

```bash
pip install -r requirements.txt
```

### 4. Execute the Application

```bash
python src/main.py
```

---

## Testing

StreamLens features high coverage unit tests. To run tests locally in your virtual environment:

```bash
python -m unittest discover -s tests
```

---

## 🤝 Contributing

Contributions make the open-source community an amazing place! Check out our [CONTRIBUTING.md](CONTRIBUTING.md) to get started on following PEP 8 coding style standards and executing headless test suites before sending pull requests.
