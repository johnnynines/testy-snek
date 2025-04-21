"""
Enhanced reporting utilities for test results.

This module provides custom reporting functionalities including rich console output,
HTML report generation, and test result visualization.
"""

import os
import time
import json
import pytest
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

# Import these conditionally since they're not part of the standard library
try:
    import rich
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def setup_reporting():
    """
    Set up enhanced reporting for tests.
    
    This function configures pytest to use custom reporting hooks
    for better visualization of test results.
    """
    # Register plugins if rich is available
    if HAS_RICH:
        # Create a pytest plugin
        class RichReporter:
            def __init__(self):
                self.console = Console()
                self.total_passed = 0
                self.total_failed = 0
                self.total_skipped = 0
                self.total_xfailed = 0
                self.start_time = time.time()
                self.current_test = None
                self.test_progress = None
            
            def pytest_sessionstart(self, session):
                self.console.print(Panel.fit(
                    "PyDesktop Test Framework", 
                    title="Starting Test Session",
                    subtitle=f"Python {os.sys.version.split()[0]}"
                ))
                self.start_time = time.time()
            
            def pytest_collection_modifyitems(self, items):
                self.console.print(f"[bold blue]Collected [cyan]{len(items)}[/cyan] tests[/bold blue]")
                
                # Create a progress bar
                self.test_progress = Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(),
                    TextColumn("[bold]{task.completed}/{task.total}"),
                    TimeElapsedColumn(),
                )
                self.progress_task = self.test_progress.add_task("[bold blue]Running tests", total=len(items))
                
                if len(items) > 0:
                    self.test_progress.start()
            
            def pytest_runtest_logstart(self, nodeid, location):
                self.current_test = nodeid
                if self.test_progress:
                    self.test_progress.update(self.progress_task, description=f"Running: {nodeid}")
            
            def pytest_runtest_logreport(self, report):
                if report.when == "call" or (report.when == "setup" and report.skipped):
                    if self.test_progress:
                        self.test_progress.advance(self.progress_task)
                    
                    if report.passed:
                        if report.when == "call":
                            self.total_passed += 1
                            status = "[bold green]PASSED[/bold green]"
                    elif report.failed:
                        if hasattr(report, "wasxfail"):
                            self.total_xfailed += 1
                            status = "[bold yellow]XFAILED[/bold yellow]"
                        else:
                            self.total_failed += 1
                            status = "[bold red]FAILED[/bold red]"
                    elif report.skipped:
                        self.total_skipped += 1
                        status = "[bold yellow]SKIPPED[/bold yellow]"
            
            def pytest_sessionfinish(self, session, exitstatus):
                if self.test_progress:
                    self.test_progress.stop()
                
                duration = time.time() - self.start_time
                
                # Create summary table
                table = Table(title="Test Results Summary")
                table.add_column("Status", style="bold")
                table.add_column("Count", style="cyan")
                
                table.add_row("Passed", str(self.total_passed))
                table.add_row("Failed", str(self.total_failed))
                table.add_row("Skipped", str(self.total_skipped))
                table.add_row("XFailed", str(self.total_xfailed))
                table.add_row("Total", str(self.total_passed + self.total_failed + self.total_skipped + self.total_xfailed))
                table.add_row("Duration", f"{duration:.2f} seconds")
                
                self.console.print(table)
                
                # Print final status
                if self.total_failed == 0:
                    status_style = "green"
                    status_text = "SUCCESS"
                else:
                    status_style = "red"
                    status_text = "FAILURE"
                
                self.console.print(Panel.fit(
                    f"[bold {status_style}]{status_text}[/bold {status_style}]: {self.total_passed} passed, {self.total_failed} failed, {self.total_skipped} skipped",
                    title="Test Session Finished",
                    subtitle=f"Duration: {duration:.2f} seconds"
                ))
        
        # Register the plugin with pytest
        if not hasattr(pytest, "_pydesktop_test_rich_reporter_registered"):
            # Newer versions of pytest don't have register_plugin
            # Instead, we need to use pytest_configure hook
            reporter = RichReporter()
            if hasattr(pytest, "hookimpl"):
                @pytest.hookimpl()
                def pytest_configure(config):
                    config.pluginmanager.register(reporter, "rich_reporter")
                pytest.hookimpl = pytest.hookimpl
            setattr(pytest, "_pydesktop_test_rich_reporter_registered", True)


