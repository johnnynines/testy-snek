"""
Basic tests for the test configuration module.

These tests demonstrate how to test non-GUI components of your application.
"""

import pytest
from pydesktop_test.config import TestConfig

def test_config_defaults():
    """Test that the default configuration has expected values."""
    config = TestConfig()
    assert config.get("test_dir") == "tests"
    assert config.get("report_dir") == "test_reports"
    assert config.get("verbose") == True

def test_config_update():
    """Test updating configuration values."""
    config = TestConfig()
    config.update({"verbose": False, "custom_value": 42})
    assert config.get("verbose") == False
    assert config.get("custom_value") == 42
    
def test_config_set_get():
    """Test setting and getting configuration values."""
    config = TestConfig()
    config.set("new_value", "test")
    assert config.get("new_value") == "test"
    # Test default values for nonexistent keys
    assert config.get("nonexistent") is None
    assert config.get("nonexistent", "default") == "default"