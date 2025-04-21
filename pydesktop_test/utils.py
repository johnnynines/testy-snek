"""
Utility functions for PyDesktop Test.

This module provides miscellaneous helper functions used by other parts of the framework.
"""

import os
import sys
import time
import inspect
import importlib.util
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union, Type

from .config import TestConfig


def import_module_from_path(module_path: Union[str, Path]) -> Any:
    """
    Import a Python module from a file path.
    
    Args:
        module_path: Path to the Python module file
        
    Returns:
        The imported module
        
    Raises:
        ImportError: If the module cannot be imported
    """
    module_path = Path(module_path)
    
    if not module_path.exists():
        raise ImportError(f"Module file not found: {module_path}")
    
    # Generate a module name based on the file path
    module_name = module_path.stem
    
    # Import the module
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module spec for {module_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    
    return module


def wait_for(
    condition_func: Callable[[], bool], 
    timeout: float = 5.0, 
    interval: float = 0.1,
    error_message: str = "Condition not met within timeout"
) -> None:
    """
    Wait for a condition to be true within a timeout.
    
    Args:
        condition_func: Function that returns True when the condition is met
        timeout: Maximum time to wait (seconds)
        interval: Time between checks (seconds)
        error_message: Message for the TimeoutError exception
        
    Raises:
        TimeoutError: If the condition is not met within the timeout
    """
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        if condition_func():
            return
        time.sleep(interval)
    
    raise TimeoutError(error_message)


def setup_environment(config: TestConfig) -> None:
    """
    Set up the test environment based on configuration.
    
    Args:
        config: Test configuration
    """
    # Set environment variables for testing
    os.environ["PYDESKTOP_TEST_ENVIRONMENT"] = config.get("environment", "test")
    
    # Set up Python path to include the project root
    project_root = Path.cwd()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Configure basic logging
    if config.get("configure_logging", True):
        import logging
        log_level = getattr(logging, config.get("log_level", "INFO"))
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )


def get_desktop_app_class(app_module_path: Optional[str] = None, app_class_name: Optional[str] = None) -> Optional[Type]:
    """
    Get the application class to use for testing.
    
    Args:
        app_module_path: Path to the module containing the app class
        app_class_name: Name of the app class
        
    Returns:
        The application class, or None if not found
    """
    # If app_module_path is provided, import the module
    if app_module_path:
        try:
            module = import_module_from_path(app_module_path)
            
            # If app_class_name is provided, get that class
            if app_class_name:
                if hasattr(module, app_class_name):
                    return getattr(module, app_class_name)
            else:
                # Try to find a class that looks like an app class
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and any(
                        hasattr(obj, attr) for attr in 
                        ["run", "start", "main_window", "window", "windows"]
                    ):
                        return obj
        except Exception as e:
            print(f"Error importing app class: {str(e)}")
            return None
    
    # If app_class_name is provided but not app_module_path, look in sys.modules
    if app_class_name:
        for module_name, module in sys.modules.items():
            if hasattr(module, app_class_name):
                return getattr(module, app_class_name)
    
    return None


def find_tests_in_directory(directory: Union[str, Path]) -> List[Path]:
    """
    Find test files in a directory.
    
    Args:
        directory: Directory to search for tests
        
    Returns:
        List of paths to test files
    """
    directory = Path(directory)
    
    if not directory.exists():
        return []
    
    # Find files that look like test files
    test_files = []
    
    for path in directory.glob("**/*.py"):
        # Check if it's a test file
        if (
            path.name.startswith("test_") or 
            path.name.endswith("_test.py") or
            "test" in path.parent.name.lower()
        ):
            test_files.append(path)
    
    return test_files


def make_test_id(module_name: str, class_name: Optional[str], function_name: str) -> str:
    """
    Create a test ID in the format used by pytest.
    
    Args:
        module_name: Name of the module
        class_name: Name of the class (optional)
        function_name: Name of the function
        
    Returns:
        Test ID string
    """
    if class_name:
        return f"{module_name}::{class_name}::{function_name}"
    else:
        return f"{module_name}::{function_name}"


def format_test_result(test_id: str, result: str, duration: float, message: Optional[str] = None) -> str:
    """
    Format a test result for display.
    
    Args:
        test_id: Test identifier
        result: Result status (e.g., "PASS", "FAIL")
        duration: Test duration in seconds
        message: Optional message (e.g., error message for failures)
        
    Returns:
        Formatted string
    """
    duration_str = f"{duration:.3f}s"
    base_result = f"{result} {test_id} ({duration_str})"
    
    if message:
        return f"{base_result}\n    {message}"
    else:
        return base_result


def parse_test_filter(filter_str: str) -> Dict[str, str]:
    """
    Parse a test filter string into a dictionary.
    
    Format: module_name[::class_name[::function_name]]
    
    Args:
        filter_str: Filter string
        
    Returns:
        Dictionary with filter components
    """
    parts = filter_str.split("::")
    filter_dict = {"module": parts[0]}
    
    if len(parts) > 1:
        filter_dict["class"] = parts[1]
    
    if len(parts) > 2:
        filter_dict["function"] = parts[2]
    
    return filter_dict
