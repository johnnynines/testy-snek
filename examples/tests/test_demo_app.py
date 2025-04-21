"""
Tests for the DemoApp class.

These tests validate the functionality of the demo application interface.
"""

import pytest
import sys
import os

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the application class
from demo_app import DemoApp

# Import assertion utilities
try:
    from pydesktop_test.assertions import (
        assert_window_exists,
        assert_control_exists,
        assert_control_value,
        assert_control_enabled
    )
except ImportError:
    # Define placeholders if module is not available
    def assert_window_exists(*args, **kwargs): return args[0]
    def assert_control_exists(*args, **kwargs): return None
    def assert_control_value(*args, **kwargs): pass
    def assert_control_enabled(*args, **kwargs): pass


@pytest.fixture
def app_instance():
    """Create a test instance of the DemoApp."""
    app = DemoApp()
    
    # Hide the window during testing
    app.root.withdraw()
    
    # Add a method to process events
    def process_events():
        app.root.update()
    
    app.process_events = process_events
    
    yield app
    
    # Clean up after tests
    try:
        app.shutdown()
    except:
        pass


def test_app_creation(app_instance):
    """Test that the application is created successfully."""
    assert app_instance is not None
    assert isinstance(app_instance, DemoApp)


def test_window_title(app_instance):
    """Test that the window has the correct title."""
    assert app_instance.root.title() == "Demo Application"


def test_counter_increment(app_instance):
    """Test that the counter increments when the button is clicked."""
    # Get initial counter value
    initial_text = app_instance.counter_label.cget("text")
    initial_value = int(initial_text.split(": ")[1])
    
    # Click the increment button
    app_instance.increment_button.invoke()
    app_instance.process_events()
    
    # Check that the counter was incremented
    new_text = app_instance.counter_label.cget("text")
    new_value = int(new_text.split(": ")[1])
    
    assert new_value == initial_value + 1


def test_counter_reset(app_instance):
    """Test that the counter resets to zero."""
    # First increment the counter
    app_instance.increment_button.invoke()
    app_instance.process_events()
    
    # Then reset it
    app_instance.reset_button.invoke()
    app_instance.process_events()
    
    # Check that the counter is zero
    text = app_instance.counter_label.cget("text")
    value = int(text.split(": ")[1])
    
    assert value == 0


def test_form_clear(app_instance):
    """Test that the form clears correctly."""
    # Set some values
    app_instance.name_entry.insert(0, "Test User")
    app_instance.notes_text.insert("1.0", "This is a test note")
    app_instance.option1_var.set(True)
    app_instance.option2_var.set(True)
    app_instance.radio_var.set("option2")
    app_instance.combo.current(1)  # Select the second item
    
    # Process events
    app_instance.process_events()
    
    # Clear the form
    app_instance.clear_button.invoke()
    app_instance.process_events()
    
    # Check that values are cleared
    assert app_instance.name_entry.get() == ""
    assert app_instance.notes_text.get("1.0", "end-1c") == ""
    assert app_instance.option1_var.get() is False
    assert app_instance.option2_var.get() is False
    assert app_instance.radio_var.get() == "option1"  # Default option
    assert app_instance.combo.current() == 0  # First item