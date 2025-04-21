"""
Interactive dashboard for test case visualization.

This module provides a web-based dashboard for visualizing and interacting
with test results from PyDesktop Test.
"""

import json
import os
import socket
import webbrowser
from datetime import datetime
from pathlib import Path
from threading import Thread
from typing import Dict, List, Any, Optional, Union

from flask import Flask, render_template_string, jsonify, request, send_from_directory
import pytest

from pydesktop_test.reporting import TestReport


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
        self.port = self._find_available_port(port)
        self.data_dir = data_dir or os.path.join(os.getcwd(), "test_reports")
        self.open_browser = open_browser
        self.app = Flask(__name__)
        self._configure_routes()
        self.server_thread = None
        
    def _find_available_port(self, start_port: int) -> int:
        """
        Find an available port starting from the given port.
        
        Args:
            start_port: Starting port number
            
        Returns:
            Available port number
        """
        port = start_port
        while port < start_port + 100:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) != 0:
                    return port
            port += 1
        return start_port  # Default to original if none found

    def _configure_routes(self) -> None:
        """Configure the Flask routes for the dashboard."""
        
        @self.app.route('/')
        def index():
            """Render the main dashboard page."""
            return render_template_string(self._get_dashboard_template())
        
        @self.app.route('/api/test-reports')
        def test_reports():
            """Get all test reports."""
            reports = self._load_test_reports()
            return jsonify(reports)
        
        @self.app.route('/api/test-report/<report_id>')
        def test_report(report_id):
            """Get a specific test report by ID."""
            report_path = Path(self.data_dir) / f"{report_id}.json"
            if not report_path.exists():
                return jsonify({"error": "Report not found"}), 404
                
            with open(report_path, "r") as f:
                report_data = json.load(f)
            
            return jsonify(report_data)
        
        @self.app.route('/api/screenshots/<path:filename>')
        def screenshots(filename):
            """Serve screenshot files."""
            screenshot_dir = Path(self.data_dir).parent / "test_screenshots"
            return send_from_directory(screenshot_dir, filename)
        
        @self.app.route('/api/run-tests', methods=['POST'])
        def run_tests():
            """Run tests from the dashboard."""
            data = request.json
            test_paths = data.get('test_paths', [])
            markers = data.get('markers', [])
            
            # Build pytest arguments
            args = []
            for path in test_paths:
                args.append(path)
            
            for marker in markers:
                args.append(f"-m {marker}")
            
            # Run tests in a separate thread
            def run():
                pytest.main(args)
            
            Thread(target=run).start()
            return jsonify({"status": "running"})

    def _load_test_reports(self) -> List[Dict[str, Any]]:
        """
        Load all test reports from the data directory.
        
        Returns:
            List of test report summaries
        """
        reports = []
        report_dir = Path(self.data_dir)
        
        if not report_dir.exists():
            return []
            
        for report_file in report_dir.glob("*.json"):
            try:
                with open(report_file, "r") as f:
                    report_data = json.load(f)
                
                # Extract summary information
                summary = {
                    "id": report_file.stem,
                    "timestamp": report_data.get("timestamp", ""),
                    "duration": report_data.get("duration", 0),
                    "total": report_data.get("summary", {}).get("total", 0),
                    "passed": report_data.get("summary", {}).get("passed", 0),
                    "failed": report_data.get("summary", {}).get("failed", 0),
                    "skipped": report_data.get("summary", {}).get("skipped", 0),
                    "error": report_data.get("summary", {}).get("error", 0),
                }
                
                reports.append(summary)
            except Exception as e:
                print(f"Error loading report {report_file}: {e}")
                
        # Sort by timestamp, newest first
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
        <html data-bs-theme="dark">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PyDesktop Test Dashboard</title>
            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            <style>
                .test-card {
                    transition: transform 0.2s ease;
                    cursor: pointer;
                }
                .test-card:hover {
                    transform: translateY(-5px);
                }
                .progress {
                    height: 10px;
                }
                .status-badge {
                    position: absolute;
                    top: 10px;
                    right: 10px;
                }
                .dashboard-header {
                    background: linear-gradient(135deg, #2a2a72 0%, #009ffd 100%);
                }
                .test-detail {
                    border-left: 4px solid;
                    padding-left: 15px;
                    margin-bottom: 15px;
                }
                .test-detail.pass {
                    border-color: var(--bs-success);
                }
                .test-detail.fail {
                    border-color: var(--bs-danger);
                }
                .test-detail.skip {
                    border-color: var(--bs-warning);
                }
                .test-detail.error {
                    border-color: var(--bs-info);
                }
                .screenshot-container {
                    margin-top: 15px;
                    text-align: center;
                }
                .screenshot-container img {
                    max-width: 100%;
                    border: 1px solid #666;
                    border-radius: 5px;
                }
            </style>
        </head>
        <body>
            <div class="container-fluid">
                <!-- Header -->
                <div class="row dashboard-header py-4 mb-4">
                    <div class="col-md-8">
                        <h1 class="text-white">PyDesktop Test Dashboard</h1>
                        <p class="text-white opacity-75">Interactive test case visualization and analysis</p>
                    </div>
                    <div class="col-md-4 text-end">
                        <button id="run-tests-btn" class="btn btn-light me-2">
                            <i class="bi bi-play-fill"></i> Run Tests
                        </button>
                        <button id="refresh-btn" class="btn btn-outline-light">
                            <i class="bi bi-arrow-clockwise"></i> Refresh
                        </button>
                    </div>
                </div>
                
                <!-- Main Content -->
                <div class="row">
                    <!-- Test Reports List -->
                    <div class="col-md-4">
                        <div class="card mb-4">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h5 class="mb-0">Test Reports</h5>
                                <span id="report-count" class="badge bg-primary">0</span>
                            </div>
                            <div class="card-body p-0">
                                <div id="reports-list" class="list-group list-group-flush">
                                    <!-- Reports will be loaded here -->
                                    <div class="text-center py-5">
                                        <div class="spinner-border text-primary" role="status">
                                            <span class="visually-hidden">Loading...</span>
                                        </div>
                                        <p class="mt-2">Loading reports...</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="card">
                            <div class="card-header">
                                <h5 class="mb-0">Test Statistics</h5>
                            </div>
                            <div class="card-body">
                                <canvas id="test-stats-chart"></canvas>
                                <div id="test-stats" class="mt-3">
                                    <!-- Stats will be loaded here -->
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Test Details -->
                    <div class="col-md-8">
                        <div id="report-details" class="card">
                            <div class="card-header">
                                <h5 class="mb-0">Test Report Details</h5>
                            </div>
                            <div class="card-body">
                                <div id="report-placeholder" class="text-center py-5">
                                    <p class="mb-0">Select a test report to view details</p>
                                </div>
                                <div id="report-content" class="d-none">
                                    <div class="mb-4">
                                        <h4 id="report-title">Report Title</h4>
                                        <div class="d-flex justify-content-between">
                                            <div>
                                                <span class="badge bg-secondary me-2" id="report-date">Date</span>
                                                <span class="badge bg-secondary" id="report-duration">Duration</span>
                                            </div>
                                            <div>
                                                <span class="badge bg-success me-1" id="report-passed">Passed: 0</span>
                                                <span class="badge bg-danger me-1" id="report-failed">Failed: 0</span>
                                                <span class="badge bg-warning me-1" id="report-skipped">Skipped: 0</span>
                                                <span class="badge bg-info" id="report-error">Error: 0</span>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="progress mb-4">
                                        <div id="progress-passed" class="progress-bar bg-success" role="progressbar" style="width: 0%"></div>
                                        <div id="progress-failed" class="progress-bar bg-danger" role="progressbar" style="width: 0%"></div>
                                        <div id="progress-skipped" class="progress-bar bg-warning" role="progressbar" style="width: 0%"></div>
                                        <div id="progress-error" class="progress-bar bg-info" role="progressbar" style="width: 0%"></div>
                                    </div>
                                    
                                    <ul class="nav nav-tabs mb-3" id="resultTabs" role="tablist">
                                        <li class="nav-item" role="presentation">
                                            <button class="nav-link active" id="tests-tab" data-bs-toggle="tab" data-bs-target="#tests" 
                                                type="button" role="tab" aria-selected="true">Test Cases</button>
                                        </li>
                                        <li class="nav-item" role="presentation">
                                            <button class="nav-link" id="screenshots-tab" data-bs-toggle="tab" data-bs-target="#screenshots" 
                                                type="button" role="tab" aria-selected="false">Screenshots</button>
                                        </li>
                                        <li class="nav-item" role="presentation">
                                            <button class="nav-link" id="logs-tab" data-bs-toggle="tab" data-bs-target="#logs" 
                                                type="button" role="tab" aria-selected="false">Logs</button>
                                        </li>
                                    </ul>
                                    
                                    <div class="tab-content" id="resultTabContent">
                                        <div class="tab-pane fade show active" id="tests" role="tabpanel" tabindex="0">
                                            <div id="test-cases" class="accordion">
                                                <!-- Test cases will be loaded here -->
                                            </div>
                                        </div>
                                        <div class="tab-pane fade" id="screenshots" role="tabpanel" tabindex="0">
                                            <div id="screenshots-content" class="row">
                                                <!-- Screenshots will be loaded here -->
                                            </div>
                                        </div>
                                        <div class="tab-pane fade" id="logs" role="tabpanel" tabindex="0">
                                            <pre id="logs-content" class="p-3 bg-dark text-light rounded">
                                                <!-- Logs will be loaded here -->
                                            </pre>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Run Tests Modal -->
            <div class="modal fade" id="run-tests-modal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Run Tests</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label for="test-paths" class="form-label">Test Path(s)</label>
                                <input type="text" class="form-control" id="test-paths" placeholder="e.g. tests/ test_app.py">
                                <div class="form-text">Multiple paths can be separated by space</div>
                            </div>
                            <div class="mb-3">
                                <label for="test-markers" class="form-label">Test Markers</label>
                                <input type="text" class="form-control" id="test-markers" placeholder="e.g. slow gui">
                                <div class="form-text">Multiple markers can be separated by space</div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="start-tests-btn">Run Tests</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js"></script>
            <script>
                // Global variables
                let currentReport = null;
                let testStatsChart = null;
                
                // DOM elements
                const reportsList = document.getElementById('reports-list');
                const reportCount = document.getElementById('report-count');
                const reportPlaceholder = document.getElementById('report-placeholder');
                const reportContent = document.getElementById('report-content');
                const reportTitle = document.getElementById('report-title');
                const reportDate = document.getElementById('report-date');
                const reportDuration = document.getElementById('report-duration');
                const reportPassed = document.getElementById('report-passed');
                const reportFailed = document.getElementById('report-failed');
                const reportSkipped = document.getElementById('report-skipped');
                const reportError = document.getElementById('report-error');
                const progressPassed = document.getElementById('progress-passed');
                const progressFailed = document.getElementById('progress-failed');
                const progressSkipped = document.getElementById('progress-skipped');
                const progressError = document.getElementById('progress-error');
                const testCases = document.getElementById('test-cases');
                const screenshotsContent = document.getElementById('screenshots-content');
                const logsContent = document.getElementById('logs-content');
                const refreshBtn = document.getElementById('refresh-btn');
                const runTestsBtn = document.getElementById('run-tests-btn');
                const runTestsModal = new bootstrap.Modal(document.getElementById('run-tests-modal'));
                const startTestsBtn = document.getElementById('start-tests-btn');
                
                // Fetch all test reports
                function fetchReports() {
                    fetch('/api/test-reports')
                        .then(response => response.json())
                        .then(data => {
                            displayReports(data);
                            updateStatistics(data);
                        })
                        .catch(error => {
                            console.error('Error fetching reports:', error);
                            reportsList.innerHTML = `
                                <div class="text-center py-5">
                                    <p class="text-danger mb-0">Error loading reports</p>
                                    <p class="small">Click refresh to try again</p>
                                </div>
                            `;
                        });
                }
                
                // Display test reports in the sidebar
                function displayReports(reports) {
                    if (reports.length === 0) {
                        reportsList.innerHTML = `
                            <div class="text-center py-5">
                                <p class="mb-0">No test reports found</p>
                            </div>
                        `;
                        reportCount.textContent = '0';
                        return;
                    }
                    
                    reportCount.textContent = reports.length;
                    
                    let html = '';
                    reports.forEach(report => {
                        const date = new Date(report.timestamp);
                        const formattedDate = date.toLocaleString();
                        const total = report.total || 0;
                        const passed = report.passed || 0;
                        const passPercent = total > 0 ? Math.round((passed / total) * 100) : 0;
                        
                        let statusClass = 'success';
                        if (report.failed > 0) {
                            statusClass = 'danger';
                        } else if (report.error > 0) {
                            statusClass = 'info';
                        } else if (report.skipped > 0 && report.passed === 0) {
                            statusClass = 'warning';
                        }
                        
                        html += `
                            <div class="list-group-item list-group-item-action test-card" data-report-id="${report.id}">
                                <span class="status-badge badge bg-${statusClass}">${passPercent}%</span>
                                <div class="d-flex w-100 justify-content-between">
                                    <h6 class="mb-1">Test Run ${report.id}</h6>
                                    <small>${formattedDate}</small>
                                </div>
                                <div class="progress mt-2 mb-1" style="height: 5px;">
                                    <div class="progress-bar bg-success" role="progressbar" style="width: ${report.passed / (total || 1) * 100}%"></div>
                                    <div class="progress-bar bg-danger" role="progressbar" style="width: ${report.failed / (total || 1) * 100}%"></div>
                                    <div class="progress-bar bg-warning" role="progressbar" style="width: ${report.skipped / (total || 1) * 100}%"></div>
                                    <div class="progress-bar bg-info" role="progressbar" style="width: ${report.error / (total || 1) * 100}%"></div>
                                </div>
                                <small>
                                    <span class="text-success">${report.passed} passed</span>
                                    <span class="text-danger">${report.failed} failed</span>
                                    <span class="text-warning">${report.skipped} skipped</span>
                                </small>
                            </div>
                        `;
                    });
                    
                    reportsList.innerHTML = html;
                    
                    // Add click event to report items
                    document.querySelectorAll('.test-card').forEach(card => {
                        card.addEventListener('click', () => {
                            const reportId = card.dataset.reportId;
                            fetchReportDetails(reportId);
                            
                            // Highlight selected card
                            document.querySelectorAll('.test-card').forEach(c => {
                                c.classList.remove('active');
                            });
                            card.classList.add('active');
                        });
                    });
                }
                
                // Update statistics chart
                function updateStatistics(reports) {
                    const testStats = document.getElementById('test-stats');
                    
                    // Calculate totals
                    let totalTests = 0;
                    let totalPassed = 0;
                    let totalFailed = 0;
                    let totalSkipped = 0;
                    let totalError = 0;
                    
                    reports.forEach(report => {
                        totalTests += report.total || 0;
                        totalPassed += report.passed || 0;
                        totalFailed += report.failed || 0;
                        totalSkipped += report.skipped || 0;
                        totalError += report.error || 0;
                    });
                    
                    // Update stats display
                    testStats.innerHTML = `
                        <div class="row text-center">
                            <div class="col">
                                <h3 class="text-success">${totalPassed}</h3>
                                <p class="small">Passed</p>
                            </div>
                            <div class="col">
                                <h3 class="text-danger">${totalFailed}</h3>
                                <p class="small">Failed</p>
                            </div>
                            <div class="col">
                                <h3 class="text-warning">${totalSkipped}</h3>
                                <p class="small">Skipped</p>
                            </div>
                            <div class="col">
                                <h3 class="text-info">${totalError}</h3>
                                <p class="small">Errors</p>
                            </div>
                        </div>
                    `;
                    
                    // Create/update chart
                    const ctx = document.getElementById('test-stats-chart').getContext('2d');
                    
                    if (testStatsChart) {
                        testStatsChart.data.datasets[0].data = [totalPassed, totalFailed, totalSkipped, totalError];
                        testStatsChart.update();
                    } else {
                        testStatsChart = new Chart(ctx, {
                            type: 'doughnut',
                            data: {
                                labels: ['Passed', 'Failed', 'Skipped', 'Error'],
                                datasets: [{
                                    data: [totalPassed, totalFailed, totalSkipped, totalError],
                                    backgroundColor: [
                                        '#198754', // success
                                        '#dc3545', // danger
                                        '#ffc107', // warning
                                        '#0dcaf0'  // info
                                    ],
                                    borderWidth: 1
                                }]
                            },
                            options: {
                                plugins: {
                                    legend: {
                                        position: 'bottom'
                                    }
                                },
                                maintainAspectRatio: false
                            }
                        });
                    }
                }
                
                // Fetch report details
                function fetchReportDetails(reportId) {
                    fetch(`/api/test-report/${reportId}`)
                        .then(response => response.json())
                        .then(data => {
                            currentReport = data;
                            displayReportDetails(data);
                        })
                        .catch(error => {
                            console.error('Error fetching report details:', error);
                            reportContent.classList.add('d-none');
                            reportPlaceholder.classList.remove('d-none');
                            reportPlaceholder.innerHTML = `
                                <p class="text-danger mb-0">Error loading report details</p>
                                <p class="small">Click refresh to try again</p>
                            `;
                        });
                }
                
                // Display report details
                function displayReportDetails(report) {
                    reportPlaceholder.classList.add('d-none');
                    reportContent.classList.remove('d-none');
                    
                    const summary = report.summary || {};
                    const total = summary.total || 0;
                    const passed = summary.passed || 0;
                    const failed = summary.failed || 0;
                    const skipped = summary.skipped || 0;
                    const error = summary.error || 0;
                    
                    // Update header info
                    reportTitle.textContent = `Test Run ${report.id || ''}`;
                    reportDate.textContent = new Date(report.timestamp).toLocaleString();
                    reportDuration.textContent = `${report.duration || 0}s`;
                    reportPassed.textContent = `Passed: ${passed}`;
                    reportFailed.textContent = `Failed: ${failed}`;
                    reportSkipped.textContent = `Skipped: ${skipped}`;
                    reportError.textContent = `Error: ${error}`;
                    
                    // Update progress bar
                    if (total > 0) {
                        progressPassed.style.width = `${passed / total * 100}%`;
                        progressFailed.style.width = `${failed / total * 100}%`;
                        progressSkipped.style.width = `${skipped / total * 100}%`;
                        progressError.style.width = `${error / total * 100}%`;
                    } else {
                        progressPassed.style.width = '0%';
                        progressFailed.style.width = '0%';
                        progressSkipped.style.width = '0%';
                        progressError.style.width = '0%';
                    }
                    
                    // Display test cases
                    const testCasesData = report.test_cases || [];
                    displayTestCases(testCasesData);
                    
                    // Display screenshots
                    const screenshots = report.screenshots || [];
                    displayScreenshots(screenshots);
                    
                    // Display logs
                    const logs = report.logs || '';
                    logsContent.textContent = logs;
                }
                
                // Display test cases
                function displayTestCases(testCases) {
                    const testCasesContainer = document.getElementById('test-cases');
                    
                    if (testCases.length === 0) {
                        testCasesContainer.innerHTML = `
                            <div class="text-center py-3">
                                <p class="mb-0">No test cases found</p>
                            </div>
                        `;
                        return;
                    }
                    
                    let html = '';
                    testCases.forEach((test, index) => {
                        const statusClass = test.status === 'passed' ? 'success' : 
                                           test.status === 'failed' ? 'danger' : 
                                           test.status === 'skipped' ? 'warning' : 'info';
                        
                        html += `
                            <div class="accordion-item">
                                <h2 class="accordion-header">
                                    <button class="accordion-button collapsed" type="button" 
                                        data-bs-toggle="collapse" data-bs-target="#test-${index}">
                                        <span class="badge bg-${statusClass} me-2">${test.status}</span>
                                        ${test.name}
                                    </button>
                                </h2>
                                <div id="test-${index}" class="accordion-collapse collapse">
                                    <div class="accordion-body">
                                        <div class="d-flex justify-content-between mb-2">
                                            <span class="badge bg-secondary">${test.duration || 0}s</span>
                                            <span>${test.nodeid || ''}</span>
                                        </div>
                                        
                                        ${test.call ? `
                                            <div class="test-detail ${test.status}">
                                                <h6>Test Details</h6>
                                                <pre class="bg-dark text-light p-2 rounded small">${test.call.longrepr || 'No details available'}</pre>
                                            </div>
                                        ` : ''}
                                        
                                        ${test.screenshots ? `
                                            <div class="mt-3">
                                                <h6>Screenshots</h6>
                                                <div class="row">
                                                    ${test.screenshots.map(screenshot => `
                                                        <div class="col-md-6 mb-3">
                                                            <div class="card">
                                                                <img src="/api/screenshots/${screenshot}" class="card-img-top">
                                                                <div class="card-body py-2">
                                                                    <p class="card-text small">${screenshot}</p>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    `).join('')}
                                                </div>
                                            </div>
                                        ` : ''}
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    
                    testCasesContainer.innerHTML = html;
                }
                
                // Display screenshots
                function displayScreenshots(screenshots) {
                    if (!screenshots || screenshots.length === 0) {
                        screenshotsContent.innerHTML = `
                            <div class="text-center py-3 col-12">
                                <p class="mb-0">No screenshots available</p>
                            </div>
                        `;
                        return;
                    }
                    
                    let html = '';
                    screenshots.forEach(screenshot => {
                        html += `
                            <div class="col-md-6 mb-4">
                                <div class="card">
                                    <img src="/api/screenshots/${screenshot}" class="card-img-top">
                                    <div class="card-body">
                                        <h6 class="card-title">${screenshot.split('/').pop()}</h6>
                                        <p class="card-text small text-muted">${screenshot}</p>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    
                    screenshotsContent.innerHTML = html;
                }
                
                // Event listeners
                refreshBtn.addEventListener('click', fetchReports);
                
                runTestsBtn.addEventListener('click', () => {
                    runTestsModal.show();
                });
                
                startTestsBtn.addEventListener('click', () => {
                    const paths = document.getElementById('test-paths').value.trim().split(' ').filter(p => p);
                    const markers = document.getElementById('test-markers').value.trim().split(' ').filter(m => m);
                    
                    fetch('/api/run-tests', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            test_paths: paths,
                            markers: markers
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        runTestsModal.hide();
                        
                        // Show toast notification
                        alert('Tests are running. Refresh in a few moments to see results.');
                        
                        // Clear form
                        document.getElementById('test-paths').value = '';
                        document.getElementById('test-markers').value = '';
                    })
                    .catch(error => {
                        console.error('Error running tests:', error);
                        alert('Error running tests. Check console for details.');
                    });
                });
                
                // Initialize
                fetchReports();
            </script>
        </body>
        </html>
        """

    def start(self) -> None:
        """Start the dashboard server."""
        if self.server_thread and self.server_thread.is_alive():
            return
            
        self.server_thread = Thread(target=self._run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        url = f"http://localhost:{self.port}"
        print(f"Dashboard running at {url}")
        
        if self.open_browser:
            webbrowser.open(url)
    
    def _run_server(self) -> None:
        """Run the Flask server."""
        self.app.run(host="0.0.0.0", port=self.port, debug=False, threaded=True)


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
    dashboard = Dashboard(port=port, data_dir=data_dir, open_browser=open_browser)
    dashboard.start()
    return dashboard


if __name__ == "__main__":
    # Quick test: launch dashboard with example data directory
    launch_dashboard()