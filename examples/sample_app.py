"""
Sample desktop application for demonstrating PyDesktop Test.

This is a simple Tkinter application with basic functionality
that can be used to demonstrate the testing framework.
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Optional, Dict, Any, List


class SimpleNoteApp:
    """
    A simple note-taking application built with Tkinter.
    
    This application demonstrates common desktop application patterns
    that can be tested with PyDesktop Test.
    """
    
    def __init__(self):
        """Initialize the application."""
        self.root = tk.Tk()
        self.root.title("Simple Note App")
        self.root.geometry("600x500")
        
        # Application state
        self.current_file: Optional[str] = None
        self.is_modified: bool = False
        self.is_test_mode: bool = False
        
        # Setup UI
        self._setup_menu()
        self._setup_toolbar()
        self._setup_editor()
        self._setup_status_bar()
        
        # Bind events
        self._bind_events()
        
        # Load default settings
        self.settings = self._load_settings()
        self._apply_settings()
    
    def _setup_menu(self):
        """Set up the application menu."""
        self.menu_bar = tk.Menu(self.root)
        
        # File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        self.file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        self.file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        self.file_menu.add_command(label="Save As", command=self.save_file_as, accelerator="Ctrl+Shift+S")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.confirm_exit, accelerator="Alt+F4")
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        
        # Edit menu
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        self.edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="Cut", command=self.cut, accelerator="Ctrl+X")
        self.edit_menu.add_command(label="Copy", command=self.copy, accelerator="Ctrl+C")
        self.edit_menu.add_command(label="Paste", command=self.paste, accelerator="Ctrl+V")
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)
        
        # Help menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)
        
        self.root.config(menu=self.menu_bar)
    
    def _setup_toolbar(self):
        """Set up the application toolbar."""
        self.toolbar_frame = ttk.Frame(self.root)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        
        # New file button
        self.new_button = ttk.Button(self.toolbar_frame, text="New", command=self.new_file)
        self.new_button.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Open file button
        self.open_button = ttk.Button(self.toolbar_frame, text="Open", command=self.open_file)
        self.open_button.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Save file button
        self.save_button = ttk.Button(self.toolbar_frame, text="Save", command=self.save_file)
        self.save_button.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Separator
        ttk.Separator(self.toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Font size selector
        ttk.Label(self.toolbar_frame, text="Font Size:").pack(side=tk.LEFT, padx=2)
        self.font_size = tk.StringVar(value="12")
        self.font_size_combo = ttk.Combobox(self.toolbar_frame, textvariable=self.font_size, 
                                            values=["8", "10", "12", "14", "16", "18", "20"], width=3)
        self.font_size_combo.pack(side=tk.LEFT, padx=2)
        self.font_size_combo.bind("<<ComboboxSelected>>", self._on_font_size_change)
    
    def _setup_editor(self):
        """Set up the text editor area."""
        # Create a frame for the editor with a scrollbar
        self.editor_frame = ttk.Frame(self.root)
        self.editor_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        
        # Add scrollbar
        self.scrollbar = ttk.Scrollbar(self.editor_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add text editor
        self.editor = tk.Text(self.editor_frame, wrap=tk.WORD, 
                            yscrollcommand=self.scrollbar.set, 
                            font=("TkDefaultFont", 12))
        self.editor.pack(expand=True, fill=tk.BOTH)
        self.scrollbar.config(command=self.editor.yview)
        
        # Set editor ID for testing
        self.editor.winfo_name = lambda: "text_editor"
    
    def _setup_status_bar(self):
        """Set up the status bar."""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status message
        self.status_message = tk.StringVar()
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_message)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Set default status
        self.update_status("Ready")
    
    def _bind_events(self):
        """Bind event handlers."""
        # Text modification events
        self.editor.bind("<<Modified>>", self._on_text_modified)
        
        # Keyboard shortcuts
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-Shift-s>", lambda e: self.save_file_as())
        
        # Window closing event
        self.root.protocol("WM_DELETE_WINDOW", self.confirm_exit)
    
    def _load_settings(self) -> Dict[str, Any]:
        """
        Load application settings from file.
        
        Returns:
            Dictionary containing application settings
        """
        default_settings = {
            "font_size": 12,
            "window_width": 600,
            "window_height": 500,
            "recent_files": []
        }
        
        settings_dir = Path.home() / ".simplenoteapp"
        settings_file = settings_dir / "settings.json"
        
        # Use test settings in test mode
        if self.is_test_mode:
            return default_settings
        
        # Try to load settings
        try:
            if settings_file.exists():
                with open(settings_file, "r") as f:
                    settings = json.load(f)
                return {**default_settings, **settings}
        except Exception:
            pass
        
        return default_settings
    
    def _save_settings(self):
        """Save application settings to file."""
        if self.is_test_mode:
            return
        
        settings_dir = Path.home() / ".simplenoteapp"
        settings_file = settings_dir / "settings.json"
        
        # Create settings directory if it doesn't exist
        settings_dir.mkdir(exist_ok=True)
        
        # Update settings from current state
        self.settings["font_size"] = int(self.font_size.get())
        self.settings["window_width"] = self.root.winfo_width()
        self.settings["window_height"] = self.root.winfo_height()
        
        # Add current file to recent files if it exists
        if self.current_file:
            recent_files = self.settings.get("recent_files", [])
            if self.current_file in recent_files:
                recent_files.remove(self.current_file)
            recent_files.insert(0, self.current_file)
            self.settings["recent_files"] = recent_files[:5]  # Keep only 5 most recent
        
        # Save settings
        try:
            with open(settings_file, "w") as f:
                json.dump(self.settings, f, indent=2)
        except Exception:
            pass
    
    def _apply_settings(self):
        """Apply loaded settings to the application."""
        # Set font size
        self.font_size.set(str(self.settings.get("font_size", 12)))
        self._on_font_size_change(None)
        
        # Set window size
        width = self.settings.get("window_width", 600)
        height = self.settings.get("window_height", 500)
        self.root.geometry(f"{width}x{height}")
    
    def _on_text_modified(self, event):
        """
        Handle text modification events.
        
        Args:
            event: The event object
        """
        if self.editor.edit_modified():
            if not self.is_modified:
                self.is_modified = True
                self._update_title()
            
            # Reset the modified flag
            self.editor.edit_modified(False)
    
    def _on_font_size_change(self, event):
        """
        Handle font size change events.
        
        Args:
            event: The event object
        """
        try:
            size = int(self.font_size.get())
            self.editor.config(font=("TkDefaultFont", size))
        except ValueError:
            pass
    
    def _update_title(self):
        """Update the window title based on current file and modified state."""
        title = "Simple Note App"
        
        if self.current_file:
            title = f"{os.path.basename(self.current_file)} - {title}"
        
        if self.is_modified:
            title = f"*{title}"
        
        self.root.title(title)
    
    def update_status(self, message: str):
        """
        Update the status bar message.
        
        Args:
            message: The message to display
        """
        self.status_message.set(message)
    
    def new_file(self):
        """Create a new file."""
        # Check if current file needs to be saved
        if self.is_modified and not self._confirm_discard_changes():
            return
        
        # Clear editor
        self.editor.delete(1.0, tk.END)
        
        # Reset file state
        self.current_file = None
        self.is_modified = False
        self._update_title()
        
        self.update_status("New file created")
    
    def open_file(self):
        """Open a file."""
        # Check if current file needs to be saved
        if self.is_modified and not self._confirm_discard_changes():
            return
        
        # Show file dialog
        file_path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                # Read file content
                with open(file_path, "r") as f:
                    content = f.read()
                
                # Update editor
                self.editor.delete(1.0, tk.END)
                self.editor.insert(tk.END, content)
                
                # Update file state
                self.current_file = file_path
                self.is_modified = False
                self._update_title()
                
                self.update_status(f"Opened {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {str(e)}")
    
    def save_file(self):
        """Save the current file."""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.save_file_as()
    
    def save_file_as(self):
        """Save the current file with a new name."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if file_path:
            self._save_to_file(file_path)
    
    def _save_to_file(self, file_path: str):
        """
        Save editor content to a file.
        
        Args:
            file_path: Path to save the file to
        """
        try:
            # Get editor content
            content = self.editor.get(1.0, tk.END)
            
            # Write to file
            with open(file_path, "w") as f:
                f.write(content)
            
            # Update file state
            self.current_file = file_path
            self.is_modified = False
            self._update_title()
            
            self.update_status(f"Saved {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {str(e)}")
    
    def _confirm_discard_changes(self) -> bool:
        """
        Confirm whether to discard changes to the current file.
        
        Returns:
            True if changes can be discarded, False otherwise
        """
        response = messagebox.askyesnocancel(
            "Unsaved Changes",
            "There are unsaved changes. Do you want to save before continuing?",
        )
        
        if response is None:  # Cancel
            return False
        elif response:  # Yes
            self.save_file()
            # Return True only if the file was actually saved
            return not self.is_modified
        else:  # No
            return True
    
    def confirm_exit(self):
        """Confirm exit and handle unsaved changes."""
        # Check if there are unsaved changes
        if self.is_modified and not self._confirm_discard_changes():
            return
        
        # Save settings
        self._save_settings()
        
        # Exit the application
        self.root.destroy()
    
    def undo(self):
        """Undo the last edit."""
        try:
            self.editor.edit_undo()
            self.update_status("Undo")
        except tk.TclError:
            self.update_status("Nothing to undo")
    
    def redo(self):
        """Redo the last undone edit."""
        try:
            self.editor.edit_redo()
            self.update_status("Redo")
        except tk.TclError:
            self.update_status("Nothing to redo")
    
    def cut(self):
        """Cut the selected text."""
        if self.editor.tag_ranges(tk.SEL):
            self.editor.event_generate("<<Cut>>")
            self.update_status("Cut")
    
    def copy(self):
        """Copy the selected text."""
        if self.editor.tag_ranges(tk.SEL):
            self.editor.event_generate("<<Copy>>")
            self.update_status("Copied")
    
    def paste(self):
        """Paste text from the clipboard."""
        self.editor.event_generate("<<Paste>>")
        self.update_status("Pasted")
    
    def show_about(self):
        """Show the about dialog."""
        messagebox.showinfo(
            "About Simple Note App",
            "Simple Note App\nA demonstration app for PyDesktop Test\n\nVersion 1.0.0"
        )
    
    def configure_for_testing(self):
        """Configure the application for testing."""
        self.is_test_mode = True
    
    def start(self):
        """Start the application."""
        self.root.mainloop()
    
    def shutdown(self):
        """Shutdown the application."""
        self.root.destroy()
    
    def main_window(self):
        """
        Get the main window.
        
        Returns:
            The main window
        """
        return self.root


if __name__ == "__main__":
    app = SimpleNoteApp()
    app.start()
