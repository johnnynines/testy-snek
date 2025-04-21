"""
Custom assertions for desktop application testing.

This module provides specialized assertions that simplify validating
desktop application UI states and behaviors.
"""

import time
from typing import Any, List, Dict, Optional, Callable, Union


def assert_window_exists(app: Any, window_title: str, timeout: float = 2.0) -> None:
    """
    Assert that a window with the given title exists.
    
    Args:
        app: The application instance
        window_title: The title or identifier of the window to check
        timeout: Maximum time to wait for the window to appear (seconds)
        
    Raises:
        AssertionError: If the window does not exist within the timeout
    """
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        # Try different methods to find windows based on the application framework
        windows = []
        
        if hasattr(app, "windows"):
            windows = app.windows()
        elif hasattr(app, "get_windows"):
            windows = app.get_windows()
        elif hasattr(app, "find_window"):
            try:
                window = app.find_window(window_title)
                if window:
                    windows = [window]
            except Exception:
                pass
        
        # Check if the window title matches
        for window in windows:
            if hasattr(window, "title") and callable(window.title):
                if window.title() == window_title:
                    return
            elif hasattr(window, "title"):
                if window.title == window_title:
                    return
            elif hasattr(window, "get_title") and callable(window.get_title):
                if window.get_title() == window_title:
                    return
        
        # Sleep a bit before retrying
        time.sleep(0.1)
    
    # If we get here, the window was not found
    available_windows = []
    
    try:
        if hasattr(app, "windows"):
            available_windows = [w.title() if hasattr(w, "title") and callable(w.title) else str(w) for w in app.windows()]
        elif hasattr(app, "get_windows"):
            available_windows = [w.title() if hasattr(w, "title") and callable(w.title) else str(w) for w in app.get_windows()]
    except Exception:
        pass
    
    if available_windows:
        raise AssertionError(f"Window '{window_title}' not found. Available windows: {available_windows}")
    else:
        raise AssertionError(f"Window '{window_title}' not found.")


def assert_control_exists(
    window: Any, 
    control_id: Union[str, int], 
    control_type: Optional[str] = None,
    timeout: float = 2.0
) -> Any:
    """
    Assert that a control with the given ID exists in the window.
    
    Args:
        window: The window to search in
        control_id: The ID or name of the control
        control_type: Optional type of control to look for
        timeout: Maximum time to wait for the control to be found (seconds)
        
    Returns:
        The control that was found
        
    Raises:
        AssertionError: If the control does not exist within the timeout
    """
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        # Try different methods to find controls based on the UI framework
        control = None
        
        # Try by ID
        if hasattr(window, "findChild"):
            # Qt-based
            control = window.findChild(control_type, control_id) if control_type else window.findChild(control_id)
        elif hasattr(window, "find_element_by_id"):
            # Selenium/WebDriver style
            control = window.find_element_by_id(control_id)
        elif hasattr(window, "find_by_id"):
            control = window.find_by_id(control_id)
        elif hasattr(window, "find_control"):
            control = window.find_control(control_id, control_type)
        
        # Try by name if ID search failed
        if control is None and hasattr(window, "find_element_by_name"):
            control = window.find_element_by_name(control_id)
        elif control is None and hasattr(window, "find_by_name"):
            control = window.find_by_name(control_id)
        
        if control:
            return control
        
        # Sleep a bit before retrying
        time.sleep(0.1)
    
    # If we get here, the control was not found
    available_controls = []
    
    try:
        if hasattr(window, "children"):
            available_controls = [str(c) for c in window.children()]
        elif hasattr(window, "get_controls"):
            available_controls = [str(c) for c in window.get_controls()]
    except Exception:
        pass
    
    if available_controls:
        controls_str = ", ".join(available_controls[:10])
        if len(available_controls) > 10:
            controls_str += f" and {len(available_controls) - 10} more"
        raise AssertionError(f"Control '{control_id}' not found. Available controls: {controls_str}")
    else:
        type_text = f" of type {control_type}" if control_type else ""
        raise AssertionError(f"Control '{control_id}'{type_text} not found in window.")


def assert_control_value(
    control: Any, 
    expected_value: Any, 
    msg: Optional[str] = None
) -> None:
    """
    Assert that a control has the expected value.
    
    Args:
        control: The control to check
        expected_value: The expected value
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the control does not have the expected value
    """
    # Try different methods to get the control's value based on UI framework
    actual_value = None
    
    if hasattr(control, "text") and callable(control.text):
        actual_value = control.text()
    elif hasattr(control, "text"):
        actual_value = control.text
    elif hasattr(control, "value") and callable(control.value):
        actual_value = control.value()
    elif hasattr(control, "value"):
        actual_value = control.value
    elif hasattr(control, "get_text") and callable(control.get_text):
        actual_value = control.get_text()
    elif hasattr(control, "get_value") and callable(control.get_value):
        actual_value = control.get_value()
    elif hasattr(control, "currentText") and callable(control.currentText):
        # Qt ComboBox
        actual_value = control.currentText()
    elif hasattr(control, "isChecked") and callable(control.isChecked):
        # Qt checkbox
        actual_value = control.isChecked()
    
    if actual_value is None:
        raise AssertionError(f"Could not determine value of control: {control}")
    
    error_message = msg or f"Control has value '{actual_value}', expected '{expected_value}'"
    assert actual_value == expected_value, error_message


