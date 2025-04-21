#!/usr/bin/env python
"""
Simple script to run the tests using the PyDesktop Test framework.

This script provides a convenient way to test the framework modules,
demonstrating the features of the PyDesktop Test framework.
"""

import os
import sys
import pytest
import argparse
from pathlib import Path


def run_tests(launch_dashboard=False):
    """
    Run tests for the PyDesktop Test framework modules.
    
    This function focuses on testing the framework itself rather than the GUI examples
    which require Tkinter with display capabilities.
    
    Args:
        launch_dashboard: Whether to launch the dashboard after running tests
    """
    # Ensure the package is in the Python path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    print("Testing PyDesktop Test Framework...")
    
    # Create output directories
    report_dir = "test_reports"
    os.makedirs(report_dir, exist_ok=True)
    os.makedirs("example_reports", exist_ok=True)
    os.makedirs("example_coverage", exist_ok=True)
    
    # Create some simple unit tests for demonstration
    test_file = "test_framework.py"
    with open(test_file, "w") as f:
        f.write('''
import pytest
from pydesktop_test.config import TestConfig

def test_config_defaults():
    # Test that the default configuration works
    config = TestConfig()
    assert config.get("test_dir") == "tests"
    assert config.get("report_dir") == "test_reports"
    assert config.get("verbose") == True

def test_config_update():
    # Test updating configuration values
    config = TestConfig()
    config.update({"verbose": False, "custom_value": 42})
    assert config.get("verbose") == False
    assert config.get("custom_value") == 42
    
def test_config_set_get():
    # Test setting and getting configuration values
    config = TestConfig()
    config.set("new_value", "test")
    assert config.get("new_value") == "test"
    assert config.get("nonexistent") is None
    assert config.get("nonexistent", "default") == "default"
''')
    
    # Run pytest directly
    args = [
        "-xvs",  # x: exit on first failure, v: verbose, s: don't capture output
        "--html=example_reports/report.html",
        "--self-contained-html",
        "--cov=pydesktop_test",
        "--cov-report=html:example_coverage",
        "--cov-report=term",
        # We'll enable the dashboard later via our plugin system
        test_file  # Our test file
    ]
    
    # Run with pytest
    result = pytest.main(args)
    
    # Clean up temporary test file
    if os.path.exists(test_file):
        os.unlink(test_file)
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Result: {'SUCCESS' if result == 0 else 'FAILURE'}")
    print("===================\n")
    
    # Launch the dashboard if requested
    if launch_dashboard:
        try:
            from pydesktop_test.dashboard import Dashboard
            print("\nLaunching interactive dashboard...")
            dashboard = Dashboard(data_dir=report_dir)
            
            print(f"Dashboard will be available at: http://localhost:{dashboard.port}")
            print(f"Loading reports from: {dashboard.data_dir}")
            
            try:
                dashboard.start()  # This will block until stopped with Ctrl+C
            except KeyboardInterrupt:
                print("\nDashboard stopped.")
            except Exception as e:
                print(f"\nError running dashboard: {e}")
        except ImportError as e:
            print(f"Error launching dashboard: {e}")
            print("Make sure Flask is installed: pip install flask")
    
    # Return success or failure
    return 0 if result == 0 else 1


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run PyDesktop Test framework tests")
    parser.add_argument(
        "--dashboard", "-d", 
        action="store_true", 
        help="Launch the interactive dashboard after running tests"
    )
    args = parser.parse_args()
    
    # Run tests with dashboard if requested
    sys.exit(run_tests(launch_dashboard=args.dashboard))
