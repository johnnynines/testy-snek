"""
Tests for the dashboard module.

This module tests the functionality of the dashboard visualization tools.
"""

import os
import pytest
import tempfile
import json
from pathlib import Path

from pydesktop_test.dashboard import Dashboard
from pydesktop_test.reporting import TestReport


def test_dashboard_initialization():
    """Test that the dashboard can be initialized with default parameters."""
    try:
        dashboard = Dashboard(port=5501)
        assert dashboard.port == 5501 or dashboard.port > 5501  # Port might be different if 5501 is taken
        assert os.path.exists(dashboard.data_dir)
        assert os.path.exists(dashboard.screenshot_dir)
    except ImportError:
        pytest.skip("Flask not available, skipping dashboard tests")


def test_report_loading():
    """Test that the dashboard can load test reports."""
    try:
        # Create a temporary directory for test reports
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test report
            report = TestReport(report_id="test_report_1")
            report.add_test_case({
                "name": "test_example",
                "nodeid": "test_module.py::test_example",
                "status": "passed",
                "duration": 0.1
            })
            report.add_test_case({
                "name": "test_failing",
                "nodeid": "test_module.py::test_failing",
                "status": "failed",
                "duration": 0.2,
                "call": {
                    "longrepr": "AssertionError: Expected True but got False"
                }
            })
            
            # Save the report to the temporary directory
            report_path = report.save(temp_dir)
            
            # Initialize dashboard with the temporary directory
            dashboard = Dashboard(port=5502, data_dir=temp_dir)
            
            # Test report loading
            reports = dashboard._load_test_reports()
            
            # Verify that the report was loaded correctly
            assert len(reports) == 1
            assert reports[0]["id"] == "test_report_1"
            assert reports[0]["total_tests"] == 2
            assert reports[0]["passed"] == 1
            assert reports[0]["failed"] == 1
    except ImportError:
        pytest.skip("Flask not available, skipping dashboard tests")


def test_dashboard_template():
    """Test that the dashboard template renders correctly."""
    try:
        dashboard = Dashboard(port=5503)
        template = dashboard._get_dashboard_template()
        
        # Verify that the template contains key elements
        assert "PyDesktop Test Dashboard" in template
        assert "Test Reports" in template
        assert "Run Tests" in template
        assert "Report Details" in template
    except ImportError:
        pytest.skip("Flask not available, skipping dashboard tests")