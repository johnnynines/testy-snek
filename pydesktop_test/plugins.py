"""
PyTest plugins for the PyDesktop Test framework.

This module contains plugins that extend pytest's functionality
for desktop application testing.
"""

import os
import pytest
from typing import Optional

from pydesktop_test.reporting import TestReport
from pydesktop_test.dashboard import launch_dashboard


class DashboardPlugin:
    """
    Pytest plugin that generates interactive dashboard reports.
    
    This plugin automatically collects test results and screenshots,
    generating reports in a format suitable for the interactive dashboard.
    """
    
    def __init__(self):
        """Initialize the dashboard plugin."""
        self.current_report = None
        self.output_dir = os.path.join(os.getcwd(), "test_reports")
        self.screenshot_dir = os.path.join(os.getcwd(), "test_screenshots")
        self.launch_dashboard = False
        self.dashboard_port = 5500
        
    def pytest_cmdline_main(self, config):
        """Process command line arguments."""
        # Check for dashboard-related options
        if hasattr(config.option, "dashboard") and config.option.dashboard:
            self.launch_dashboard = True
        
        if hasattr(config.option, "dashboard_port") and config.option.dashboard_port:
            self.dashboard_port = config.option.dashboard_port
            
        if hasattr(config.option, "report_dir") and config.option.report_dir:
            self.output_dir = config.option.report_dir
            
        if hasattr(config.option, "screenshot_dir") and config.option.screenshot_dir:
            self.screenshot_dir = config.option.screenshot_dir
        
        # Create the output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    def pytest_sessionstart(self, session):
        """Initialize the test report at the start of the session."""
        self.current_report = TestReport()
        self.current_report.start()
    
    def pytest_runtest_logreport(self, report):
        """Process each test report as it's generated."""
        if not self.current_report:
            return
            
        # Skip setup/teardown phases unless they failed or were skipped
        if report.when != "call" and not (report.failed or report.skipped):
            return
            
        # Create test case data
        test_case = {
            "name": report.nodeid.split("::")[-1],
            "nodeid": report.nodeid,
            "status": "unknown",
            "duration": getattr(report, "duration", 0),
            "call": None,
            "screenshots": []
        }
        
        # Determine test status
        if report.passed:
            test_case["status"] = "passed"
        elif report.failed:
            test_case["status"] = "failed"
            # Add failure details
            if hasattr(report, "longrepr"):
                test_case["call"] = {
                    "longrepr": str(report.longrepr)
                }
        elif report.skipped:
            test_case["status"] = "skipped"
        
        # Look for screenshots associated with this test
        test_name = report.nodeid.replace("/", "_").replace(":", "_").replace("::", "_")
        for file in os.listdir(self.screenshot_dir):
            if file.startswith(test_name) and file.endswith((".png", ".jpg")):
                test_case["screenshots"].append(file)
                self.current_report.add_screenshot(file)
        
        # Add the test case to the report
        self.current_report.add_test_case(test_case)
    
    def pytest_sessionfinish(self, session, exitstatus):
        """Finalize and save the report when the session ends."""
        if not self.current_report:
            return
            
        # Finalize the report
        self.current_report.finish()
        
        # Add logs if available
        if hasattr(session, "config") and hasattr(session.config, "_report_log"):
            # Try to get logs from various places
            try:
                with open(session.config._report_log, "r") as f:
                    self.current_report.add_log(f.read())
            except (AttributeError, FileNotFoundError):
                pass
                
        # Save the report
        report_file = self.current_report.save(self.output_dir)
        
        # Launch the dashboard if requested
        if self.launch_dashboard:
            launch_dashboard(
                port=self.dashboard_port,
                data_dir=self.output_dir,
                open_browser=True
            )
    
    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
        """Add a dashboard summary to the terminal output."""
        if not hasattr(terminalreporter, "writer"):
            return
            
        if self.launch_dashboard:
            terminalreporter.write_sep("=", "dashboard")
            terminalreporter.write_line(f"Dashboard available at: http://localhost:{self.dashboard_port}")
            terminalreporter.write_line(f"Report saved to: {self.output_dir}")


# Add command line options for the dashboard
def pytest_addoption(parser):
    """Add pytest command line options for the dashboard."""
    group = parser.getgroup("pydesktop-dashboard")
    group.addoption(
        "--dashboard",
        action="store_true",
        help="Launch interactive dashboard after test run"
    )
    group.addoption(
        "--dashboard-port",
        type=int,
        default=5500,
        help="Port to run the dashboard server on (default: 5500)"
    )
    group.addoption(
        "--report-dir",
        type=str,
        help="Directory to save test reports in"
    )
    group.addoption(
        "--screenshot-dir",
        type=str,
        help="Directory to save screenshots in"
    )


# Register the dashboard plugin
@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """Configure pytest plugins."""
    # Register the dashboard plugin
    if not hasattr(config, "_pydesktop_dashboard_plugin"):
        dashboard_plugin = DashboardPlugin()
        config.pluginmanager.register(dashboard_plugin, "dashboard_plugin")
        config._pydesktop_dashboard_plugin = dashboard_plugin