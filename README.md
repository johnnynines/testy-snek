# PyDesktop Test

A comprehensive PyTest-based testing framework for Python desktop applications with enhanced reporting and developer experience.

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Overview

PyDesktop Test simplifies the process of testing Python desktop applications by providing specialized fixtures, assertions, and tools designed specifically for GUI testing. The framework extends PyTest with desktop-specific capabilities, making it easier to write reliable tests for desktop applications.

Key features:
- 🧪 **Auto-Test Generation**: Automatically analyze your desktop application and generate tests
- 🧩 **Custom Assertions**: GUI-specific assertions for testing UI components and interactions
- 📊 **Enhanced Reporting**: Detailed HTML reports with screenshots and test results
- 🔧 **Configurable**: Extensive configuration options for different testing environments
- 🔍 **Framework Support**: Works with multiple GUI frameworks (Tkinter, PyQt, etc.)
- 📷 **Screenshot Capture**: Visual testing and debugging with automatic screenshots

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Install from PyPI

```bash
pip install pydesktop-test
```

### Install from Source

```bash
git clone https://github.com/yourusername/pydesktop-test.git
cd pydesktop-test
pip install -e .
```

## Quick Start

### Basic Usage

1. Install the package
2. Create test files in your project's test directory
3. Run tests using the `desktop-test` command

```bash
# Run all tests
desktop-test run

# Run tests with specific options
desktop-test run --verbose --html-report
```

### Auto-Test Generation

PyDesktop Test can automatically analyze your desktop application and generate basic tests:

```bash
# Generate tests for a whole project
desktop-test autogen /path/to/your/project

# Generate tests for a single file
desktop-test autogen /path/to/your/app.py

# Specify custom output directory
desktop-test autogen /path/to/your/project --output /path/to/output
```

## Writing Tests

### Basic Test Structure

```python
import pytest
from pydesktop_test.assertions import assert_window_exists, assert_control_exists

# Test function with app_instance fixture
def test_app_window_title(app_instance, main_window):
    # Test that the application window has the correct title
    assert main_window.title() == "My Application"

# Testing a button click
def test_button_click(app_instance):
    # Get the button and counter label
    button = app_instance.button
    counter_label = app_instance.counter_label
    
    # Get initial counter value
    initial_value = int(counter_label["text"])
    
    # Click the button
    button.invoke()
    
    # Check that the counter was incremented
    assert int(counter_label["text"]) == initial_value + 1
```

### Using Custom Assertions

PyDesktop Test provides specialized assertions for UI testing:

```python
from pydesktop_test.assertions import (
    assert_window_exists,
    assert_control_exists,
    assert_control_value,
    assert_control_enabled,
    assert_dialog_shown
)

def test_ui_components(app_instance):
    # Verify window exists
    window = assert_window_exists(app_instance, "My Application")
    
    # Check a specific control exists
    button = assert_control_exists(window, "submit_button")
    
    # Verify control value
    assert_control_value(app_instance.entry, "Initial Text")
    
    # Check control is enabled
    assert_control_enabled(button)
    
    # Test dialog appears
    button.invoke()
    dialog = assert_dialog_shown(app_instance, "Confirmation")
```

## Configuration

PyDesktop Test can be configured using a `pydesktop_test.yaml` file in your project root:

```yaml
# Example configuration
test:
  screenshot_dir: "test_screenshots"
  html_report: true
  parallel: true
  
application:
  headless: true
  startup_delay: 1.0
  
frameworks:
  tkinter:
    enabled: true
  pyqt:
    enabled: false
```

Or via the command line:

```bash
desktop-test run --screenshot-dir=test_screenshots --html-report --parallel
```

## API Reference

### Main Components

- **Fixtures**: Pre-configured test fixtures for desktop application testing
- **Assertions**: Specialized assertions for testing UI states and behaviors
- **Reporting**: Enhanced test reporting with screenshots and detailed logs
- **CLI**: Command-line interface for running tests and generating reports
- **AutoGen**: Automatic test generation for desktop applications

### Key Modules

- `pydesktop_test.assertions`: UI-specific assertion functions
- `pydesktop_test.fixtures`: Test fixtures for desktop applications
- `pydesktop_test.reporting`: Report generation and formatting
- `pydesktop_test.cli`: Command-line interface tools
- `pydesktop_test.config`: Configuration handling
- `pydesktop_test.autogen`: Automatic test generation

## Examples

See the `examples` directory for complete examples with different UI frameworks:

- `examples/demo_app.py`: A simple Tkinter application for demonstration
- `examples/sample_app.py`: A more complex note-taking application
- `examples/tests/`: Example test files for these applications

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- PyTest team for the excellent testing framework
- Contributors to various GUI frameworks for Python