class TestReportGenerator:
    """
    Generate detailed test reports in various formats.
    """
    
    @staticmethod
    def save_json_report(report_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Save test results as a JSON report.
        
        Args:
            report_data: Dictionary containing test result data
            output_path: Optional file path to save the report to
            
        Returns:
            Path to the saved report file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("test_reports")
            output_dir.mkdir(exist_ok=True)
            output_path = str(output_dir / f"test_report_{timestamp}.json")
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Add timestamp to the report
        report_data["timestamp"] = datetime.now().isoformat()
        
        # Write the report to file
        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)
        
        return output_path
    
    @staticmethod
    def generate_summary_report(test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary report from test results.
        
        Args:
            test_results: Dictionary containing raw test result data
            
        Returns:
            Dictionary containing the summary report
        """
        # Extract key metrics
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": test_results.get("total", 0),
            "passed": test_results.get("passed", 0),
            "failed": test_results.get("failed", 0),
            "skipped": test_results.get("skipped", 0),
            "errors": test_results.get("errors", 0),
            "duration": test_results.get("duration", 0),
            "success_percentage": 0
        }
        
        # Calculate success percentage if there were any tests
        if summary["total_tests"] > 0:
            summary["success_percentage"] = (summary["passed"] / summary["total_tests"]) * 100
        
        return summary
    
    @staticmethod
    def print_console_summary(summary: Dict[str, Any]) -> None:
        """
        Print a test summary to the console.
        
        Args:
            summary: Dictionary containing summary report data
        """
        if HAS_RICH:
            console = Console()
            
            table = Table(title="Test Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Total Tests", str(summary.get("total_tests", 0)))
            table.add_row("Passed", str(summary.get("passed", 0)))
            table.add_row("Failed", str(summary.get("failed", 0)))
            table.add_row("Skipped", str(summary.get("skipped", 0)))
            table.add_row("Success Rate", f"{summary.get('success_percentage', 0):.2f}%")
            table.add_row("Duration", f"{summary.get('duration', 0):.2f} seconds")
            
            console.print(table)
        else:
            # Fallback to standard print
            print("\n=== Test Summary ===")
            print(f"Total Tests: {summary.get('total_tests', 0)}")
            print(f"Passed: {summary.get('passed', 0)}")
            print(f"Failed: {summary.get('failed', 0)}")
            print(f"Skipped: {summary.get('skipped', 0)}")
            print(f"Success Rate: {summary.get('success_percentage', 0):.2f}%")
            print(f"Duration: {summary.get('duration', 0):.2f} seconds")
            print("===================\n")


class TestReport:
    """
    Collects and manages test report data for visualization.
    
    This class provides methods for collecting test result data during test runs
    and saving it in a format suitable for the dashboard visualization.
    """
    
    def __init__(self, report_id: Optional[str] = None):
        """
        Initialize a new test report.
        
        Args:
            report_id: Optional ID for the report (defaults to timestamp)
        """
        self.id = report_id or datetime.now().strftime("test_%Y%m%d_%H%M%S")
        self.timestamp = datetime.now().isoformat()
        self.start_time = time.time()
        self.end_time = None
        self.duration = 0
        self.summary = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "error": 0
        }
        self.test_cases = []
        self.screenshots = []
        self.logs = ""
        
    def start(self) -> None:
        """Start the test run timer."""
        self.start_time = time.time()
        
    def finish(self) -> None:
        """Finish the test run and calculate duration."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        
    def add_test_case(self, test_data: Dict[str, Any]) -> None:
        """
        Add a test case to the report.
        
        Args:
            test_data: Dictionary with test case data
        """
        self.test_cases.append(test_data)
        
        # Update summary statistics
        self.summary["total"] += 1
        status = test_data.get("status")
        if status == "passed":
            self.summary["passed"] += 1
        elif status == "failed":
            self.summary["failed"] += 1
        elif status == "skipped":
            self.summary["skipped"] += 1
        elif status == "error":
            self.summary["error"] += 1
    
    def add_screenshot(self, screenshot_path: str) -> None:
        """
        Add a screenshot to the report.
        
        Args:
            screenshot_path: Path to the screenshot file
        """
        if screenshot_path not in self.screenshots:
            self.screenshots.append(screenshot_path)
    
    def add_log(self, log_text: str) -> None:
        """
        Add log text to the report.
        
        Args:
            log_text: Log text to add
        """
        self.logs += log_text + "\n"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the report to a dictionary.
        
        Returns:
            Dictionary representation of the report
        """
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "duration": self.duration,
            "summary": self.summary,
            "test_cases": self.test_cases,
            "screenshots": self.screenshots,
            "logs": self.logs
        }
    
    def save(self, output_dir: Optional[str] = None) -> str:
        """
        Save the report to a JSON file.
        
        Args:
            output_dir: Optional directory to save the report in
            
        Returns:
            Path to the saved report file
        """
        if not output_dir:
            output_dir = os.path.join(os.getcwd(), "test_reports")
        
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Finalize the report if not already done
        if self.end_time is None:
            self.finish()
        
        # Create the output file path
        output_path = os.path.join(output_dir, f"{self.id}.json")
        
        # Save the report
        with open(output_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        
        return output_path
    
    @classmethod
    def from_pytest_session(cls, session) -> 'TestReport':
        """
        Create a TestReport from a pytest session.
        
        Args:
            session: pytest test session
            
        Returns:
            TestReport populated with session data
        """
        report = cls()
        report.start()
        
        # Process each test item
        for item in session.items:
            # This gets more complete data after tests run
            pass
        
        return report
    
    @classmethod
    def from_pytest_terminal_summary(cls, terminalreporter) -> 'TestReport':
        """
        Create a TestReport from pytest's terminal reporter.
        
        Args:
            terminalreporter: pytest's terminal reporter
            
        Returns:
            TestReport populated with session result data
        """
        report = cls()
        
        # Get stats from terminal reporter
        stats = terminalreporter.stats
        
        # Update summary
        report.summary["passed"] = len(stats.get("passed", []))
        report.summary["failed"] = len(stats.get("failed", []))
        report.summary["skipped"] = len(stats.get("skipped", []))
        report.summary["error"] = len(stats.get("error", []))
        report.summary["total"] = (
            report.summary["passed"] + 
            report.summary["failed"] + 
            report.summary["skipped"] + 
            report.summary["error"]
        )
        
        # Calculate duration
        report.duration = time.time() - report.start_time
        
        # Process test results
        for status in ["passed", "failed", "skipped", "error"]:
            for test_report in stats.get(status, []):
                test_case = {
                    "name": test_report.nodeid.split("::")[-1],
                    "nodeid": test_report.nodeid,
                    "status": status,
                    "duration": getattr(test_report, "duration", 0),
                    "call": None
                }
                
                # Add detailed information for failures
                if status == "failed" and hasattr(test_report, "longrepr"):
                    test_case["call"] = {
                        "longrepr": str(test_report.longrepr)
                    }
                
                report.test_cases.append(test_case)
        
        return report


def parse_junit_xml(xml_path: str) -> Dict[str, Any]:
    """
    Parse JUnit XML file to extract test results.
    
    Args:
        xml_path: Path to the JUnit XML file
        
    Returns:
        Dictionary containing parsed test results
    """
    try:
        import xml.etree.ElementTree as ET
        
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Extract test suite information
        testsuite = root.find(".//testsuite")
        if testsuite is None:
            testsuite = root
        
        # Extract overall statistics
        result = {
            "name": testsuite.get("name", "Unknown"),
            "total": int(testsuite.get("tests", 0)),
            "failed": int(testsuite.get("failures", 0)),
            "errors": int(testsuite.get("errors", 0)),
            "skipped": int(testsuite.get("skipped", 0)),
            "passed": 0,  # Will calculate below
            "duration": float(testsuite.get("time", 0)),
            "timestamp": testsuite.get("timestamp", datetime.now().isoformat()),
            "tests": []
        }
        
        # Calculate passed tests
        result["passed"] = result["total"] - result["failed"] - result["errors"] - result["skipped"]
        
        # Extract individual test case information
        for testcase in testsuite.findall(".//testcase"):
            test_info = {
                "name": testcase.get("name", "Unknown"),
                "classname": testcase.get("classname", "Unknown"),
                "duration": float(testcase.get("time", 0)),
                "status": "passed"
            }
            
            # Check for failures
            failure = testcase.find("failure")
            if failure is not None:
                test_info["status"] = "failed"
                test_info["failure_message"] = failure.get("message", "")
                test_info["failure_text"] = failure.text
            
            # Check for errors
            error = testcase.find("error")
            if error is not None:
                test_info["status"] = "error"
                test_info["error_message"] = error.get("message", "")
                test_info["error_text"] = error.text
            
            # Check for skipped
            skipped = testcase.find("skipped")
            if skipped is not None:
                test_info["status"] = "skipped"
                test_info["skip_message"] = skipped.get("message", "")
            
            result["tests"].append(test_info)
        
        return result
    
    except Exception as e:
        print(f"Error parsing JUnit XML: {str(e)}")
        return {
            "name": "Error",
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 1,
            "skipped": 0,
            "duration": 0,
            "error": str(e),
            "tests": []
        }
