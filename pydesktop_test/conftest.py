"""
PyTest configuration file for PyDesktop Test.

This file defines global fixtures and hooks that are automatically used by pytest.
"""

import os
import sys
import pytest
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from .fixtures import (
    app_instance, 
    main_window, 
    temp_data, 
    mock_dialog,
    ui_screenshot,
    isolated_config
)
from .config import TestConfig, load_config


# Make fixtures available to all tests
pytest_plugins = [
    # Empty string indicates fixtures are in this module
    ""
]


def pytest_addoption(parser):
    """
    Add custom command-line options to pytest.
    """
    group = parser.getgroup("pydesktop", "PyDesktop Test Options")
    
    group.addoption(
        "--app-class",
        action="store",
        dest="app_class",
        help="Full import path to the application class"
    )
    
    group.addoption(
        "--config-file",
        action="store",
        dest="config_file",
        help="Path to the test configuration file"
    )
    
    group.addoption(
        "--screenshot-dir",
        action="store",
        dest="screenshot_dir",
        default="test_screenshots",
        help="Directory to store screenshots"
    )
    
    group.addoption(
        "--ui-timeout",
        action="store",
        dest="ui_timeout",
        type=float,
        default=2.0,
        help="Timeout for UI operations"
    )


@pytest.fixture(scope="session", autouse=True)
def pydesktop_config(request):
    """
    Fixture that provides test configuration.
    
    This fixture loads configuration from files or command-line options
    and makes it available to tests.
    """
    # Try to load config from command-line option
    config_file = request.config.getoption("--config-file")
    
    # Load the configuration
    config = load_config(config_file)
    
    # Update with command-line options
    app_class = request.config.getoption("--app-class")
    if app_class:
        config.set("app_class", app_class)
    
    screenshot_dir = request.config.getoption("--screenshot-dir")
    if screenshot_dir:
        config.set("screenshot_dir", screenshot_dir)
    
    ui_timeout = request.config.getoption("--ui-timeout")
    if ui_timeout:
        config.set("ui_timeout", ui_timeout)
    
    # Create screenshot directory if it doesn't exist
    os.makedirs(config.get("screenshot_dir", "test_screenshots"), exist_ok=True)
    
    return config


def pytest_configure(config):
    """
    Configure pytest before tests start.
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Register custom markers
    config.addinivalue_line(
        "markers", "desktop: mark a test as a desktop application test"
    )
    config.addinivalue_line(
        "markers", "ui: mark a test as a UI test"
    )
    config.addinivalue_line(
        "markers", "app_class(cls, wait_time): specify the application class and optional wait time"
    )
    config.addinivalue_line(
        "markers", "requires_display: mark a test that requires a display to run"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test items during collection.
    
    This hook is used to skip tests that require a display if no display is available.
    """
    # Check if we have a display
    has_display = True
    
    # On Unix-like systems, check for X display
    if sys.platform != "win32" and not os.environ.get("DISPLAY"):
        has_display = False
    
    if not has_display:
        skip_no_display = pytest.mark.skip(reason="No display available")
        for item in items:
            if "requires_display" in item.keywords or "ui" in item.keywords:
                item.add_marker(skip_no_display)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Process test outcome to capture screenshots on failures.
    """
    # Execute the hook normally
    outcome = yield
    result = outcome.get_result()
    
    # Check if the test failed and we have ui_screenshot fixture
    if result.when == "call" and result.failed:
        # Try to capture a screenshot if the ui_screenshot fixture is available
        try:
            if "ui_screenshot" in item.fixturenames:
                screenshot_func = item.funcargs["ui_screenshot"]
                screenshot_path = screenshot_func("failure")
                
                if screenshot_path:
                    result.screenshot = screenshot_path
                    
                    # Add to report sections
                    if hasattr(result, "sections"):
                        result.sections.append((
                            "Screenshot", 
                            f"Screenshot saved to: {screenshot_path}"
                        ))
        except Exception as e:
            print(f"Failed to capture screenshot: {str(e)}")
