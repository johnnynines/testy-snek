import pytest
import os
import sys

# Add the parent directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))))

# Import the application class
from . import DemoApp
import tkinter as tk

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
    # Define placeholder functions if the module is not available
    def assert_window_exists(*args, **kwargs): return args[0]
    def assert_control_exists(*args, **kwargs): return None
    def assert_control_value(*args, **kwargs): pass
    def assert_control_enabled(*args, **kwargs): pass
    def assert_dialog_shown(*args, **kwargs): return None


def test_demo_app_init(demo_app_instance):
    """Test that DemoApp initializes correctly."""
    # Verify the instance was created
    assert demo_app_instance is not None
    assert isinstance(demo_app_instance, DemoApp)

def test_demo_app_title(demo_app_instance, main_window):
    """Test that the DemoApp window has a title."""
    # Get the window title
    title = main_window.title()
    # Verify it's not empty
    assert title is not None
    assert len(title) > 0

def test_demo_app_clear_form(demo_app_instance):
    """Test that the clear_form method exists."""
    # Verify the method exists
    assert hasattr(demo_app_instance, 'clear_form')
    assert callable(getattr(demo_app_instance, 'clear_form'))
    # This is a placeholder test - to actually test the method,
    # you'd need to call it with appropriate arguments and verify the results
    # Example:
    # result = demo_app_instance.clear_form()
    # assert result is not None

def test_demo_app_confirm_exit(demo_app_instance):
    """Test that the confirm_exit method exists."""
    # Verify the method exists
    assert hasattr(demo_app_instance, 'confirm_exit')
    assert callable(getattr(demo_app_instance, 'confirm_exit'))
    # This is a placeholder test - to actually test the method,
    # you'd need to call it with appropriate arguments and verify the results
    # Example:
    # result = demo_app_instance.confirm_exit()
    # assert result is not None

def test_demo_app_increment_counter(demo_app_instance):
    """Test that the increment_counter method exists."""
    # Verify the method exists
    assert hasattr(demo_app_instance, 'increment_counter')
    assert callable(getattr(demo_app_instance, 'increment_counter'))
    # This is a placeholder test - to actually test the method,
    # you'd need to call it with appropriate arguments and verify the results
    # Example:
    # result = demo_app_instance.increment_counter()
    # assert result is not None

def test_demo_app_reset_counter(demo_app_instance):
    """Test that the reset_counter method exists."""
    # Verify the method exists
    assert hasattr(demo_app_instance, 'reset_counter')
    assert callable(getattr(demo_app_instance, 'reset_counter'))
    # This is a placeholder test - to actually test the method,
    # you'd need to call it with appropriate arguments and verify the results
    # Example:
    # result = demo_app_instance.reset_counter()
    # assert result is not None

def test_demo_app_show_about(demo_app_instance):
    """Test that the show_about method exists."""
    # Verify the method exists
    assert hasattr(demo_app_instance, 'show_about')
    assert callable(getattr(demo_app_instance, 'show_about'))
    # This is a placeholder test - to actually test the method,
    # you'd need to call it with appropriate arguments and verify the results
    # Example:
    # result = demo_app_instance.show_about()
    # assert result is not None
