"""
Pytest fixtures for desktop application testing.

This module provides fixtures that can be used in tests to simplify 
common desktop application testing scenarios.
"""

import os
import sys
import time
import pytest
import tempfile
import contextlib
from pathlib import Path
from typing import Any, Dict, Optional, Callable, Generator, TypeVar, Type

# Type for application instances
T = TypeVar('T')


@pytest.fixture
def app_instance(request: pytest.FixtureRequest) -> Generator[Any, None, None]:
    """
    Fixture that creates an instance of the desktop application.
    
    This fixture starts the application, yields the application instance,
    and then ensures proper cleanup after the test is complete.
    
    Usage:
        def test_app_functionality(app_instance):
            # app_instance is running application
            assert app_instance.is_running()
    
    Returns:
        Generator yielding the application instance
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
    
    # Start the application
    if hasattr(app, "start"):
        app.start()
    
    # Wait for application to fully initialize
    wait_time = 0.5  # Default wait time
    
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
        elif hasattr(app, "close"):
            app.close()
        elif hasattr(app, "quit"):
            app.quit()


@pytest.fixture
def main_window(app_instance: Any) -> Any:
    """
    Fixture that provides the main window of the application.
    
    This fixture depends on the app_instance fixture and returns
    the main window or primary UI component.
    
    Usage:
        def test_window_title(main_window):
            assert main_window.title() == "My Application"
    
    Args:
        app_instance: The application instance fixture
        
    Returns:
        The main window or primary UI component
    """
    if hasattr(app_instance, "main_window"):
        return app_instance.main_window()
    elif hasattr(app_instance, "get_main_window"):
        return app_instance.get_main_window()
    elif hasattr(app_instance, "window"):
        return app_instance.window
    else:
        # For frameworks that store windows in a list/collection
        if hasattr(app_instance, "windows") and app_instance.windows:
            return app_instance.windows[0]
        elif hasattr(app_instance, "get_windows") and app_instance.get_windows():
            return app_instance.get_windows()[0]
    
    pytest.skip("Could not determine main window from application instance")


@pytest.fixture
def temp_data() -> Generator[Dict[str, Any], None, None]:
    """
    Fixture providing a dictionary for temporary test data.
    
    This fixture provides a clean dictionary that tests can use to store
    and share data between test steps or fixtures.
    
    Usage:
        def test_with_shared_data(temp_data):
            temp_data['key'] = 'value'
            # Use the data later in the test
    
    Returns:
        Empty dictionary for storing temporary data
    """
    return {}


@pytest.fixture
def mock_dialog(monkeypatch: pytest.MonkeyPatch) -> Dict[str, Any]:
    """
    Fixture to mock dialog interactions.
    
    This fixture provides utilities to mock common dialogs like file open/save,
    message boxes, and input dialogs to enable automated testing without UI interaction.
    
    Usage:
        def test_file_open(app_instance, mock_dialog):
            mock_dialog.set_file_dialog_path('/path/to/test/file.txt')
            app_instance.open_file()  # Will use the mocked path
    
    Args:
        monkeypatch: The pytest monkeypatch fixture
        
    Returns:
        Dictionary of dialog mocking utilities
    """
    mock_utils = {}
    _responses = {}
    
    def set_message_box_response(response_type):
        _responses['message_box'] = response_type
    
    def set_file_dialog_path(path):
        _responses['file_dialog'] = path
    
    def set_input_dialog_text(text):
        _responses['input_dialog'] = text
    
    mock_utils['set_message_box_response'] = set_message_box_response
    mock_utils['set_file_dialog_path'] = set_file_dialog_path
    mock_utils['set_input_dialog_text'] = set_input_dialog_text
    mock_utils['_responses'] = _responses
    
    # Add common response types
    mock_utils['OK'] = 'ok'
    mock_utils['CANCEL'] = 'cancel'
    mock_utils['YES'] = 'yes'
    mock_utils['NO'] = 'no'
    
    return mock_utils


@pytest.fixture
def ui_screenshot(request: pytest.FixtureRequest, app_instance: Any) -> Callable[[str], str]:
    """
    Fixture to capture UI screenshots during tests.
    
    This fixture provides a function to capture screenshots of the application
    UI at different points during test execution, which can be used for debugging
    or visual verification.
    
    Usage:
        def test_ui_appearance(app_instance, ui_screenshot):
            # Perform actions
            screenshot_path = ui_screenshot("after_button_click")
    
    Args:
        request: The pytest request object
        app_instance: The application instance
        
    Returns:
        Function that captures screenshots and returns the path
    """
    screenshots_dir = Path("test_screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    
    # Get the test name to use in the screenshot filename
    test_name = request.node.name
    
    def capture_screenshot(label: str = "") -> str:
        """
        Capture a screenshot of the current UI state.
        
        Args:
            label: Optional label to include in the filename
            
        Returns:
            Path to the saved screenshot
        """
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{test_name}_{label}_{timestamp}.png"
        
        if label:
            filename = f"{test_name}_{label}_{timestamp}.png"
        else:
            filename = f"{test_name}_{timestamp}.png"
        
        file_path = screenshots_dir / filename
        
        # Try different methods of capturing screenshot based on app type
        if hasattr(app_instance, "capture_screenshot"):
            app_instance.capture_screenshot(str(file_path))
        elif hasattr(app_instance, "screenshot"):
            app_instance.screenshot(str(file_path))
        elif hasattr(app_instance, "main_window") and hasattr(app_instance.main_window(), "grab"):
            # Qt-based applications
            pixmap = app_instance.main_window().grab()
            pixmap.save(str(file_path))
        else:
            # Generic fallback attempt for desktop screenshots
            try:
                import PIL.ImageGrab
                screenshot = PIL.ImageGrab.grab()
                screenshot.save(str(file_path))
            except (ImportError, Exception) as e:
                print(f"Could not capture screenshot: {str(e)}")
                return ""
        
        return str(file_path)
    
    return capture_screenshot


@pytest.fixture
def isolated_config() -> Generator[Dict[str, Any], None, None]:
    """
    Fixture providing an isolated configuration environment.
    
    This fixture creates a temporary environment for application configuration
    to prevent tests from modifying the user's actual settings.
    
    Usage:
        def test_with_custom_config(app_instance, isolated_config):
            isolated_config['theme'] = 'dark'
            app_instance.load_config(isolated_config)
    
    Returns:
        Dictionary for storing configuration values
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        config = {
            "config_dir": temp_dir,
            "is_test_environment": True,
        }
        
        # Create an empty config file
        config_file = Path(temp_dir) / "test_config.json"
        config_file.write_text("{}")
        
        config["config_file"] = str(config_file)
        
        yield config
