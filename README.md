# Desktop Test

A standalone desktop testing suite for Python GUI applications based on PyTest. This tool runs locally on your computer to test desktop applications before deployment.

## Overview

Desktop Test provides a user-friendly way to run tests against desktop applications built with Python GUI frameworks (Tkinter, PyQt, etc.). No installation required - just download and run!

## Features

- **Desktop Testing**: Run tests directly on your local machine
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **GUI Framework Support**: Test applications built with Tkinter, PyQt, wxPython, etc.
- **Screenshot Testing**: Capture screenshots for visual comparison
- **Custom Assertions**: Verify window states, control properties, and UI behaviors
- **HTML Reports**: Generate detailed test reports with screenshots
- **Code Coverage**: Track which parts of your application are covered by tests
- **Automatic Test Generation**: Analyze your projects and automatically generate tests

## Requirements

- Python 3.6 or higher
- PyTest (will be checked and a warning displayed if not installed)
- GUI library corresponding to your application (e.g., Tkinter, PyQt)

## Getting Started

1. Download this repository to your computer
2. Navigate to the repository directory in your terminal
3. Run the executable script:

```bash
# On Linux/macOS
./desktop-test run

# On Windows
python desktop-test run
```

## Automatic Test Generation

One of the most powerful features of Desktop Test is its ability to automatically analyze your Python desktop application and generate tests:

```bash
# Analyze a project and generate tests
./desktop-test autogen /path/to/your/project

# Specify custom output directory for tests
./desktop-test autogen /path/to/your/project --output /path/to/output

# Just analyze the project without generating tests
./desktop-test autogen /path/to/your/project --analyze-only
```

The auto-generation feature:

1. Analyzes your project structure
2. Detects GUI framework (Tkinter, PyQt, etc.)
3. Identifies UI elements (buttons, entries, etc.)
4. Creates appropriate test fixtures
5. Generates test cases for UI components
6. Creates basic tests for application logic

### How Auto-Generation Works

The automatic test generator analyzes your code using Python's AST (Abstract Syntax Tree) to identify:

- Application classes and their inheritance hierarchy
- UI elements created in your code
- Methods that can be tested
- Event handlers and callbacks

Based on this analysis, it generates:

1. A `conftest.py` file with fixtures for your application
2. Test files for each major class in your application
3. Test cases for UI elements that exercise their functionality

## Writing Tests Manually

Create a `tests` directory in your project and add test files. Here's a simple example for a Tkinter application:

```python
# tests/test_my_app.py
import pytest
from myapp import MyApplication  # Your application

def test_app_window_title(app_instance, main_window):
    # Test that the application window has the correct title
    assert main_window.title() == "My Application"

def test_button_click(app_instance):
    # Test that clicking a button updates the counter
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

## Command-Line Options

```bash
# Run all tests
./desktop-test run

# Run specific test files or directories
./desktop-test run tests/test_login.py

# Generate HTML report
./desktop-test run --html

# Run tests in parallel for faster results
./desktop-test run --parallel

# List all available tests without running them
./desktop-test list

# Auto-generate tests
./desktop-test autogen /path/to/your/project
```

## Configuration

Create a `desktop_test.json` file in your project root for custom settings:

```json
{
    "test_dir": "tests",
    "report_dir": "test_reports",
    "screenshot_dir": "screenshots",
    "screenshot_on_failure": true,
    "parallel": true,
    "max_workers": 4
}
```

## Example Projects

See the `examples` directory for sample desktop applications with test suites:

- `examples/tkinter_app`: A simple Tkinter note-taking application
- `examples/pyqt_app`: A PyQt calculator application (requires PyQt installation)

## Custom Assertions for UI Testing

Desktop Test provides special assertion functions for UI testing:

```python
from desktop_test.assertions import (
    assert_window_exists,
    assert_control_exists,
    assert_control_value,
    assert_control_enabled,
    assert_dialog_shown
)

def test_dialog_shown(app_instance):
    # Click a button that shows a dialog
    app_instance.show_dialog_button.invoke()
    
    # Assert that a dialog with the given title is shown
    dialog = assert_dialog_shown(app_instance, "Confirmation Dialog")
    
    # Check dialog content
    ok_button = assert_control_exists(dialog, "ok_button")
    assert_control_enabled(ok_button)
```
