# Contributing to StreamLens

Thank you for your interest in contributing to StreamLens! We aim for high-quality, production-grade camera utilities, and we welcome contributions from developers of all skill levels.

## Code of Conduct
Please be respectful and professional in all communications, pull requests, and issue reports.

## Getting Started

1. **Fork and Clone:**
   Fork this repository and clone it to your local environment.

2. **Set up virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install development tools:**
   ```bash
   pip install flake8 pytest
   ```

## Development Guidelines

- **Style Standard:** Follow PEP 8 guidelines for Python code.
- **Strict Multi-threading:** Never block the main GUI thread. Any resource-intensive background loops (like camera processing, network calls, file writing) must be handled inside `QThread` workers.
- **Zero-Warning Rule:** Ensure your code passes all linting (`flake8 .`) and typing checks without suppressions or warnings.
- **Write Tests:** Every new feature, bug fix, or helper method must include unit tests under the `tests/` directory.

## Pull Request Process

1. Create a descriptive feature branch (`git checkout -b feature/cool-new-effect`).
2. Make your modular changes. Ensure there is clear separation of concerns (UI in `ui_main.py`, processing in `camera_engine.py`, state in `state_manager.py`).
3. Run lint checks and verify unit tests pass locally:
   ```bash
   # Linux (with virtual frame buffer)
   QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests
   
   # Windows
   python -m unittest discover -s tests
   ```
4. Commit your changes cleanly.
5. Open a Pull Request targeting the `main` branch. Provide a comprehensive summary of your changes, any performance metrics, and validation tests.
