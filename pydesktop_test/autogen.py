"""
Automatic test generation module for Desktop Test.

This module analyzes Python desktop applications and generates
test cases automatically based on code structure and UI elements.
"""

import os
import ast
import inspect
import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Set, Union

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(handler)


class ProjectAnalyzer:
    """Analyzes a Python project structure to identify testable components."""
    
    def __init__(self, project_path: str):
        """
        Initialize the analyzer with a project path.
        
        Args:
            project_path: Path to the Python project to analyze
        """
        self.project_path = Path(project_path).resolve()
        self.modules = {}  # Dict to store module info
        self.classes = {}  # Dict to store class info
        self.functions = {}  # Dict to store function info
        self.ui_elements = {}  # Dict to store UI element info
        self.imports = {}  # Dict to store import info
        
        # GUI framework detection
        self.gui_framework = None
        self.gui_patterns = {
            'tkinter': ['tkinter', 'tk', 'Tk', 'Frame', 'Label', 'Button', 'Entry'],
            'pyqt': ['PyQt', 'QApplication', 'QMainWindow', 'QWidget', 'QPushButton'],
            'wxpython': ['wx', 'wxPython', 'App', 'Frame', 'Panel', 'Button'],
            'kivy': ['kivy', 'App', 'Widget', 'Label', 'Button'],
            'pyside': ['PySide', 'QApplication', 'QMainWindow', 'QWidget']
        }
    
    def analyze(self) -> Dict[str, Any]:
        """
        Perform full analysis of the project.
        
        Returns:
            Dict containing analysis results
        """
        logger.info(f"Analyzing project at {self.project_path}")
        
        # Collect Python files
        py_files = self._collect_python_files()
        logger.info(f"Found {len(py_files)} Python files")
        
        # Analyze each file
        for file_path in py_files:
            self._analyze_file(file_path)
        
        # Detect main application class
        self._detect_app_class()
        
        # Return analysis results
        return {
            'project_path': str(self.project_path),
            'gui_framework': self.gui_framework,
            'modules': self.modules,
            'classes': self.classes,
            'functions': self.functions,
            'ui_elements': self.ui_elements
        }
    
    def _collect_python_files(self) -> List[Path]:
        """
        Collect all Python files in the project.
        
        Returns:
            List of paths to Python files
        """
        py_files = []
        
        # Handle the case when project_path is a single Python file
        if os.path.isfile(self.project_path) and str(self.project_path).endswith('.py'):
            py_files.append(Path(self.project_path))
            logger.info(f"Found single Python file: {self.project_path}")
            return py_files
        
        # Handle directory project
        for root, _, files in os.walk(self.project_path):
            # Skip test directories and virtual environments
            if ('test' in root.lower() or 
                'venv' in root.lower() or 
                '.env' in root.lower()):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    py_files.append(Path(root) / file)
        
        logger.info(f"Found {len(py_files)} Python files")
        return py_files
    
    def _analyze_file(self, file_path: Path) -> None:
        """
        Analyze a single Python file.
        
        Args:
            file_path: Path to the Python file
        """
        # Handle the case when analyzing a single file
        if os.path.isfile(self.project_path) and str(file_path) == self.project_path:
            # Use the filename without extension as the module name
            module_name = os.path.basename(file_path).replace('.py', '')
        else:
            # Calculate the relative path for files within a project directory
            try:
                rel_path = file_path.relative_to(self.project_path)
                module_name = str(rel_path).replace('/', '.').replace('\\', '.').replace('.py', '')
            except ValueError:
                # Fallback for when relative_to fails
                module_name = os.path.basename(file_path).replace('.py', '')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Store module info
            self.modules[module_name] = {
                'path': str(file_path),
                'classes': [],
                'functions': [],
                'imports': []
            }
            
            # Analyze imports, classes, and functions
            self._analyze_node(tree, module_name, file_path)
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {str(e)}")
    
    def _analyze_node(self, node, module_name: str, file_path: Path) -> None:
        """
        Recursively analyze AST nodes.
        
        Args:
            node: AST node
            module_name: Name of the module
            file_path: Path to the file
        """
        # Check imports
        for item in ast.iter_child_nodes(node):
            if isinstance(item, ast.Import):
                for name in item.names:
                    self.modules[module_name]['imports'].append(name.name)
                    self._check_gui_framework(name.name)
            
            elif isinstance(item, ast.ImportFrom):
                if item.module:
                    self.modules[module_name]['imports'].append(item.module)
                    self._check_gui_framework(item.module)
            
            # Check classes
            elif isinstance(item, ast.ClassDef):
                class_info = self._analyze_class(item, module_name, file_path)
                if class_info:
                    self.classes[f"{module_name}.{item.name}"] = class_info
                    self.modules[module_name]['classes'].append(item.name)
            
            # Check functions
            elif isinstance(item, ast.FunctionDef):
                function_info = self._analyze_function(item, module_name, file_path)
                if function_info:
                    self.functions[f"{module_name}.{item.name}"] = function_info
                    self.modules[module_name]['functions'].append(item.name)
    
    def _analyze_class(self, node, module_name: str, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a class definition.
        
        Args:
            node: Class AST node
            module_name: Name of the module
            file_path: Path to the file
            
        Returns:
            Dict containing class information
        """
        # Get class docstring
        docstring = ast.get_docstring(node)
        
        # Check if this is a GUI class
        is_gui_class = False
        base_classes = []
        
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_name = base.id
                base_classes.append(base_name)
                if any(pattern in base_name for framework, patterns in self.gui_patterns.items() for pattern in patterns):
                    is_gui_class = True
                    if not self.gui_framework:
                        for framework, patterns in self.gui_patterns.items():
                            if any(pattern in base_name for pattern in patterns):
                                self.gui_framework = framework
                                break
        
        # Get methods
        methods = []
        ui_elements = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(item.name)
                
                # Check for UI elements in __init__ method
                if item.name == '__init__':
                    ui_elements.extend(self._extract_ui_elements(item, node.name, module_name))
        
        return {
            'module': module_name,
            'name': node.name,
            'docstring': docstring,
            'methods': methods,
            'is_gui_class': is_gui_class,
            'base_classes': base_classes,
            'ui_elements': ui_elements,
            'file_path': str(file_path),
            'line_number': node.lineno
        }
    
    def _analyze_function(self, node, module_name: str, file_path: Path) -> Dict[str, Any]:
        """
        Analyze a function definition.
        
        Args:
            node: Function AST node
            module_name: Name of the module
            file_path: Path to the file
            
        Returns:
            Dict containing function information
        """
        # Get function docstring
        docstring = ast.get_docstring(node)
        
        # Get arguments
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        
        return {
            'module': module_name,
            'name': node.name,
            'docstring': docstring,
            'args': args,
            'file_path': str(file_path),
            'line_number': node.lineno
        }
    
    def _extract_ui_elements(self, init_method, class_name: str, module_name: str) -> List[Dict[str, Any]]:
        """
        Extract UI elements created in __init__ method.
        
        Args:
            init_method: AST node for __init__ method
            class_name: Name of the class
            module_name: Name of the module
            
        Returns:
            List of UI elements
        """
        ui_elements = []
        
        # Look for assignments
        for item in ast.walk(init_method):
            if isinstance(item, ast.Assign):
                # Check the target (left side of assignment)
                for target in item.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                        if target.value.id == 'self':
                            # Check the value (right side of assignment)
                            if isinstance(item.value, ast.Call):
                                func = item.value.func
                                if isinstance(func, ast.Name):
                                    # Direct instantiation like self.button = Button(...)
                                    element_type = func.id
                                    if self._is_ui_element_type(element_type):
                                        ui_element = {
                                            'name': target.attr,
                                            'type': element_type,
                                            'class': class_name,
                                            'module': module_name
                                        }
                                        ui_elements.append(ui_element)
                                        self.ui_elements[f"{module_name}.{class_name}.{target.attr}"] = ui_element
                                elif isinstance(func, ast.Attribute):
                                    # Instantiation like self.button = tk.Button(...)
                                    if isinstance(func.value, ast.Name):
                                        element_type = f"{func.value.id}.{func.attr}"
                                        if self._is_ui_element_type(func.attr):
                                            ui_element = {
                                                'name': target.attr,
                                                'type': element_type,
                                                'class': class_name,
                                                'module': module_name
                                            }
                                            ui_elements.append(ui_element)
                                            self.ui_elements[f"{module_name}.{class_name}.{target.attr}"] = ui_element
        
        return ui_elements
    
    def _is_ui_element_type(self, element_type: str) -> bool:
        """
        Check if a type is a UI element type.
        
        Args:
            element_type: Type name to check
            
        Returns:
            True if it's a UI element type, False otherwise
        """
        ui_element_patterns = {
            'tkinter': ['Button', 'Label', 'Entry', 'Text', 'Frame', 'Canvas', 'Listbox', 'Menubutton', 
                        'Menu', 'Radiobutton', 'Checkbutton', 'Scale', 'Scrollbar', 'Spinbox', 'Combobox'],
            'pyqt': ['QPushButton', 'QLabel', 'QLineEdit', 'QTextEdit', 'QFrame', 'QWidget', 'QListWidget', 
                    'QMenuBar', 'QMenu', 'QRadioButton', 'QCheckBox', 'QSlider', 'QScrollBar', 'QSpinBox', 'QComboBox'],
            'wxpython': ['Button', 'StaticText', 'TextCtrl', 'Panel', 'Frame', 'ListBox', 'MenuBar', 
                        'Menu', 'RadioButton', 'CheckBox', 'Slider', 'ScrollBar', 'SpinCtrl', 'ComboBox'],
            'kivy': ['Button', 'Label', 'TextInput', 'Widget', 'BoxLayout', 'GridLayout', 'ListView', 
                    'Spinner', 'CheckBox', 'Slider', 'ScrollView'],
            'pyside': ['QPushButton', 'QLabel', 'QLineEdit', 'QTextEdit', 'QFrame', 'QWidget', 'QListWidget', 
                        'QMenuBar', 'QMenu', 'QRadioButton', 'QCheckBox', 'QSlider', 'QScrollBar', 'QSpinBox', 'QComboBox']
        }
        
        # Check against all UI element patterns
        for framework, patterns in ui_element_patterns.items():
            if any(element_type == pattern or element_type.endswith('.' + pattern) for pattern in patterns):
                return True
        
        return False
    
    def _check_gui_framework(self, import_name: str) -> None:
        """
        Check if an import suggests a GUI framework.
        
        Args:
            import_name: Name of the import
        """
        for framework, patterns in self.gui_patterns.items():
            if any(pattern in import_name for pattern in patterns):
                self.gui_framework = framework
                break
    
    def _detect_app_class(self) -> None:
        """Detect the main application class based on heuristics."""
        # Look for classes with names like 'App', 'Application', 'MainWindow', etc.
        app_name_patterns = ['App', 'Application', 'MainWindow', 'Window', 'GUI', 'Interface']
        
        for class_path, class_info in self.classes.items():
            # Check if it's a GUI class
            if class_info.get('is_gui_class', False):
                # Check if the name contains common app name patterns
                if any(pattern in class_info['name'] for pattern in app_name_patterns):
                    class_info['is_app_class'] = True
                
                # Check if it has typical app methods
                app_methods = ['run', 'start', 'main', 'mainloop', 'exec', 'exec_', 'show']
                if any(method in class_info.get('methods', []) for method in app_methods):
                    class_info['is_app_class'] = True


class TestGenerator:
    """Generates test code for Python desktop applications."""
    
    def __init__(self, analysis_results: Dict[str, Any]):
        """
        Initialize the test generator with analysis results.
        
        Args:
            analysis_results: Results from ProjectAnalyzer
        """
        self.analysis = analysis_results
        self.project_path = Path(analysis_results['project_path'])
        self.gui_framework = analysis_results.get('gui_framework')
    
    def generate_tests(self, output_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Generate test files for the analyzed project.
        
        Args:
            output_dir: Directory to write test files to (optional)
            
        Returns:
            Dict mapping test file paths to content
        """
        # Determine output directory
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = self.project_path / 'tests'
        
        # Ensure output directory exists
        output_path.mkdir(exist_ok=True, parents=True)
        
        # Generate test files
        test_files = {}
        
        # Generate test fixtures file
        fixtures_content = self._generate_fixtures()
        fixtures_path = output_path / 'conftest.py'
        test_files[str(fixtures_path)] = fixtures_content
        
        # Generate test files for classes
        app_classes = {}
        for class_path, class_info in self.analysis['classes'].items():
            if class_info.get('is_app_class', False) or class_info.get('is_gui_class', False):
                app_classes[class_path] = class_info
        
        # Generate tests for app classes
        for class_path, class_info in app_classes.items():
            test_content = self._generate_class_tests(class_path, class_info)
            module_name = class_info['module']
            class_name = class_info['name']
            test_file_name = f"test_{self._snake_case(class_name)}.py"
            test_path = output_path / test_file_name
            test_files[str(test_path)] = test_content
        
        # Write files if output_dir is provided
        if output_dir:
            for path, content in test_files.items():
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            logger.info(f"Generated {len(test_files)} test files in {output_path}")
        
        return test_files
    
    def _generate_fixtures(self) -> str:
        """
        Generate test fixtures file.
        
        Returns:
            Content for conftest.py
        """
        fixtures = []
        imports = ["import pytest", "import os", "import sys"]
        
        # Add GUI framework-specific imports
        if self.gui_framework == 'tkinter':
            imports.append("import tkinter as tk")
        elif self.gui_framework == 'pyqt':
            imports.append("from PyQt5 import QtWidgets")
            imports.append("from PyQt5.QtTest import QTest")
        elif self.gui_framework == 'wxpython':
            imports.append("import wx")
        elif self.gui_framework == 'kivy':
            imports.append("from kivy.app import App")
        elif self.gui_framework == 'pyside':
            imports.append("from PySide2 import QtWidgets")
            imports.append("from PySide2.QtTest import QTest")
        
        # Add imports for app classes
        app_modules = set()
        app_classes = {}
        for class_path, class_info in self.analysis['classes'].items():
            if class_info.get('is_app_class', False) or class_info.get('is_gui_class', False):
                module_name = class_info['module']
                class_name = class_info['name']
                app_modules.add(module_name)
                app_classes[class_path] = class_info
        
        for module in app_modules:
            imports.append(f"from {module} import " + ", ".join(
                [self.analysis['classes'][f"{module}.{class_name}"]['name'] 
                 for class_name in self.analysis['modules'][module]['classes']
                 if f"{module}.{class_name}" in app_classes]))
        
        # Add path setup
        setup = [
            "",
            "# Add project root to Python path",
            "project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))",
            "if project_root not in sys.path:",
            "    sys.path.insert(0, project_root)",
            ""
        ]
        
        # Generate fixtures for app classes
        for class_path, class_info in app_classes.items():
            class_name = class_info['name']
            fixture_name = self._snake_case(class_name) + "_instance"
            
            fixture = [
                f"@pytest.fixture",
                f"def {fixture_name}():",
                f"    \"\"\"Fixture to provide a test instance of {class_name}.\"\"\"",
                f"    app = {class_name}()"
            ]
            
            # Add framework-specific setup
            if self.gui_framework == 'tkinter':
                fixture.extend([
                    "    # Configure for testing",
                    "    app.root.withdraw()  # Hide window during tests",
                    "    # Set up event processing",
                    "    def process_events():",
                    "        app.root.update()",
                    "    app.process_events = process_events"
                ])
            elif self.gui_framework in ('pyqt', 'pyside'):
                fixture.extend([
                    "    # Configure for testing",
                    "    app.setVisible(False)  # Hide window during tests"
                ])
            elif self.gui_framework == 'wxpython':
                fixture.extend([
                    "    # Configure for testing",
                    "    app.Hide()  # Hide window during tests"
                ])
            
            fixture.extend([
                "    yield app",
                "    # Clean up",
                "    try:",
                "        if hasattr(app, 'shutdown'):",
                "            app.shutdown()",
                "        elif hasattr(app, 'close'):",
                "            app.close()",
                "    except:",
                "        pass",
                ""
            ])
            
            fixtures.append("\n".join(fixture))
        
        # Generate fixture for main window
        if self.gui_framework == 'tkinter':
            fixtures.append("\n".join([
                "@pytest.fixture",
                "def main_window(app_instance):",
                "    \"\"\"Fixture to provide the main window of the application.\"\"\"",
                "    # Get the main window based on the app structure",
                "    if hasattr(app_instance, 'root'):",
                "        return app_instance.root",
                "    elif hasattr(app_instance, 'window'):",
                "        return app_instance.window",
                "    elif hasattr(app_instance, 'main_window'):",
                "        return app_instance.main_window",
                "    # If we can't find it, assume the app itself is the main window",
                "    return app_instance",
                ""
            ]))
        elif self.gui_framework in ('pyqt', 'pyside'):
            fixtures.append("\n".join([
                "@pytest.fixture",
                "def main_window(app_instance):",
                "    \"\"\"Fixture to provide the main window of the application.\"\"\"",
                "    # For PyQt/PySide, the app_instance is typically the main window",
                "    return app_instance",
                ""
            ]))
        
        # Combine all parts
        return "\n".join(imports + setup + fixtures)
    
    def _generate_class_tests(self, class_path: str, class_info: Dict[str, Any]) -> str:
        """
        Generate tests for a class.
        
        Args:
            class_path: Path to the class
            class_info: Class information
            
        Returns:
            Test file content
        """
        module_name = class_info['module']
        class_name = class_info['name']
        
        imports = [
            "import pytest",
            "import os",
            "import sys",
            f"from {module_name} import {class_name}"
        ]
        
        # Import GUI testing modules
        if self.gui_framework == 'tkinter':
            imports.append("import tkinter as tk")
        elif self.gui_framework == 'pyqt':
            imports.append("from PyQt5.QtTest import QTest")
            imports.append("from PyQt5.QtCore import Qt")
        elif self.gui_framework == 'pyside':
            imports.append("from PySide2.QtTest import QTest")
            imports.append("from PySide2.QtCore import Qt")
        
        # Import Desktop Test assertions
        imports.extend([
            "",
            "# Import custom assertions for GUI testing",
            "try:",
            "    from pydesktop_test.assertions import (",
            "        assert_window_exists,",
            "        assert_control_exists,",
            "        assert_control_value,",
            "        assert_control_enabled,",
            "        assert_dialog_shown",
            "    )",
            "except ImportError:",
            "    # Define placeholder functions if the module is not available",
            "    def assert_window_exists(*args, **kwargs): return args[0]",
            "    def assert_control_exists(*args, **kwargs): return None",
            "    def assert_control_value(*args, **kwargs): pass",
            "    def assert_control_enabled(*args, **kwargs): pass",
            "    def assert_dialog_shown(*args, **kwargs): return None",
            ""
        ])
        
        # Add fixture name
        fixture_name = self._snake_case(class_name) + "_instance"
        
        # Generate tests
        tests = []
        
        # Test class initialization
        tests.append("\n".join([
            f"def test_{self._snake_case(class_name)}_init({fixture_name}):",
            f"    \"\"\"Test that {class_name} initializes correctly.\"\"\"",
            f"    # Verify the instance was created",
            f"    assert {fixture_name} is not None",
            f"    assert isinstance({fixture_name}, {class_name})",
            ""
        ]))
        
        # Test window title (for GUI classes)
        if class_info.get('is_gui_class', False):
            title_test = self._generate_title_test(class_name, fixture_name)
            if title_test:
                tests.append(title_test)
        
        # Generate tests for UI elements
        ui_elements = []
        for element_path, element_info in self.analysis['ui_elements'].items():
            if element_info['class'] == class_name and element_info['module'] == module_name:
                ui_elements.append(element_info)
        
        # Test UI elements
        for element in ui_elements:
            element_name = element['name']
            element_type = element['type'].split('.')[-1]  # Get base type name
            
            test_name = f"test_{self._snake_case(class_name)}_{self._snake_case(element_name)}"
            
            # Generate test based on element type
            if element_type in ('Button', 'QPushButton'):
                tests.append(self._generate_button_test(class_name, fixture_name, element_name, element_type))
            elif element_type in ('Entry', 'QLineEdit', 'TextInput', 'TextCtrl'):
                tests.append(self._generate_text_input_test(class_name, fixture_name, element_name, element_type))
            elif element_type in ('Checkbutton', 'QCheckBox', 'CheckBox'):
                tests.append(self._generate_checkbox_test(class_name, fixture_name, element_name, element_type))
            elif element_type in ('Radiobutton', 'QRadioButton', 'RadioButton'):
                tests.append(self._generate_radio_test(class_name, fixture_name, element_name, element_type))
            elif element_type in ('Combobox', 'QComboBox', 'ComboBox', 'Spinner'):
                tests.append(self._generate_combo_test(class_name, fixture_name, element_name, element_type))
        
        # Generate tests for methods
        method_tests = self._generate_method_tests(class_name, fixture_name, class_info.get('methods', []))
        if method_tests:
            tests.extend(method_tests)
        
        # Combine all parts
        return "\n".join(imports + [""] + tests)
    
    def _generate_title_test(self, class_name: str, fixture_name: str) -> str:
        """
        Generate test for window title.
        
        Args:
            class_name: Name of the class
            fixture_name: Name of the fixture
            
        Returns:
            Title test code
        """
        if self.gui_framework == 'tkinter':
            return "\n".join([
                f"def test_{self._snake_case(class_name)}_title({fixture_name}, main_window):",
                f"    \"\"\"Test that the {class_name} window has a title.\"\"\"",
                f"    # Get the window title",
                f"    title = main_window.title()",
                f"    # Verify it's not empty",
                f"    assert title is not None",
                f"    assert len(title) > 0",
                ""
            ])
        elif self.gui_framework in ('pyqt', 'pyside'):
            return "\n".join([
                f"def test_{self._snake_case(class_name)}_title({fixture_name}):",
                f"    \"\"\"Test that the {class_name} window has a title.\"\"\"",
                f"    # Get the window title",
                f"    title = {fixture_name}.windowTitle()",
                f"    # Verify it's not empty",
                f"    assert title is not None",
                f"    assert len(title) > 0",
                ""
            ])
        elif self.gui_framework == 'wxpython':
            return "\n".join([
                f"def test_{self._snake_case(class_name)}_title({fixture_name}):",
                f"    \"\"\"Test that the {class_name} window has a title.\"\"\"",
                f"    # Get the window title",
                f"    title = {fixture_name}.GetTitle()",
                f"    # Verify it's not empty",
                f"    assert title is not None",
                f"    assert len(title) > 0",
                ""
            ])
        
        return ""
    
    def _generate_button_test(self, class_name: str, fixture_name: str, button_name: str, button_type: str) -> str:
        """
        Generate test for a button.
        
        Args:
            class_name: Name of the class
            fixture_name: Name of the fixture
            button_name: Name of the button
            button_type: Type of the button
            
        Returns:
            Button test code
        """
        test_name = f"test_{self._snake_case(class_name)}_{self._snake_case(button_name)}"
        
        if self.gui_framework == 'tkinter':
            return "\n".join([
                f"def {test_name}({fixture_name}):",
                f"    \"\"\"Test that the {button_name} button works correctly.\"\"\"",
                f"    # Get the button",
                f"    button = {fixture_name}.{button_name}",
                f"    # Verify it exists and is enabled",
                f"    assert button is not None",
                f"    assert str(button['state']) in ('normal', 'active')",
                f"    # Test clicking the button (this might raise an exception if button has no command)",
                f"    try:",
                f"        button.invoke()",
                f"        # Process events to ensure UI updates",
                f"        if hasattr({fixture_name}, 'process_events'):",
                f"            {fixture_name}.process_events()",
                f"    except:",
                f"        # This is expected if the button doesn't have a command attached",
                f"        pass",
                ""
            ])
        elif self.gui_framework in ('pyqt', 'pyside'):
            return "\n".join([
                f"def {test_name}({fixture_name}):",
                f"    \"\"\"Test that the {button_name} button works correctly.\"\"\"",
                f"    # Get the button",
                f"    button = {fixture_name}.{button_name}",
                f"    # Verify it exists and is enabled",
                f"    assert button is not None",
                f"    assert button.isEnabled()",
                f"    # Test clicking the button",
                f"    try:",
                f"        QTest.mouseClick(button, Qt.LeftButton)",
                f"    except:",
                f"        # This might fail if the button has no slot connected",
                f"        pass",
                ""
            ])
        
        return ""
    
    def _generate_text_input_test(self, class_name: str, fixture_name: str, input_name: str, input_type: str) -> str:
        """
        Generate test for a text input field.
        
        Args:
            class_name: Name of the class
            fixture_name: Name of the fixture
            input_name: Name of the input field
            input_type: Type of the input field
            
        Returns:
            Text input test code
        """
        test_name = f"test_{self._snake_case(class_name)}_{self._snake_case(input_name)}"
        test_text = "Test input text"
        
        if self.gui_framework == 'tkinter':
            if input_type == 'Entry':
                return "\n".join([
                    f"def {test_name}({fixture_name}):",
                    f"    \"\"\"Test that the {input_name} input field works correctly.\"\"\"",
                    f"    # Get the input field",
                    f"    entry = {fixture_name}.{input_name}",
                    f"    # Verify it exists and is enabled",
                    f"    assert entry is not None",
                    f"    assert str(entry['state']) in ('normal', 'active')",
                    f"    # Clear existing text",
                    f"    entry.delete(0, tk.END)",
                    f"    # Test entering text",
                    f"    entry.insert(0, \"{test_text}\")",
                    f"    # Verify the text was entered",
                    f"    assert entry.get() == \"{test_text}\"",
                    ""
                ])
            else:  # Text widget
                return "\n".join([
                    f"def {test_name}({fixture_name}):",
                    f"    \"\"\"Test that the {input_name} text widget works correctly.\"\"\"",
                    f"    # Get the text widget",
                    f"    text = {fixture_name}.{input_name}",
                    f"    # Verify it exists and is enabled",
                    f"    assert text is not None",
                    f"    assert str(text['state']) in ('normal', 'active')",
                    f"    # Clear existing text",
                    f"    text.delete(1.0, tk.END)",
                    f"    # Test entering text",
                    f"    text.insert(1.0, \"{test_text}\")",
                    f"    # Verify the text was entered",
                    f"    assert text.get(1.0, tk.END).strip() == \"{test_text}\"",
                    ""
                ])
        elif self.gui_framework in ('pyqt', 'pyside'):
            if input_type == 'QLineEdit':
                return "\n".join([
                    f"def {test_name}({fixture_name}):",
                    f"    \"\"\"Test that the {input_name} input field works correctly.\"\"\"",
                    f"    # Get the input field",
                    f"    line_edit = {fixture_name}.{input_name}",
                    f"    # Verify it exists and is enabled",
                    f"    assert line_edit is not None",
                    f"    assert line_edit.isEnabled()",
                    f"    # Clear existing text",
                    f"    line_edit.clear()",
                    f"    # Test entering text",
                    f"    line_edit.setText(\"{test_text}\")",
                    f"    # Verify the text was entered",
                    f"    assert line_edit.text() == \"{test_text}\"",
                    ""
                ])
            else:  # QTextEdit
                return "\n".join([
                    f"def {test_name}({fixture_name}):",
                    f"    \"\"\"Test that the {input_name} text area works correctly.\"\"\"",
                    f"    # Get the text area",
                    f"    text_edit = {fixture_name}.{input_name}",
                    f"    # Verify it exists and is enabled",
                    f"    assert text_edit is not None",
                    f"    assert text_edit.isEnabled()",
                    f"    # Clear existing text",
                    f"    text_edit.clear()",
                    f"    # Test entering text",
                    f"    text_edit.setText(\"{test_text}\")",
                    f"    # Verify the text was entered",
                    f"    assert text_edit.toPlainText() == \"{test_text}\"",
                    ""
                ])
        
        return ""
    
    def _generate_checkbox_test(self, class_name: str, fixture_name: str, checkbox_name: str, checkbox_type: str) -> str:
        """
        Generate test for a checkbox.
        
        Args:
            class_name: Name of the class
            fixture_name: Name of the fixture
            checkbox_name: Name of the checkbox
            checkbox_type: Type of the checkbox
            
        Returns:
            Checkbox test code
        """
        test_name = f"test_{self._snake_case(class_name)}_{self._snake_case(checkbox_name)}"
        
        if self.gui_framework == 'tkinter':
            return "\n".join([
                f"def {test_name}({fixture_name}):",
                f"    \"\"\"Test that the {checkbox_name} checkbox works correctly.\"\"\"",
                f"    # Get the checkbox",
                f"    checkbox = {fixture_name}.{checkbox_name}",
                f"    # Verify it exists and is enabled",
                f"    assert checkbox is not None",
                f"    assert str(checkbox['state']) in ('normal', 'active')",
                f"    # Get the initial state",
                f"    var = checkbox.cget('variable')",
                f"    initial_value = var.get() if var else 0",
                f"    # Toggle the checkbox",
                f"    checkbox.invoke()",
                f"    # Verify the state changed",
                f"    new_value = var.get() if var else 0",
                f"    assert new_value != initial_value",
                ""
            ])
        elif self.gui_framework in ('pyqt', 'pyside'):
            return "\n".join([
                f"def {test_name}({fixture_name}):",
                f"    \"\"\"Test that the {checkbox_name} checkbox works correctly.\"\"\"",
                f"    # Get the checkbox",
                f"    checkbox = {fixture_name}.{checkbox_name}",
                f"    # Verify it exists and is enabled",
                f"    assert checkbox is not None",
                f"    assert checkbox.isEnabled()",
                f"    # Get the initial state",
                f"    initial_state = checkbox.isChecked()",
                f"    # Toggle the checkbox",
                f"    checkbox.setChecked(not initial_state)",
                f"    # Verify the state changed",
                f"    assert checkbox.isChecked() != initial_state",
                ""
            ])
        
        return ""
    
    def _generate_radio_test(self, class_name: str, fixture_name: str, radio_name: str, radio_type: str) -> str:
        """
        Generate test for a radio button.
        
        Args:
            class_name: Name of the class
            fixture_name: Name of the fixture
            radio_name: Name of the radio button
            radio_type: Type of the radio button
            
        Returns:
            Radio button test code
        """
        test_name = f"test_{self._snake_case(class_name)}_{self._snake_case(radio_name)}"
        
        if self.gui_framework == 'tkinter':
            return "\n".join([
                f"def {test_name}({fixture_name}):",
                f"    \"\"\"Test that the {radio_name} radio button works correctly.\"\"\"",
                f"    # Get the radio button",
                f"    radio = {fixture_name}.{radio_name}",
                f"    # Verify it exists and is enabled",
                f"    assert radio is not None",
                f"    assert str(radio['state']) in ('normal', 'active')",
                f"    # Test selecting the radio button",
                f"    radio.invoke()",
                f"    # Get the value",
                f"    var = radio.cget('variable')",
                f"    value = var.get() if var else None",
                f"    # Verify the button's value is selected",
                f"    if var:",
                f"        assert value == radio.cget('value')",
                ""
            ])
        elif self.gui_framework in ('pyqt', 'pyside'):
            return "\n".join([
                f"def {test_name}({fixture_name}):",
                f"    \"\"\"Test that the {radio_name} radio button works correctly.\"\"\"",
                f"    # Get the radio button",
                f"    radio = {fixture_name}.{radio_name}",
                f"    # Verify it exists and is enabled",
                f"    assert radio is not None",
                f"    assert radio.isEnabled()",
                f"    # Test selecting the radio button",
                f"    radio.setChecked(True)",
                f"    # Verify it's selected",
                f"    assert radio.isChecked()",
                ""
            ])
        
        return ""
    
    def _generate_combo_test(self, class_name: str, fixture_name: str, combo_name: str, combo_type: str) -> str:
        """
        Generate test for a combobox.
        
        Args:
            class_name: Name of the class
            fixture_name: Name of the fixture
            combo_name: Name of the combobox
            combo_type: Type of the combobox
            
        Returns:
            Combobox test code
        """
        test_name = f"test_{self._snake_case(class_name)}_{self._snake_case(combo_name)}"
        
        if self.gui_framework == 'tkinter':
            return "\n".join([
                f"def {test_name}({fixture_name}):",
                f"    \"\"\"Test that the {combo_name} combobox works correctly.\"\"\"",
                f"    # Get the combobox",
                f"    combo = {fixture_name}.{combo_name}",
                f"    # Verify it exists and is enabled",
                f"    assert combo is not None",
                f"    assert str(combo['state']) in ('normal', 'readonly', 'active')",
                f"    # Check if there are any values in the combobox",
                f"    values = combo['values']",
                f"    if values and len(values) > 0:",
                f"        # Select the first value",
                f"        combo.current(0)",
                f"        # Verify selection",
                f"        assert combo.get() == values[0]",
                ""
            ])
        elif self.gui_framework in ('pyqt', 'pyside'):
            return "\n".join([
                f"def {test_name}({fixture_name}):",
                f"    \"\"\"Test that the {combo_name} combobox works correctly.\"\"\"",
                f"    # Get the combobox",
                f"    combo = {fixture_name}.{combo_name}",
                f"    # Verify it exists and is enabled",
                f"    assert combo is not None",
                f"    assert combo.isEnabled()",
                f"    # Check if there are any items in the combobox",
                f"    if combo.count() > 0:",
                f"        # Select the first item",
                f"        combo.setCurrentIndex(0)",
                f"        # Verify selection",
                f"        assert combo.currentIndex() == 0",
                ""
            ])
        
        return ""
    
    def _generate_method_tests(self, class_name: str, fixture_name: str, methods: List[str]) -> List[str]:
        """
        Generate tests for methods.
        
        Args:
            class_name: Name of the class
            fixture_name: Name of the fixture
            methods: List of method names
            
        Returns:
            List of method test code
        """
        method_tests = []
        
        # Skip common methods and private methods
        skip_methods = [
            '__init__', '__del__', '__enter__', '__exit__', 
            '__repr__', '__str__', '__len__', '__iter__',
            '__getitem__', '__setitem__', '__delitem__'
        ]
        
        testable_methods = [m for m in methods if not m.startswith('_') and m not in skip_methods]
        
        # Create basic tests for testable methods
        for method in sorted(testable_methods)[:5]:  # Limit to 5 methods to avoid creating too many tests
            snake_method = self._snake_case(method)
            test_name = f"test_{self._snake_case(class_name)}_{snake_method}"
            
            # Create a basic test that just calls the method without arguments
            method_test = [
                f"def {test_name}({fixture_name}):",
                f"    \"\"\"Test that the {method} method exists.\"\"\"",
                f"    # Verify the method exists",
                f"    assert hasattr({fixture_name}, '{method}')",
                f"    assert callable(getattr({fixture_name}, '{method}'))",
                f"    # This is a placeholder test - to actually test the method,",
                f"    # you'd need to call it with appropriate arguments and verify the results",
                f"    # Example:",
                f"    # result = {fixture_name}.{method}()",
                f"    # assert result is not None",
                ""
            ]
            
            method_tests.append("\n".join(method_test))
        
        return method_tests
    
    def _snake_case(self, text: str) -> str:
        """
        Convert text to snake_case.
        
        Args:
            text: Text to convert
            
        Returns:
            Text in snake_case
        """
        import re
        # Insert underscore before uppercase letters
        s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', text)
        # Insert underscore between lowercase and uppercase letters
        s2 = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1)
        # Replace non-alphanumeric characters with underscore
        s3 = re.sub(r'[^a-zA-Z0-9]', '_', s2)
        # Convert to lowercase
        return s3.lower()