def assert_control_enabled(
    control: Any, 
    expected_enabled: bool = True, 
    msg: Optional[str] = None
) -> None:
    """
    Assert that a control is enabled or disabled.
    
    Args:
        control: The control to check
        expected_enabled: Whether the control should be enabled (True) or disabled (False)
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the control's enabled state doesn't match expectations
    """
    # Try different methods to check enabled state based on UI framework
    enabled = None
    
    if hasattr(control, "isEnabled") and callable(control.isEnabled):
        # Qt
        enabled = control.isEnabled()
    elif hasattr(control, "is_enabled") and callable(control.is_enabled):
        enabled = control.is_enabled()
    elif hasattr(control, "enabled") and callable(control.enabled):
        enabled = control.enabled()
    elif hasattr(control, "enabled"):
        enabled = control.enabled
    
    if enabled is None:
        raise AssertionError(f"Could not determine enabled state of control: {control}")
    
    state_text = "enabled" if expected_enabled else "disabled"
    opposite_state = "disabled" if expected_enabled else "enabled"
    
    error_message = msg or f"Control is {opposite_state}, expected {state_text}"
    assert enabled == expected_enabled, error_message


def assert_control_visible(
    control: Any, 
    expected_visible: bool = True, 
    msg: Optional[str] = None
) -> None:
    """
    Assert that a control is visible or hidden.
    
    Args:
        control: The control to check
        expected_visible: Whether the control should be visible (True) or hidden (False)
        msg: Optional custom error message
        
    Raises:
        AssertionError: If the control's visibility doesn't match expectations
    """
    # Try different methods to check visibility based on UI framework
    visible = None
    
    if hasattr(control, "isVisible") and callable(control.isVisible):
        # Qt
        visible = control.isVisible()
    elif hasattr(control, "is_visible") and callable(control.is_visible):
        visible = control.is_visible()
    elif hasattr(control, "visible") and callable(control.visible):
        visible = control.visible()
    elif hasattr(control, "visible"):
        visible = control.visible
    elif hasattr(control, "is_displayed") and callable(control.is_displayed):
        # Selenium-style
        visible = control.is_displayed()
    
    if visible is None:
        raise AssertionError(f"Could not determine visibility of control: {control}")
    
    state_text = "visible" if expected_visible else "hidden"
    opposite_state = "hidden" if expected_visible else "visible"
    
    error_message = msg or f"Control is {opposite_state}, expected {state_text}"
    assert visible == expected_visible, error_message


def assert_dialog_shown(
    app: Any, 
    dialog_title: str, 
    timeout: float = 2.0
) -> Any:
    """
    Assert that a dialog with the given title is shown.
    
    Args:
        app: The application instance
        dialog_title: The title of the dialog to check
        timeout: Maximum time to wait for the dialog (seconds)
        
    Returns:
        The dialog that was found
        
    Raises:
        AssertionError: If the dialog is not shown within the timeout
    """
    end_time = time.time() + timeout
    
    while time.time() < end_time:
        # Try different methods to find dialogs based on the application framework
        dialog = None
        
        # Try to find active modal dialogs
        if hasattr(app, "activeModalWidget") and callable(app.activeModalWidget):
            # Qt
            dialog = app.activeModalWidget()
            if dialog and hasattr(dialog, "windowTitle") and dialog.windowTitle() == dialog_title:
                return dialog
        
        # Try to find the dialog by title
        if hasattr(app, "find_window"):
            try:
                dialog = app.find_window(dialog_title)
                if dialog:
                    return dialog
            except Exception:
                pass
        
        # Check all top-level windows
        dialogs = []
        if hasattr(app, "topLevelWidgets") and callable(app.topLevelWidgets):
            # Qt
            dialogs = app.topLevelWidgets()
        elif hasattr(app, "windows"):
            dialogs = app.windows()
        elif hasattr(app, "get_windows"):
            dialogs = app.get_windows()
        
        for dlg in dialogs:
            title = None
            if hasattr(dlg, "windowTitle") and callable(dlg.windowTitle):
                title = dlg.windowTitle()
            elif hasattr(dlg, "title") and callable(dlg.title):
                title = dlg.title()
            elif hasattr(dlg, "title"):
                title = dlg.title
            
            if title == dialog_title:
                return dlg
        
        # Sleep a bit before retrying
        time.sleep(0.1)
    
    # If we get here, the dialog was not found
    raise AssertionError(f"Dialog with title '{dialog_title}' was not shown within {timeout} seconds")


def assert_ui_state(
    window: Any, 
    expected_state: Dict[str, Any],
    timeout: float = 2.0
) -> None:
    """
    Assert multiple UI controls have expected values/states.
    
    Args:
        window: The window containing the controls
        expected_state: Dictionary mapping control IDs to expected values
        timeout: Maximum time to wait for controls (seconds)
        
    Raises:
        AssertionError: If any control's state doesn't match expectations
    """
    for control_id, expected_value in expected_state.items():
        # Find the control
        control = assert_control_exists(window, control_id, timeout=timeout)
        
        # Check if expected_value is a dict with specific checks
        if isinstance(expected_value, dict):
            # Check value if specified
            if "value" in expected_value:
                assert_control_value(control, expected_value["value"])
            
            # Check enabled state if specified
            if "enabled" in expected_value:
                assert_control_enabled(control, expected_value["enabled"])
            
            # Check visibility if specified
            if "visible" in expected_value:
                assert_control_visible(control, expected_value["visible"])
        else:
            # Simple case: expected_value is the control's value
            assert_control_value(control, expected_value)
