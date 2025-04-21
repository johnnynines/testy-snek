"""
Simple demo application to showcase the auto-test generation feature.

This is a basic Tkinter application with various UI elements
that can be detected and tested by the auto-test generator.
"""

import tkinter as tk
from tkinter import messagebox, ttk

class DemoApp:
    """A simple demo application with various UI elements."""
    
    def __init__(self):
        """Initialize the application."""
        self.root = tk.Tk()
        self.root.title("Demo Application")
        self.root.geometry("400x500")
        
        # Counter for button clicks
        self.counter = 0
        
        self._create_widgets()
        self._bind_events()
    
    def _create_widgets(self):
        """Create the UI widgets."""
        # Main frame
        self.main_frame = tk.Frame(self.root, padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title label
        self.title_label = tk.Label(
            self.main_frame, 
            text="Demo Application", 
            font=("Arial", 16, "bold")
        )
        self.title_label.pack(pady=(0, 20))
        
        # Counter section
        counter_frame = tk.Frame(self.main_frame)
        counter_frame.pack(fill=tk.X, pady=10)
        
        self.counter_label = tk.Label(
            counter_frame, 
            text="Counter: 0", 
            font=("Arial", 12)
        )
        self.counter_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.increment_button = tk.Button(
            counter_frame, 
            text="Increment", 
            command=self.increment_counter
        )
        self.increment_button.pack(side=tk.LEFT)
        
        self.reset_button = tk.Button(
            counter_frame, 
            text="Reset", 
            command=self.reset_counter
        )
        self.reset_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # Text input section
        input_frame = tk.Frame(self.main_frame)
        input_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(input_frame, text="Name:").pack(anchor=tk.W)
        self.name_entry = tk.Entry(input_frame)
        self.name_entry.pack(fill=tk.X)
        
        # Text area
        notes_frame = tk.Frame(self.main_frame)
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        tk.Label(notes_frame, text="Notes:").pack(anchor=tk.W)
        
        self.notes_text = tk.Text(notes_frame, height=5)
        self.notes_text.pack(fill=tk.BOTH, expand=True)
        
        # Options section
        options_frame = tk.Frame(self.main_frame)
        options_frame.pack(fill=tk.X, pady=10)
        
        # Checkboxes
        self.option1_var = tk.BooleanVar()
        self.option1_checkbox = tk.Checkbutton(
            options_frame, 
            text="Option 1", 
            variable=self.option1_var
        )
        self.option1_checkbox.pack(anchor=tk.W)
        
        self.option2_var = tk.BooleanVar()
        self.option2_checkbox = tk.Checkbutton(
            options_frame, 
            text="Option 2", 
            variable=self.option2_var
        )
        self.option2_checkbox.pack(anchor=tk.W)
        
        # Radio buttons
        radio_frame = tk.Frame(self.main_frame)
        radio_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(radio_frame, text="Select one:").pack(anchor=tk.W)
        
        self.radio_var = tk.StringVar(value="option1")
        self.radio1 = tk.Radiobutton(
            radio_frame, 
            text="Option A", 
            variable=self.radio_var, 
            value="option1"
        )
        self.radio1.pack(anchor=tk.W)
        
        self.radio2 = tk.Radiobutton(
            radio_frame, 
            text="Option B", 
            variable=self.radio_var, 
            value="option2"
        )
        self.radio2.pack(anchor=tk.W)
        
        self.radio3 = tk.Radiobutton(
            radio_frame, 
            text="Option C", 
            variable=self.radio_var, 
            value="option3"
        )
        self.radio3.pack(anchor=tk.W)
        
        # Dropdown (Combobox)
        combo_frame = tk.Frame(self.main_frame)
        combo_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(combo_frame, text="Select an item:").pack(anchor=tk.W)
        
        self.combo = ttk.Combobox(combo_frame, values=["Item 1", "Item 2", "Item 3"])
        self.combo.current(0)
        self.combo.pack(fill=tk.X)
        
        # Buttons
        button_frame = tk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.submit_button = tk.Button(
            button_frame, 
            text="Submit", 
            command=self.submit_form
        )
        self.submit_button.pack(side=tk.LEFT)
        
        self.clear_button = tk.Button(
            button_frame, 
            text="Clear Form", 
            command=self.clear_form
        )
        self.clear_button.pack(side=tk.LEFT, padx=(10, 0))
        
        self.about_button = tk.Button(
            button_frame, 
            text="About", 
            command=self.show_about
        )
        self.about_button.pack(side=tk.RIGHT)
    
    def _bind_events(self):
        """Bind events to widgets."""
        self.root.protocol("WM_DELETE_WINDOW", self.confirm_exit)
    
    def start(self):
        """Start the application."""
        self.root.mainloop()
    
    def shutdown(self):
        """Shutdown the application."""
        self.root.destroy()
    
    def increment_counter(self):
        """Increment the counter and update the label."""
        self.counter += 1
        self.counter_label.config(text=f"Counter: {self.counter}")
    
    def reset_counter(self):
        """Reset the counter to zero."""
        self.counter = 0
        self.counter_label.config(text=f"Counter: {self.counter}")
    
    def submit_form(self):
        """Process the form submission."""
        name = self.name_entry.get()
        notes = self.notes_text.get("1.0", tk.END).strip()
        option1 = self.option1_var.get()
        option2 = self.option2_var.get()
        radio_option = self.radio_var.get()
        combo_item = self.combo.get()
        
        message = f"Form submitted with:\n\n" \
                 f"Name: {name}\n" \
                 f"Notes: {notes}\n" \
                 f"Option 1: {'Checked' if option1 else 'Unchecked'}\n" \
                 f"Option 2: {'Checked' if option2 else 'Unchecked'}\n" \
                 f"Radio Option: {radio_option}\n" \
                 f"Combo Item: {combo_item}"
        
        messagebox.showinfo("Form Submitted", message)
    
    def clear_form(self):
        """Clear all form fields."""
        self.name_entry.delete(0, tk.END)
        self.notes_text.delete("1.0", tk.END)
        self.option1_var.set(False)
        self.option2_var.set(False)
        self.radio_var.set("option1")
        self.combo.current(0)
    
    def show_about(self):
        """Show the about dialog."""
        messagebox.showinfo(
            "About Demo App",
            "Demo Application v1.0\n\n"
            "Created to showcase the auto-test generation feature."
        )
    
    def confirm_exit(self):
        """Confirm before exiting the application."""
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.shutdown()


if __name__ == "__main__":
    app = DemoApp()
    app.start()