def analyze_project(project_path: str) -> Dict[str, Any]:
    """
    Analyze a Python project and detect its structure.
    
    Args:
        project_path: Path to the Python project to analyze
        
    Returns:
        Dict containing analysis results
    """
    analyzer = ProjectAnalyzer(project_path)
    return analyzer.analyze()


def generate_tests(analysis_results: Dict[str, Any], output_dir: Optional[str] = None) -> Dict[str, str]:
    """
    Generate tests for a Python project.
    
    Args:
        analysis_results: Results from ProjectAnalyzer
        output_dir: Directory to write test files to (optional)
        
    Returns:
        Dict mapping test file paths to content
    """
    generator = TestGenerator(analysis_results)
    return generator.generate_tests(output_dir)


def auto_generate_tests(project_path: str, output_dir: Optional[str] = None) -> Dict[str, str]:
    """
    Automatically analyze a project and generate tests.
    
    Args:
        project_path: Path to the Python project to analyze
        output_dir: Directory to write test files to (optional)
        
    Returns:
        Dict mapping test file paths to content
    """
    logger.info(f"Analyzing project at {project_path}")
    analysis_results = analyze_project(project_path)
    
    logger.info(f"Generating tests for {len(analysis_results.get('classes', {}))} classes")
    return generate_tests(analysis_results, output_dir)