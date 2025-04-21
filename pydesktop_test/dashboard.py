"""
Interactive dashboard for test case visualization.

This module provides a web-based dashboard for visualizing and interacting
with test results from PyDesktop Test.
"""

import os
import time
import json
import threading
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

# Import flask conditionally since it might not be installed
try:
    import flask
    from flask import Flask, render_template_string, jsonify, send_file, request
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

# Import rich for console output if available
try:
    from rich.console import Console
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    console = None

# Import reporting module for report processing
from .reporting import TestReport


class Dashboard:
    """Interactive dashboard for visualizing test results."""

    def __init__(
        self,
        port: int = 5500,
        data_dir: Optional[str] = None,
        open_browser: bool = True,
    ):
        """
        Initialize the dashboard.
        
        Args:
            port: Port to run the dashboard server on
            data_dir: Directory containing test reports
            open_browser: Whether to automatically open the browser
        """
        if not HAS_FLASK:
            raise ImportError(
                "Flask is required for the dashboard. "
                "Install it with: pip install flask"
            )
        
        self.port = self._find_available_port(port)
        self.data_dir = data_dir or os.path.join(os.getcwd(), "test_reports")
        self.screenshot_dir = os.path.join(os.getcwd(), "test_screenshots")
        self.open_browser = open_browser
        self.app = Flask(__name__)
        self._configure_routes()
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.screenshot_dir, exist_ok=True)

    def _find_available_port(self, start_port: int) -> int:
        """
        Find an available port starting from the given port.
        
        Args:
            start_port: Starting port number
            
        Returns:
            Available port number
        """
        import socket
        
        port = start_port
        max_port = start_port + 100  # Limit to 100 ports to avoid infinite loop
        
        while port < max_port:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(("127.0.0.1", port))
                s.close()
                return port
            except OSError:
                port += 1
        
        # If no ports are available, return the original
        return start_port

    def _configure_routes(self) -> None:
        """Configure the Flask routes for the dashboard."""
        app = self.app
        
        @app.route("/")
        def index():
            """Render the main dashboard page."""
            return render_template_string(self._get_dashboard_template())
        
        @app.route("/api/reports")
        def test_reports():
            """Get all test reports."""
            reports = self._load_test_reports()
            return jsonify(reports)
        
        @app.route("/api/reports/<report_id>")
        def test_report(report_id):
            """Get a specific test report by ID."""
            report_path = os.path.join(self.data_dir, f"{report_id}.json")
            
            if not os.path.exists(report_path):
                return jsonify({"error": "Report not found"}), 404
                
            with open(report_path, "r") as f:
                report_data = json.load(f)
                
            return jsonify(report_data)
        
        @app.route("/screenshots/<path:filename>")
        def screenshots(filename):
            """Serve screenshot files."""
            return send_file(os.path.join(self.screenshot_dir, filename))
            
        @app.route("/api/run", methods=["POST"])
        def run_tests():
            """Run tests from the dashboard."""
            data = request.json
            test_paths = data.get("test_paths", ["."])
            markers = data.get("markers", None)
            
            # Run in a separate thread to avoid blocking
            def run():
                from .core import run_tests
                result = run_tests(
                    test_paths=test_paths,
                    markers=markers,
                    generate_html=True,
                    generate_coverage=True
                )
                return result
                
            thread = threading.Thread(target=run)
            thread.daemon = True
            thread.start()
            
            return jsonify({"status": "running"})

    def _load_test_reports(self) -> List[Dict[str, Any]]:
        """
        Load all test reports from the data directory.
        
        Returns:
            List of test report summaries
        """
        reports = []
        
        # Check if directory exists
        if not os.path.exists(self.data_dir):
            return reports
            
        # Find all JSON files in the directory
        for file in os.listdir(self.data_dir):
            if file.endswith(".json"):
                try:
                    report_path = os.path.join(self.data_dir, file)
                    with open(report_path, "r") as f:
                        data = json.load(f)
                        
                    # Extract basic summary data
                    summary = {
                        "id": data.get("id", file.replace(".json", "")),
                        "timestamp": data.get("timestamp", "Unknown"),
                        "duration": data.get("duration", 0),
                        "total_tests": data.get("summary", {}).get("total", 0),
                        "passed": data.get("summary", {}).get("passed", 0),
                        "failed": data.get("summary", {}).get("failed", 0),
                        "skipped": data.get("summary", {}).get("skipped", 0),
                        "error": data.get("summary", {}).get("error", 0)
                    }
                    
                    reports.append(summary)
                except Exception as e:
                    if HAS_RICH and console:
                        console.print(f"[red]Error loading report {file}: {str(e)}[/red]")
                    else:
                        print(f"Error loading report {file}: {str(e)}")
        
        # Sort reports by timestamp (newest first)
        reports.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return reports

    def _get_dashboard_template(self) -> str:
        """
        Get the HTML template for the dashboard.
        
        Returns:
            HTML template string
        """
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyDesktop Test Dashboard</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            padding-top: 20px;
            color: var(--bs-body-color);
            background-color: var(--bs-body-bg);
        }
        .dashboard-header {
            margin-bottom: 30px;
        }
        .card {
            margin-bottom: 20px;
            border-color: var(--bs-border-color);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
            background-color: var(--bs-tertiary-bg);
        }
        .test-details {
            margin-top: 20px;
        }
        .chart-container {
            position: relative;
            height: 250px;
            margin-bottom: 20px;
        }
        .screenshot-container {
            margin: 10px 0;
            border: 1px solid var(--bs-border-color);
            padding: 10px;
            border-radius: 5px;
        }
        .screenshot-container img {
            max-width: 100%;
            max-height: 300px;
            display: block;
            margin: 0 auto;
        }
        .badge {
            font-size: 0.9rem;
        }
        .test-item {
            cursor: pointer;
            padding: 10px;
            border-radius: 5px;
            border-left: 3px solid transparent;
            transition: background-color 0.2s ease;
        }
        .test-item:hover {
            background-color: var(--bs-tertiary-bg);
            border-left: 3px solid var(--bs-primary);
        }
        .test-item.active {
            background-color: var(--bs-tertiary-bg);
            border-left: 3px solid var(--bs-primary);
        }
        pre {
            background-color: var(--bs-tertiary-bg);
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .log-container {
            max-height: 400px;
            overflow-y: auto;
            background-color: var(--bs-tertiary-bg);
            border-radius: 5px;
            padding: 10px;
        }
        .chart-container {
            position: relative;
            height: 200px;
            width: 100%;
            margin-bottom: 20px;
        }
        .test-status-passed {
            color: var(--bs-success);
        }
        .test-status-failed {
            color: var(--bs-danger);
        }
        .test-status-skipped {
            color: var(--bs-warning);
        }
        .test-summary-card {
            text-align: center;
        }
        .test-summary-number {
            font-size: 2rem;
            font-weight: bold;
        }
        .dashboard-icon {
            font-size: 1.2rem;
            margin-right: 0.5rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="dashboard-header">
            <h1 class="display-5">PyDesktop Test Dashboard</h1>
            <p class="lead">Interactive test result visualizer</p>
        </div>

        <div class="row">
            <div class="col-md-4">
                <div class="card mb-4">
                    <div class="card-header bg-primary text-white">
                        Test Reports
                    </div>
                    <div class="card-body">
                        <div id="reportsList" class="list-group">
                            <div class="text-center p-3">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <p class="mt-2">Loading reports...</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card mb-4">
                    <div class="card-header bg-info text-white">
                        Historical Trends
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="trendChart"></canvas>
                        </div>
                        <div id="noTrendData" class="text-center p-3" style="display: none;">
                            <p>Need more test runs to show trends</p>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header bg-secondary text-white">
                        Run Tests
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <label for="testPaths" class="form-label">Test Paths (comma separated)</label>
                            <input type="text" class="form-control" id="testPaths" placeholder="tests">
                        </div>
                        <div class="mb-3">
                            <label for="markers" class="form-label">Markers (comma separated)</label>
                            <input type="text" class="form-control" id="markers" placeholder="e.g., smoke, gui">
                        </div>
                        <button id="runTestsBtn" class="btn btn-primary">Run Tests</button>
                    </div>
                </div>
            </div>

            <div class="col-md-8">
                <div id="reportDetails">
                    <div class="card">
                        <div class="card-header bg-info text-white">
                            Report Details
                        </div>
                        <div class="card-body">
                            <p class="text-center">Select a report to view details</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Load reports when the page loads
            loadReports();

            // Set up run tests button
            document.getElementById('runTestsBtn').addEventListener('click', runTests);
        });

        // Load all test reports
        function loadReports() {
            fetch('/api/reports')
                .then(response => response.json())
                .then(reports => {
                    const reportsList = document.getElementById('reportsList');
                    
                    if (reports.length === 0) {
                        reportsList.innerHTML = '<p class="text-center">No reports found</p>';
                        return;
                    }
                    
                    reportsList.innerHTML = '';
                    
                    // Generate trend data for historical view
                    if (reports.length > 1) {
                        createHistoricalTrendChart(reports);
                    }
                    
                    reports.forEach(report => {
                        const passRate = report.total_tests > 0 
                            ? ((report.passed / report.total_tests) * 100).toFixed(1) 
                            : 0;
                            
                        const date = new Date(report.timestamp);
                        const formattedDate = `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
                        
                        const reportItem = document.createElement('a');
                        reportItem.href = '#';
                        reportItem.className = 'list-group-item list-group-item-action';
                        reportItem.innerHTML = `
                            <div class="d-flex justify-content-between align-items-center">
                                <h6 class="mb-1">${formattedDate}</h6>
                                <span class="badge ${passRate >= 90 ? 'bg-success' : passRate >= 70 ? 'bg-warning' : 'bg-danger'}">${passRate}%</span>
                            </div>
                            <div class="d-flex justify-content-between">
                                <small>Tests: ${report.total_tests}</small>
                                <div>
                                    <span class="badge bg-success">${report.passed}</span>
                                    <span class="badge bg-danger">${report.failed}</span>
                                    <span class="badge bg-secondary">${report.skipped}</span>
                                </div>
                            </div>
                        `;
                        
                        reportItem.addEventListener('click', (e) => {
                            e.preventDefault();
                            loadReportDetails(report.id);
                        });
                        
                        reportsList.appendChild(reportItem);
                    });
                    
                    // Auto-load the most recent report
                    if (reports.length > 0) {
                        loadReportDetails(reports[0].id);
                    }
                })
                .catch(error => {
                    console.error('Error loading reports:', error);
                    document.getElementById('reportsList').innerHTML = `
                        <div class="alert alert-danger">
                            Error loading reports: ${error.message}
                        </div>
                    `;
                });
        }

        // Load details for a specific report
        function loadReportDetails(reportId) {
            const detailsContainer = document.getElementById('reportDetails');
            
            detailsContainer.innerHTML = `
                <div class="card">
                    <div class="card-header bg-info text-white">
                        Report Details
                    </div>
                    <div class="card-body text-center">
                        <div class="spinner-border text-info" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="mt-2">Loading report details...</p>
                    </div>
                </div>
            `;
            
            fetch(`/api/reports/${reportId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Report not found');
                    }
                    return response.json();
                })
                .then(report => {
                    // Calculate summary statistics
                    const summary = report.summary || {};
                    const total = summary.total || 0;
                    const passed = summary.passed || 0;
                    const failed = summary.failed || 0;
                    const skipped = summary.skipped || 0;
                    const errors = summary.error || 0;
                    const passRate = total > 0 ? ((passed / total) * 100).toFixed(1) : 0;
                    
                    // Format date
                    const date = new Date(report.timestamp);
                    const formattedDate = `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
                    
                    // Start building HTML
                    let html = `
                        <div class="card mb-4">
                            <div class="card-header bg-info text-white">
                                Report Summary
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <p><strong>ID:</strong> ${report.id}</p>
                                        <p><strong>Date:</strong> ${formattedDate}</p>
                                        <p><strong>Duration:</strong> ${report.duration.toFixed(2)} seconds</p>
                                    </div>
                                    <div class="col-md-6">
                                        <div class="text-center">
                                            <h3>Pass Rate: ${passRate}%</h3>
                                            <div class="progress" style="height: 20px;">
                                                <div class="progress-bar bg-success" style="width: ${passed/total*100}%" role="progressbar" aria-valuenow="${passed}" aria-valuemin="0" aria-valuemax="${total}">
                                                    ${passed}
                                                </div>
                                                <div class="progress-bar bg-danger" style="width: ${failed/total*100}%" role="progressbar" aria-valuenow="${failed}" aria-valuemin="0" aria-valuemax="${total}">
                                                    ${failed}
                                                </div>
                                                <div class="progress-bar bg-secondary" style="width: ${skipped/total*100}%" role="progressbar" aria-valuenow="${skipped}" aria-valuemin="0" aria-valuemax="${total}">
                                                    ${skipped}
                                                </div>
                                            </div>
                                            <div class="mt-2">
                                                <span class="badge bg-success">Passed: ${passed}</span>
                                                <span class="badge bg-danger">Failed: ${failed}</span>
                                                <span class="badge bg-secondary">Skipped: ${skipped}</span>
                                                ${errors > 0 ? `<span class="badge bg-warning">Errors: ${errors}</span>` : ''}
                                            </div>
                                            <div class="chart-container mt-3">
                                                <canvas id="summaryChart"></canvas>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    // Add screenshots section if available
                    if (report.screenshots && report.screenshots.length > 0) {
                        html += `
                            <div class="card mb-4">
                                <div class="card-header bg-primary text-white">
                                    Screenshots
                                </div>
                                <div class="card-body">
                                    <div class="row">
                        `;
                        
                        report.screenshots.forEach(screenshot => {
                            html += `
                                <div class="col-md-6">
                                    <div class="screenshot-container">
                                        <img src="/screenshots/${screenshot}" alt="Screenshot" />
                                        <p class="text-center mt-2">${screenshot}</p>
                                    </div>
                                </div>
                            `;
                        });
                        
                        html += `
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                    
                    // Add test duration chart section
                    if (report.test_cases && report.test_cases.length > 0) {
                        html += `
                            <div class="card mb-4">
                                <div class="card-header bg-info text-white">
                                    Test Performance
                                </div>
                                <div class="card-body">
                                    <div class="chart-container">
                                        <canvas id="durationChart"></canvas>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                    
                    // Add test cases section
                    if (report.test_cases && report.test_cases.length > 0) {
                        html += `
                            <div class="card mb-4">
                                <div class="card-header bg-primary text-white">
                                    Test Cases
                                </div>
                                <div class="card-body">
                                    <div class="list-group">
                        `;
                        
                        report.test_cases.forEach((test, index) => {
                            const statusClass = 
                                test.status === 'passed' ? 'success' : 
                                test.status === 'failed' ? 'danger' : 
                                test.status === 'skipped' ? 'secondary' : 'warning';
                                
                            html += `
                                <div class="test-item" onclick="toggleTestDetails(${index})">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <h6 class="mb-1">${test.name}</h6>
                                        <span class="badge bg-${statusClass}">${test.status}</span>
                                    </div>
                                    <div class="d-flex justify-content-between">
                                        <small>${test.nodeid}</small>
                                        <small>Duration: ${test.duration.toFixed(3)}s</small>
                                    </div>
                                    
                                    <div id="test-details-${index}" class="test-details" style="display: none;">
                                        ${test.call && test.call.longrepr ? `
                                            <div class="mt-3">
                                                <h6>Error Details:</h6>
                                                <pre>${test.call.longrepr}</pre>
                                            </div>
                                        ` : ''}
                                        
                                        ${test.screenshots && test.screenshots.length > 0 ? `
                                            <div class="mt-3">
                                                <h6>Test Screenshots:</h6>
                                                <div class="row">
                                                    ${test.screenshots.map(screenshot => `
                                                        <div class="col-md-6">
                                                            <div class="screenshot-container">
                                                                <img src="/screenshots/${screenshot}" alt="Screenshot" />
                                                            </div>
                                                        </div>
                                                    `).join('')}
                                                </div>
                                            </div>
                                        ` : ''}
                                    </div>
                                </div>
                                <hr>
                            `;
                        });
                        
                        html += `
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                    
                    // Add logs section if available
                    if (report.logs && report.logs.trim()) {
                        html += `
                            <div class="card">
                                <div class="card-header bg-secondary text-white">
                                    Logs
                                </div>
                                <div class="card-body">
                                    <div class="log-container">
                                        <pre>${report.logs}</pre>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                    
                    detailsContainer.innerHTML = html;
                    
                    // Create summary chart
                    if (total > 0) {
                        const summaryCtx = document.getElementById('summaryChart').getContext('2d');
                        new Chart(summaryCtx, {
                            type: 'doughnut',
                            data: {
                                labels: ['Passed', 'Failed', 'Skipped'],
                                datasets: [{
                                    data: [passed, failed, skipped],
                                    backgroundColor: [
                                        'rgba(40, 167, 69, 0.8)',
                                        'rgba(220, 53, 69, 0.8)',
                                        'rgba(108, 117, 125, 0.8)'
                                    ],
                                    borderColor: 'transparent',
                                    hoverOffset: 4
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: {
                                        position: 'bottom',
                                        labels: {
                                            color: 'rgb(200, 200, 200)'
                                        }
                                    }
                                }
                            }
                        });
                    }
                    
                    // Create duration chart if we have enough test cases
                    if (report.test_cases && report.test_cases.length > 0) {
                        const durationCtx = document.getElementById('durationChart').getContext('2d');
                        
                        // Get data for duration chart (up to 10 tests)
                        const testCasesToChart = report.test_cases.slice(0, 10);
                        const testNames = testCasesToChart.map(test => test.name);
                        const testDurations = testCasesToChart.map(test => test.duration);
                        const testColors = testCasesToChart.map(test => {
                            if (test.status === 'passed') return 'rgba(40, 167, 69, 0.8)';
                            if (test.status === 'failed') return 'rgba(220, 53, 69, 0.8)';
                            return 'rgba(108, 117, 125, 0.8)';
                        });
                        
                        new Chart(durationCtx, {
                            type: 'bar',
                            data: {
                                labels: testNames,
                                datasets: [{
                                    label: 'Duration (seconds)',
                                    data: testDurations,
                                    backgroundColor: testColors,
                                    borderColor: 'transparent',
                                    borderWidth: 1
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                scales: {
                                    y: {
                                        beginAtZero: true,
                                        ticks: {
                                            color: 'rgb(200, 200, 200)'
                                        },
                                        grid: {
                                            color: 'rgba(200, 200, 200, 0.1)'
                                        }
                                    },
                                    x: {
                                        ticks: {
                                            color: 'rgb(200, 200, 200)'
                                        },
                                        grid: {
                                            color: 'rgba(200, 200, 200, 0.1)'
                                        }
                                    }
                                },
                                plugins: {
                                    legend: {
                                        labels: {
                                            color: 'rgb(200, 200, 200)'
                                        }
                                    }
                                }
                            }
                        });
                    }
                })
                .catch(error => {
                    console.error('Error loading report details:', error);
                    detailsContainer.innerHTML = `
                        <div class="card">
                            <div class="card-header bg-danger text-white">
                                Error
                            </div>
                            <div class="card-body">
                                <p class="text-center">Error loading report details: ${error.message}</p>
                            </div>
                        </div>
                    `;
                });
        }

        // Create historical trend chart from multiple test reports
        function createHistoricalTrendChart(reports) {
            if (reports.length < 2) {
                document.getElementById('noTrendData').style.display = 'block';
                return;
            }
            
            // Sort reports by timestamp (oldest first)
            reports = reports.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
            
            // Extract data for the chart
            const labels = reports.map(report => {
                const date = new Date(report.timestamp);
                return date.toLocaleDateString();
            });
            
            const passRates = reports.map(report => {
                if (report.total_tests === 0) return 0;
                return (report.passed / report.total_tests) * 100;
            });
            
            const passedCounts = reports.map(report => report.passed);
            const failedCounts = reports.map(report => report.failed);
            const skippedCounts = reports.map(report => report.skipped);
            
            // Create the chart
            const ctx = document.getElementById('trendChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Pass Rate (%)',
                            data: passRates,
                            borderColor: 'rgba(40, 167, 69, 0.8)',
                            backgroundColor: 'rgba(40, 167, 69, 0.2)',
                            borderWidth: 2,
                            yAxisID: 'y',
                            tension: 0.1
                        },
                        {
                            label: 'Passed',
                            data: passedCounts,
                            borderColor: 'rgba(40, 167, 69, 0.8)',
                            backgroundColor: 'transparent',
                            borderDashed: [5, 5],
                            borderWidth: 1,
                            yAxisID: 'y1',
                            tension: 0.1
                        },
                        {
                            label: 'Failed',
                            data: failedCounts,
                            borderColor: 'rgba(220, 53, 69, 0.8)',
                            backgroundColor: 'transparent',
                            borderDashed: [5, 5],
                            borderWidth: 1,
                            yAxisID: 'y1',
                            tension: 0.1
                        },
                        {
                            label: 'Skipped',
                            data: skippedCounts,
                            borderColor: 'rgba(108, 117, 125, 0.8)',
                            backgroundColor: 'transparent',
                            borderDashed: [5, 5],
                            borderWidth: 1,
                            yAxisID: 'y1',
                            tension: 0.1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    stacked: false,
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {
                                display: true,
                                text: 'Pass Rate (%)',
                                color: 'rgb(200, 200, 200)'
                            },
                            min: 0,
                            max: 100,
                            ticks: {
                                color: 'rgb(200, 200, 200)'
                            },
                            grid: {
                                color: 'rgba(200, 200, 200, 0.1)'
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: {
                                display: true,
                                text: 'Test Count',
                                color: 'rgb(200, 200, 200)'
                            },
                            min: 0,
                            ticks: {
                                color: 'rgb(200, 200, 200)'
                            },
                            grid: {
                                color: 'rgba(200, 200, 200, 0.1)'
                            }
                        },
                        x: {
                            ticks: {
                                color: 'rgb(200, 200, 200)'
                            },
                            grid: {
                                color: 'rgba(200, 200, 200, 0.1)'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            labels: {
                                color: 'rgb(200, 200, 200)'
                            }
                        }
                    }
                }
            });
            
            document.getElementById('noTrendData').style.display = 'none';
        }
        
        // Toggle test details visibility
        function toggleTestDetails(index) {
            const detailsElement = document.getElementById(`test-details-${index}`);
            if (detailsElement) {
                detailsElement.style.display = detailsElement.style.display === 'none' ? 'block' : 'none';
            }
        }

        // Run tests from the dashboard
        function runTests() {
            const testPaths = document.getElementById('testPaths').value;
            const markers = document.getElementById('markers').value;
            
            const runTestsBtn = document.getElementById('runTestsBtn');
            runTestsBtn.disabled = true;
            runTestsBtn.innerHTML = `
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                Running...
            `;
            
            const data = {
                test_paths: testPaths.split(',').map(p => p.trim()).filter(p => p),
                markers: markers.split(',').map(m => m.trim()).filter(m => m)
            };
            
            fetch('/api/run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                if (result.status === 'running') {
                    // Set a timeout to refresh the reports list after a delay
                    setTimeout(() => {
                        loadReports();
                        runTestsBtn.disabled = false;
                        runTestsBtn.textContent = 'Run Tests';
                    }, 3000);
                }
            })
            .catch(error => {
                console.error('Error running tests:', error);
                runTestsBtn.disabled = false;
                runTestsBtn.textContent = 'Run Tests';
                alert('Error running tests: ' + error.message);
            });
        }
    </script>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</body>
</html>
        """

    def start(self) -> None:
        """Start the dashboard server."""
        if self.open_browser:
            threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{self.port}")).start()
        
        if HAS_RICH and console:
            console.print(f"[green]Dashboard running at: [bold blue]http://localhost:{self.port}[/bold blue][/green]")
            console.print(f"[green]Loading reports from: [yellow]{self.data_dir}[/yellow][/green]")
            console.print("\nPress Ctrl+C to stop the dashboard")
        else:
            print(f"Dashboard running at: http://localhost:{self.port}")
            print(f"Loading reports from: {self.data_dir}")
            print("\nPress Ctrl+C to stop the dashboard")
        
        self._run_server()

    def _run_server(self) -> None:
        """Run the Flask server."""
        try:
            self.app.run(host="0.0.0.0", port=self.port, debug=False)
        except KeyboardInterrupt:
            if HAS_RICH and console:
                console.print("\n[yellow]Dashboard stopped[/yellow]")
            else:
                print("\nDashboard stopped")


def launch_dashboard(
    port: int = 5500,
    data_dir: Optional[str] = None,
    open_browser: bool = True,
) -> Dashboard:
    """
    Launch the dashboard in a separate thread.
    
    Args:
        port: Port to run the dashboard server on
        data_dir: Directory containing test reports
        open_browser: Whether to automatically open the browser
        
    Returns:
        Dashboard instance
    """
    dashboard = Dashboard(
        port=port,
        data_dir=data_dir,
        open_browser=open_browser
    )
    
    # Start the dashboard
    dashboard_thread = threading.Thread(target=dashboard.start)
    dashboard_thread.daemon = True
    dashboard_thread.start()
    
    return dashboard