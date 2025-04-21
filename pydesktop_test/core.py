"""
Core functionality for PyDesktop Test framework.

This module provides the main functions for test discovery and execution.
"""

import os
import sys
import pytest
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Callable

from .config import TestConfig
from .reporting import setup_reporting
from .utils import import_module_from_path, setup_environment


def run_tests(
    test_paths: Union[str, List[str]] = None,
    config: Optional[TestConfig] = None,
    markers: Optional[List[str]] = None,
    capture_output: bool = True,
    generate_html: bool = True,
    generate_coverage: bool = True,
    verbose: bool = True,
    parallel: bool = False,
    max_workers: int = None,
) -> Dict[str, Any]:
    """
    Run tests in the specified paths with the given configuration.
    
    Args:
        test_paths: Path or list of paths to test files or directories
        config: Test configuration object
        markers: List of markers to run tests with
        capture_output: Whether to capture stdout/stderr during tests
        generate_html: Whether to generate HTML reports
        generate_coverage: Whether to generate coverage reports
        verbose: Whether to output verbose test information
        parallel: Whether to run tests in parallel
        max_workers: Maximum number of parallel workers (if parallel=True)
        
    Returns:
        Dictionary containing test results and report paths
    """
    # Set default test path if none provided
    if test_paths is None:
        test_paths = ["tests"]
    elif isinstance(test_paths, str):
        test_paths = [test_paths]
    
    # Set up configuration
    config = config or TestConfig()
    
    # Build pytest arguments
    pytest_args = []
    
    # Add test paths
    pytest_args.extend(test_paths)
    
    # Add verbosity level
    if verbose:
        pytest_args.append("-v")
    
    # Add markers if specified
    if markers:
        for marker in markers:
            pytest_args.append(f"-m {marker}")
    
    # Configure output capture
    if not capture_output:
        pytest_args.append("-s")
    
    # Configure HTML reporting
    if generate_html:
        report_dir = config.get("report_dir", "test_reports")
        os.makedirs(report_dir, exist_ok=True)
        html_path = os.path.join(report_dir, "report.html")
        pytest_args.extend(["--html", html_path, "--self-contained-html"])
    
    # Configure coverage
    if generate_coverage:
        coverage_dir = config.get("coverage_dir", "coverage")
        os.makedirs(coverage_dir, exist_ok=True)
        pytest_args.extend([
            "--cov", config.get("coverage_package", "."),
            "--cov-report", f"html:{coverage_dir}",
            "--cov-report", "term"
        ])
    
    # Configure parallel execution
    if parallel:
        workers = max_workers if max_workers else "auto"
        pytest_args.extend(["-n", str(workers)])
    
    # Set up reporting and environment
    setup_reporting()
    setup_environment(config)
    
    # Run tests and capture results
    result = pytest.main(pytest_args)
    
    # Prepare result dictionary
    test_results = {
        "exit_code": result,
        "success": result == pytest.ExitCode.OK,
    }
    
    # Add report paths if generated
    if generate_html:
        test_results["html_report"] = os.path.abspath(html_path)
    
    if generate_coverage:
        test_results["coverage_report"] = os.path.abspath(coverage_dir)
    
    return test_results


def collect_tests(
    test_paths: Union[str, List[str]] = None,
    config: Optional[TestConfig] = None,
    markers: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Collect test information without running them.
    
    Args:
        test_paths: Path or list of paths to test files or directories
        config: Test configuration object
        markers: List of markers to filter tests
        
    Returns:
        List of dictionaries containing test information
    """
    # Set default test path if none provided
    if test_paths is None:
        test_paths = ["tests"]
    elif isinstance(test_paths, str):
        test_paths = [test_paths]
    
    # Set up configuration
    config = config or TestConfig()
    
    # Build pytest arguments for collection only
    pytest_args = ["--collect-only"]
    
    # Add test paths
    pytest_args.extend(test_paths)
    
    # Add markers if specified
    if markers:
        for marker in markers:
            pytest_args.append(f"-m {marker}")
    
    # Set up environment
    setup_environment(config)
    
    # Collect tests using pytest's collection mechanism
    collected_tests = []
    
    class TestCollector:
        def pytest_collection_modifyitems(self, items):
            for item in items:
                test_info = {
                    "name": item.name,
                    "path": str(item.fspath),
                    "module": item.module.__name__,
                    "markers": [m.name for m in item.iter_markers()],
                    "id": item.nodeid,
                }
                collected_tests.append(test_info)
    
    pytest.main(pytest_args, plugins=[TestCollector()])
    
    return collected_tests


def run_specific_test(test_id: str, config: Optional[TestConfig] = None) -> Dict[str, Any]:
    """
    Run a specific test identified by its nodeid.
    
    Args:
        test_id: The pytest nodeid of the test to run
        config: Test configuration object
        
    Returns:
        Dictionary containing test results
    """
    # Set up configuration
    config = config or TestConfig()
    
    # Set up reporting and environment
    setup_reporting()
    setup_environment(config)
    
    # Run the specific test
    result = pytest.main([test_id, "-v"])
    
    return {
        "exit_code": result,
        "success": result == pytest.ExitCode.OK,
        "test_id": test_id
    }
