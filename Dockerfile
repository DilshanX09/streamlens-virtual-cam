# Use Python 3.11 slim as the official base image
FROM python:3.11-slim

# Prevent Python from writing .pyc files to disc and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system-level dependencies for OpenCV and PyQt6 (X11, GL, and DBus dependencies)
# Install xvfb to support virtual framebuffers if GUI tests are run
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-util1 \
    libxcb-xfixes0 \
    libxcb-xkb1 \
    libxkbcommon-x11-0 \
    libdbus-1-3 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Create and define the application workspace
WORKDIR /workspace

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source and tests
COPY src/ src/
COPY tests/ tests/

# Configure Headless Qt Platform & PythonPath
ENV QT_QPA_PLATFORM=offscreen
ENV PYTHONPATH=/workspace

# Default command to run the unit test discovery
CMD ["python", "-m", "unittest", "discover", "-s", "tests"]
