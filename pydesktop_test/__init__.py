"""
PyDesktop Test - A PyTest-based testing framework for Python desktop applications.

This framework provides enhanced testing capabilities for Python desktop applications,
including custom fixtures, assertions, and reporting mechanisms.
"""

__version__ = "0.1.0"

from .core import run_tests, collect_tests
from .assertions import (
    assert_window_exists, 
    assert_control_exists,
    assert_control_value, 
    assert_control_enabled,
    assert_control_visible,
    assert_dialog_shown,
    assert_ui_state
)
from .fixtures import (
    app_instance, 
    main_window, 
    temp_data, 
    mock_dialog,
    ui_screenshot,
    isolated_config
)
from .dashboard import launch_dashboard
from .reporting import TestReport, TestReportGenerator
from .plugins import DashboardPlugin

__all__ = [
    # Core functionality
    'run_tests',
    'collect_tests',
    
    # Assertions
    'assert_window_exists',
    'assert_control_exists',
    'assert_control_value',
    'assert_control_enabled',
    'assert_control_visible',
    'assert_dialog_shown',
    'assert_ui_state',
    
    # Fixtures
    'app_instance',
    'main_window',
    'temp_data',
    'mock_dialog',
    'ui_screenshot',
    'isolated_config',
    
    # Dashboard and Reporting
    'launch_dashboard',
    'TestReport',
    'TestReportGenerator',
    'DashboardPlugin'
]
