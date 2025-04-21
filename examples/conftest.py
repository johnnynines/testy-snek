"""
PyTest configuration for example tests.

This file configures pytest for running the example tests.
"""

import os
import sys
import time
import pytest
import tkinter as tk
from pathlib import Path
from typing import Any, Dict, Optional

# Add parent directory to path so we can import pydesktop_test
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import from the package
from pydesktop_test.fixtures import (
    temp_data,
    mock_dialog,
    ui_screenshot,
    isolated_config
)


@pytest.fixture
def app_instance(request):
    """
    Custom app_instance fixture for Tkinter applications.
    
    This is a version of the fixture specialized for Tkinter applications
    that handles the mainloop differently.
    """
    # Get app_class from marker or use default
    app_class = None
    marker = request.node.get_closest_marker("app_class")
    
    if marker:
        app_class = marker.args[0]
    else:
        # Attempt to import from module-level fixture if available
        if hasattr(request.module, "APP_CLASS"):
            app_class = request.module.APP_CLASS
    
    if app_class is None:
        pytest.skip("No application class specified for test")
    
    # Initialize app with test environment settings
    app = app_class()
    
    # Configure app for testing
    if hasattr(app, "configure_for_testing"):
        app.configure_for_testing()
    
    # For Tkinter apps, we need to handle the mainloop differently
    if hasattr(app, "root") and isinstance(app.root, tk.Tk):
        # Make sure the app is visible
        app.root.update()
        
        # For tests, we don't want to start the mainloop
        def process_events():
            app.root.update()
        
        # Replace the start method to just process events
        app.start = process_events
        
        # Process events immediately to make the window visible
        process_events()
    else:
        # For non-Tkinter apps, use the normal start method
        if hasattr(app, "start"):
            app.start()
    
    # Wait for application to fully initialize
    wait_time = 0.1  # Default wait time
    
    if marker and len(marker.args) > 1:
        wait_time = marker.args[1]
    
    time.sleep(wait_time)
    
    # Yield the app instance for the test to use
    try:
        yield app
    finally:
        # Clean up the application instance
        if hasattr(app, "shutdown"):
            app.shutdown()
        elif hasattr(app, "root") and isinstance(app.root, tk.Tk):
            app.root.destroy()
        elif hasattr(app, "close"):
            app.close()
        elif hasattr(app, "quit"):
            app.quit()


@pytest.fixture
def main_window(app_instance):
    """
    Custom main_window fixture for Tkinter applications.
    
    Returns the root window of a Tkinter application.
    """
    if hasattr(app_instance, "root") and isinstance(app_instance.root, tk.Tk):
        return app_instance.root
    elif hasattr(app_instance, "main_window"):
        return app_instance.main_window()
    elif hasattr(app_instance, "get_main_window"):
        return app_instance.get_main_window()
    
    pytest.skip("Could not determine main window from application instance")
