# PyDesktop Test

A PyTest-based testing framework for Python desktop applications with enhanced reporting and developer experience.

## Features

- **Easy Test Creation**: Simplifies writing tests for desktop applications
- **Custom Assertions**: Built-in assertions for UI components and states
- **Enhanced Reporting**: Rich console output and HTML reports
- **Configurable**: Flexible configuration for different testing environments
- **Test Discovery**: Automatic test discovery across project directories
- **Parallel Execution**: Run tests in parallel for faster results
- **Code Coverage**: Integrated coverage reporting
- **Framework Support**: Compatible with multiple GUI frameworks (Tkinter, PyQt, etc.)
- **Screenshot Testing**: Capture screenshots for visual regression testing

## Installation

```bash
pip install pydesktop-test
```

## Quick Start

Here's a simple example of how to use PyDesktop Test with a Tkinter application:

```python
import pytest
from myapp import MyTkinterApp  # Your application class

# Mark the test with the application class
@pytest.mark.app_class(MyTkinterApp)
def test_app_window_title(app_instance, main_window):
    """Test that the application window has the correct title."""
    assert main_window.title() == "My Application"

@pytest.mark.app_class(MyTkinterApp)
def test_button_click(app_instance):
    """Test that clicking a button updates the counter."""
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

## Running Tests

You can run tests using the included command-line tool:

```bash
# Run all tests in the current directory
pydesktop-test run

# Run tests with HTML reporting
pydesktop-test run --html

# Run tests in parallel
pydesktop-test run --parallel
```

Or use pytest directly with the PyDesktop Test fixtures:

```bash
pytest tests/ --cov=myapp
```

## Custom Assertions

PyDesktop Test provides specialized assertions for testing UI components:

```python
from pydesktop_test.assertions import (
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

## Configuration

Create a `pydesktop_test.json` file in your project root to configure the framework:

```json
{
    "test_dir": "tests",
    "report_dir": "test_reports",
    "coverage_dir": "coverage",
    "screenshot_on_failure": true,
    "parallel": true,
    "max_workers": 4
}
```

## Documentation

For more detailed documentation and examples, visit the [documentation site](https://pydesktop-test.readthedocs.io/).
