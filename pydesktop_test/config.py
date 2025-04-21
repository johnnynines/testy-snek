"""
Configuration management for PyDesktop Test.

This module provides utilities for creating and managing test configuration.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union


class TestConfig:
    """
    Configuration manager for tests.
    
    This class handles loading, validating, and providing access to
    test configuration settings.
    """
    
    DEFAULT_CONFIG = {
        # Directory settings
        "test_dir": "tests",
        "report_dir": "test_reports",
        "coverage_dir": "coverage",
        
        # Test execution settings
        "timeout": 30,
        "parallel": False,
        "max_workers": None,
        
        # Reporting settings
        "generate_html": True,
        "generate_coverage": True,
        "verbose": True,
        
        # Application settings
        "app_start_timeout": 5.0,
        "app_class": None,
        "app_args": [],
        "environment": "test",
        
        # UI testing settings
        "screenshot_on_failure": True,
        "wait_timeout": 2.0,
        "ui_interaction_delay": 0.1
    }
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize a new test configuration.
        
        Args:
            config_dict: Optional dictionary with configuration values
        """
        self._config = self.DEFAULT_CONFIG.copy()
        
        if config_dict:
            self.update(config_dict)
    
    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        Update configuration with values from the given dictionary.
        
        Args:
            config_dict: Dictionary with configuration values to update
        """
        for key, value in config_dict.items():
            if value is not None:  # Only update if the value is not None
                self._config[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key is not found
            
        Returns:
            The configuration value, or the default if not found
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
    
    def as_dict(self) -> Dict[str, Any]:
        """
        Get the configuration as a dictionary.
        
        Returns:
            Dictionary containing all configuration values
        """
        return self._config.copy()
    
    def load_from_file(self, file_path: Union[str, Path]) -> None:
        """
        Load configuration from a file.
        
        Supports JSON and YAML file formats, determined by file extension.
        
        Args:
            file_path: Path to the configuration file
            
        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file format is not supported or parsing fails
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        # Determine file format from extension
        if file_path.suffix.lower() in (".json", ".jsn"):
            with open(file_path, "r") as f:
                config_data = json.load(f)
        elif file_path.suffix.lower() in (".yaml", ".yml"):
            try:
                import yaml
                with open(file_path, "r") as f:
                    config_data = yaml.safe_load(f)
            except ImportError:
                raise ValueError("YAML configuration requires PyYAML package")
        else:
            raise ValueError(f"Unsupported configuration file format: {file_path.suffix}")
        
        # Update configuration with loaded data
        self.update(config_data)
    
    def save_to_file(self, file_path: Union[str, Path], format: str = "json") -> None:
        """
        Save configuration to a file.
        
        Args:
            file_path: Path to save the configuration to
            format: File format ("json" or "yaml")
            
        Raises:
            ValueError: If the format is not supported
        """
        file_path = Path(file_path)
        
        # Create parent directory if it doesn't exist
        os.makedirs(file_path.parent, exist_ok=True)
        
        # Save in the specified format
        if format.lower() == "json":
            with open(file_path, "w") as f:
                json.dump(self._config, f, indent=2)
        elif format.lower() in ("yaml", "yml"):
            try:
                import yaml
                with open(file_path, "w") as f:
                    yaml.dump(self._config, f, default_flow_style=False)
            except ImportError:
                raise ValueError("YAML configuration requires PyYAML package")
        else:
            raise ValueError(f"Unsupported configuration format: {format}")


def find_config_file(start_dir: Union[str, Path] = None) -> Optional[Path]:
    """
    Find a configuration file in the given directory or its parents.
    
    Looks for files named "pydesktop_test.json", "pydesktop_test.yaml", etc.
    
    Args:
        start_dir: Directory to start searching from (defaults to current directory)
        
    Returns:
        Path to the configuration file, or None if not found
    """
    if start_dir is None:
        start_dir = Path.cwd()
    else:
        start_dir = Path(start_dir)
    
    # Configuration file names to look for
    config_names = [
        "pydesktop_test.json",
        "pydesktop_test.yaml",
        "pydesktop_test.yml",
        ".pydesktop_test.json",
        ".pydesktop_test.yaml",
        ".pydesktop_test.yml",
    ]
    
    # Look in the current directory and its parents
    current_dir = start_dir
    while current_dir != current_dir.parent:  # Stop at root
        for name in config_names:
            config_path = current_dir / name
            if config_path.exists():
                return config_path
        
        # Move up to the parent directory
        current_dir = current_dir.parent
    
    # No configuration file found
    return None


def load_config(config_path: Optional[Union[str, Path]] = None, search_parents: bool = True) -> TestConfig:
    """
    Load a configuration from a file or the default configuration.
    
    Args:
        config_path: Path to the configuration file (optional)
        search_parents: Whether to search parent directories for config files
        
    Returns:
        TestConfig object with loaded configuration
    """
    config = TestConfig()
    
    # Try to load from specified path
    if config_path:
        try:
            config.load_from_file(config_path)
            return config
        except FileNotFoundError:
            if not search_parents:
                return config
    
    # Try to find and load from default locations
    if search_parents:
        found_path = find_config_file()
        if found_path:
            try:
                config.load_from_file(found_path)
            except (ValueError, FileNotFoundError):
                pass
    
    return config
