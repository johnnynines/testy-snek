"""
Example GUI tests for desktop applications.

This module demonstrates how to write tests for GUI applications.
NOTE: These tests are for demonstration only and will be skipped
      unless you replace the placeholder with your actual application.
"""

import pytest
import os

# Skip GUI tests when running in environments without display
# or when tkinter is not available
SKIP_GUI_TESTS = os.environ.get("SKIP_GUI_TESTS", False) or not pytest.importorskip("tkinter")

# Import custom assertions for GUI testing
try:
    from pydesktop_test.assertions import (
        assert_window_exists,
        assert_control_exists,
        assert_control_value,
        assert_control_enabled,
        assert_dialog_shown
    )
except ImportError:
    # For demonstration, we'll define placeholder functions
    def assert_window_exists(*args, **kwargs): pass
    def assert_control_exists(*args, **kwargs): return None
    def assert_control_value(*args, **kwargs): pass
    def assert_control_enabled(*args, **kwargs): pass
    def assert_dialog_shown(*args, **kwargs): return None


# Replace this with your actual application class
class DemoApplication:
    """
    Placeholder for a GUI application class.
    
    In a real test, you would import your actual application class here.
    For example:
        from my_app.main import MyApplication
    """
    def __init__(self):
        self.title = "Demo Application"
        self.counter = 0
        
    def get_title(self):
        return self.title
        
    def increment_counter(self):
        self.counter += 1
        return self.counter


# Skip all GUI tests in this module if we can't run them
pytestmark = pytest.mark.skipif(
    SKIP_GUI_TESTS, 
    reason="GUI tests skipped (no display or tkinter not available)"
)


@pytest.fixture
def app_instance():
    """Fixture to provide a test instance of the application."""
    app = DemoApplication()
    yield app
    # Clean up (if needed)


def test_application_title(app_instance):
    """Test that the application has the expected title."""
    assert app_instance.get_title() == "Demo Application"
    
    # In a real GUI test, you might do something like:
    # assert_window_exists(app_instance, "Demo Application")
    # or
    # assert app_instance.window.title() == "Demo Application"


def test_counter_increment(app_instance):
    """Test that the counter increments correctly."""
    initial_count = app_instance.counter
    
    # Simulate clicking a button
    app_instance.increment_counter()
    
    # Check that the counter increased by 1
    assert app_instance.counter == initial_count + 1
    
    # In a real GUI test, you might do something like:
    # counter_label = assert_control_exists(app_instance.window, "counter_label")
    # assert_control_value(counter_label, "1")


# Example of a more complex test
def test_multiple_interactions(app_instance):
    """Test multiple interactions with the application."""
    # Simulate several button clicks
    for i in range(5):
        app_instance.increment_counter()
    
    # Verify the final state
    assert app_instance.counter == 5


# This demonstrates how to use the special assertions
def test_assertions_example(app_instance):
    """
    Example showing how to use the custom assertions.
    
    This test is a placeholder to demonstrate the syntax.
    It will not actually test anything in this demo.
    """
    # Skip this test as it's just for demonstration
    pytest.skip("This is a demonstration test only")
    
    # Check that a window with a specific title exists
    main_window = assert_window_exists(app_instance, "Demo Application")
    
    # Check that a specific control exists in the window
    counter_label = assert_control_exists(main_window, "counter_label")
    
    # Check the value of the control
    assert_control_value(counter_label, "0")
    
    # Check that a button is enabled
    increment_button = assert_control_exists(main_window, "increment_button")
    assert_control_enabled(increment_button)
    
    # Simulate clicking the button
    increment_button.invoke()
    
    # Check that the counter was updated
    assert_control_value(counter_label, "1")