"""
Example tests for the sample note-taking application.

This module demonstrates how to use PyDesktop Test to test a Tkinter application.
"""

import os
import time
import pytest
import tkinter as tk
from pathlib import Path

# Import the sample application
from sample_app import SimpleNoteApp

# Set the application class for tests that don't specify it explicitly
APP_CLASS = SimpleNoteApp


@pytest.mark.app_class(SimpleNoteApp)
def test_app_starts_with_correct_title(app_instance, main_window):
    """Test that the application starts with the correct title."""
    assert main_window.title() == "Simple Note App"


@pytest.mark.app_class(SimpleNoteApp)
def test_new_file_clears_editor(app_instance):
    """Test that the new file command clears the editor."""
    # Get the editor widget
    editor = app_instance.editor
    
    # Add some text to the editor
    editor.insert("1.0", "Some test text")
    
    # Create a new file
    app_instance.new_file()
    
    # Check that the editor is empty
    assert editor.get("1.0", "end-1c") == ""
    
    # Check that the window title is updated
    assert app_instance.root.title() == "Simple Note App"


@pytest.mark.app_class(SimpleNoteApp)
def test_typing_marks_as_modified(app_instance):
    """Test that typing in the editor marks the file as modified."""
    # Create a new file to start with a clean state
    app_instance.new_file()
    
    # Check that the file is not marked as modified
    assert not app_instance.is_modified
    
    # Type in the editor
    app_instance.editor.insert("1.0", "Modified text")
    
    # Trigger the modified event manually (needed in test environment)
    app_instance.editor.edit_modified(True)
    app_instance._on_text_modified(None)
    
    # Check that the file is marked as modified
    assert app_instance.is_modified
    
    # Check that the window title shows the modified indicator
    assert app_instance.root.title() == "*Simple Note App"


@pytest.mark.app_class(SimpleNoteApp)
def test_font_size_change(app_instance):
    """Test changing the font size."""
    # Get initial font size
    initial_font = app_instance.editor["font"]
    
    # Change the font size
    app_instance.font_size.set("16")
    app_instance._on_font_size_change(None)
    
    # Get the new font
    new_font = app_instance.editor["font"]
    
    # Check that the font size changed
    assert "16" in new_font


@pytest.mark.app_class(SimpleNoteApp)
def test_save_and_open_file(app_instance, temp_data):
    """Test saving and opening a file."""
    # Create a temporary file path
    temp_dir = Path("./temp_test_files")
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / "test_note.txt"
    
    # Store the path in temp_data for cleanup
    temp_data["temp_file"] = str(temp_file)
    
    # Start with a new file
    app_instance.new_file()
    
    # Add some text
    test_content = "This is a test note.\nWith multiple lines."
    app_instance.editor.insert("1.0", test_content)
    
    # Manually set the current file (to avoid the save dialog)
    app_instance.current_file = str(temp_file)
    
    # Save the file
    app_instance._save_to_file(str(temp_file))
    
    # Check that the file exists
    assert temp_file.exists()
    
    # Create a new file to clear the editor
    app_instance.new_file()
    
    # Check that the editor is empty
    assert app_instance.editor.get("1.0", "end-1c") == ""
    
    # Manually open the file (to avoid the open dialog)
    with open(temp_file, "r") as f:
        content = f.read()
    app_instance.editor.insert("1.0", content)
    app_instance.current_file = str(temp_file)
    app_instance.is_modified = False
    app_instance._update_title()
    
    # Check that the content matches
    assert app_instance.editor.get("1.0", "end-1c") == test_content
    
    # Clean up
    if temp_file.exists():
        temp_file.unlink()
    
    # Try to remove the directory if it's empty
    try:
        temp_dir.rmdir()
    except OSError:
        pass


@pytest.mark.app_class(SimpleNoteApp)
def test_cut_copy_paste(app_instance):
    """Test cut, copy, and paste functionality."""
    # Create a new file
    app_instance.new_file()
    
    # Add some text
    app_instance.editor.insert("1.0", "This is sample text for testing copy and paste.")
    
    # Select some text (from index 8 to 14 - "sample")
    app_instance.editor.tag_add(tk.SEL, "1.8", "1.14")
    
    # Copy the selected text
    app_instance.copy()
    
    # Clear the editor
    app_instance.editor.delete("1.0", tk.END)
    
    # Paste the copied text
    app_instance.paste()
    
    # Check that the pasted text matches what we copied
    assert app_instance.editor.get("1.0", "end-1c") == "sample"
    
    # Now test cut
    app_instance.editor.tag_add(tk.SEL, "1.0", "1.6")  # Select all text
    app_instance.cut()
    
    # Check that the editor is empty
    assert app_instance.editor.get("1.0", "end-1c") == ""
    
    # Paste again
    app_instance.paste()
    
    # Check that the pasted text matches what we cut
    assert app_instance.editor.get("1.0", "end-1c") == "sample"


@pytest.mark.app_class(SimpleNoteApp)
def test_show_about_dialog(app_instance, mock_dialog, monkeypatch):
    """Test that the about dialog is shown with the correct information."""
    # Mock the messagebox.showinfo method
    called_with = {}
    
    def mock_showinfo(title, message):
        called_with["title"] = title
        called_with["message"] = message
    
    # Apply the mock
    monkeypatch.setattr("tkinter.messagebox.showinfo", mock_showinfo)
    
    # Show the about dialog
    app_instance.show_about()
    
    # Check that showinfo was called with the correct title
    assert called_with["title"] == "About Simple Note App"
    
    # Check that the message contains expected information
    assert "Simple Note App" in called_with["message"]
    assert "Version" in called_with["message"]


@pytest.mark.app_class(SimpleNoteApp)
def test_status_updates(app_instance):
    """Test that status messages are updated correctly."""
    # Check initial status
    assert app_instance.status_message.get() == "Ready"
    
    # Update status
    test_message = "Test status message"
    app_instance.update_status(test_message)
    
    # Check that status was updated
    assert app_instance.status_message.get() == test_message


# Add a fixture for cleanup
@pytest.fixture(autouse=True)
def cleanup(temp_data):
    """Clean up temporary files after tests."""
    yield
    
    # Clean up any temporary files
    if "temp_file" in temp_data and os.path.exists(temp_data["temp_file"]):
        os.unlink(temp_data["temp_file"])
