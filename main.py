from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    """
    Main page for PyDesktop Test framework documentation.
    This provides a simple webpage for viewing the project information.
    """
    html = """
    <!DOCTYPE html>
    <html data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PyDesktop Test Framework</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container my-5">
            <div class="row">
                <div class="col-md-8 offset-md-2">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h1 class="card-title mb-0">PyDesktop Test</h1>
                        </div>
                        <div class="card-body">
                            <p class="lead">
                                A PyTest-based testing framework for Python desktop applications 
                                with enhanced reporting and developer experience.
                            </p>
                            
                            <h2>Features</h2>
                            <ul class="list-group list-group-flush mb-4">
                                <li class="list-group-item">Auto-Test Generation: Automatically generate tests for your Python desktop apps</li>
                                <li class="list-group-item">Easy Test Creation: Simplifies writing tests for desktop applications</li>
                                <li class="list-group-item">Custom Assertions: Built-in assertions for UI components and states</li>
                                <li class="list-group-item">Enhanced Reporting: Rich console output and HTML reports</li>
                                <li class="list-group-item">Configurable: Flexible configuration for different testing environments</li>
                                <li class="list-group-item">Test Discovery: Automatic test discovery across project directories</li>
                                <li class="list-group-item">Parallel Execution: Run tests in parallel for faster results</li>
                                <li class="list-group-item">Code Coverage: Integrated coverage reporting</li>
                                <li class="list-group-item">Framework Support: Compatible with multiple GUI frameworks (Tkinter, PyQt, etc.)</li>
                                <li class="list-group-item">Screenshot Testing: Capture screenshots for visual regression testing</li>
                            </ul>
                            
                            <h2>Getting Started</h2>
                            <p>Install the package via pip:</p>
                            <pre class="bg-dark text-light p-3 rounded">pip install pydesktop-test</pre>
                            
                            <h2>Usage Example: Writing Tests Manually</h2>
                            <pre class="bg-dark text-light p-3 rounded">
import pytest
from myapp import MyTkinterApp  # Your application class

# Mark the test with the application class
@pytest.mark.app_class(MyTkinterApp)
def test_app_window_title(app_instance, main_window):
    # Test that the application window has the correct title
    assert main_window.title() == "My Application"

@pytest.mark.app_class(MyTkinterApp)
def test_button_click(app_instance):
    # Test that clicking a button updates the counter
    # Get the button and counter label
    button = app_instance.button
    counter_label = app_instance.counter_label
    
    # Get initial counter value
    initial_value = int(counter_label["text"])
    
    # Click the button
    button.invoke()
    
    # Check that the counter was incremented
    assert int(counter_label["text"]) == initial_value + 1
                            </pre>
                            
                            <h2>Auto-Test Generation</h2>
                            <p>Generate tests automatically for your desktop application:</p>
                            <pre class="bg-dark text-light p-3 rounded">
# From the command line
./desktop-test autogen /path/to/your/project

# Generate tests for a single file
./desktop-test autogen /path/to/your/app.py

# Specify custom output directory
./desktop-test autogen /path/to/your/project --output /path/to/output

# Just analyze the project structure without generating tests
./desktop-test autogen /path/to/your/project --analyze-only
                            </pre>
                        </div>
                        <div class="card-footer text-muted">
                            <a href="https://github.com/example/pydesktop-test" 
                               class="btn btn-primary">GitHub Repository</a>
                            <a href="https://pydesktop-test.readthedocs.io/" 
                               class="btn btn-secondary">Documentation</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)