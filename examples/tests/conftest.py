import pytest
import os
import sys
import tkinter as tk
from . import DemoApp

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

@pytest.fixture
def demo_app_instance():
    """Fixture to provide a test instance of DemoApp."""
    app = DemoApp()
    # Configure for testing
    app.root.withdraw()  # Hide window during tests
    # Set up event processing
    def process_events():
        app.root.update()
    app.process_events = process_events
    yield app
    # Clean up
    try:
        if hasattr(app, 'shutdown'):
            app.shutdown()
        elif hasattr(app, 'close'):
            app.close()
    except:
        pass

@pytest.fixture
def main_window(app_instance):
    """Fixture to provide the main window of the application."""
    # Get the main window based on the app structure
    if hasattr(app_instance, 'root'):
        return app_instance.root
    elif hasattr(app_instance, 'window'):
        return app_instance.window
    elif hasattr(app_instance, 'main_window'):
        return app_instance.main_window
    # If we can't find it, assume the app itself is the main window
    return app_instance
