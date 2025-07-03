# --- action_handler.py (The Final, Privacy-Hardened Version) ---

import os
import subprocess
from pywinauto.application import Application
from pywinauto import Desktop
import time
import pyperclip
import pyautogui
import re

def open_url(url: str):
    """Opens a URL in the default web browser using the 'start' command."""
    try:
        if not url.lower().startswith('http'):
            url = 'https://www.' + url.split('www.')[-1]
        print(f"ACTION: Opening URL '{url}'...")
        subprocess.run(f'start "" "{url}"', shell=True, check=True)
        time.sleep(3)
        return f"Successfully opened URL {url}. Use LIST_OPEN_WINDOWS to find the browser title."
    except Exception as e:
        return f"Error opening URL '{url}': {e}"

def search_and_open_app(app_name: str):
    """Opens any application by searching for it in the Windows Start Menu."""
    try:
        print(f"ACTION: Searching for '{app_name}' in the Start Menu...")
        pyautogui.press('win')
        time.sleep(1)
        pyautogui.write(app_name, interval=0.05)
        time.sleep(1.5)
        pyautogui.press('enter')
        time.sleep(3)
        return f"Successfully launched '{app_name}' from the Start Menu. Use LIST_OPEN_WINDOWS to find its title."
    except Exception as e:
        return f"Error searching for and opening '{app_name}': {e}"

def list_open_windows() -> str:
    """Gets a list of all top-level window titles on the desktop."""
    try:
        windows = Desktop(backend="uia").windows()
        titles = [w.window_text() for w in windows if w.window_text() and w.is_visible()]
        return "\n".join(titles) if titles else "No open windows found."
    except Exception as e:
        return f"Error listing windows: {e}"

def _get_target_window(window_title: str):
    """Helper to connect to an app and get its main window."""
    if not window_title:
        raise ValueError("A window_title is required for this action.")
    app = Application(backend="uia").connect(title_re=f".*{re.escape(window_title)}.*", timeout=10)
    return app.top_window()

def get_window_elements(window_title: str) -> str:
    """
    Gets a list of all elements, intelligently redacting sensitive user content for privacy.
    """
    try:
        target_window = _get_target_window(window_title)
        target_window.set_focus()
        time.sleep(0.5)
        controls = target_window.descendants()
        element_info = []
        unique_elements = set()
        
        # --- REDACTION-BASED PRIVACY FILTER ---
        # Define control types that often contain sensitive user-generated content.
        SENSITIVE_TYPES = {'ListItem', 'Document', 'Text'}
        # Define safe titles that should always be shown (e.g., UI commands).
        SAFE_TITLES = {'Chats', 'Calls', 'Status', 'Settings', 'Profile', 'Archived chats', 'Starred messages'}

        for c in controls:
            text = c.window_text()
            control_type = c.element_info.control_type
            
            # If the element is visible and has a control type...
            if c.is_enabled() and c.is_visible() and control_type:
                # If the control type is sensitive AND its text is not a known safe UI command...
                if control_type in SENSITIVE_TYPES and text not in SAFE_TITLES:
                    # Redact the content entirely.
                    info_str = f"Type: '{control_type}', Title: '[User Content Redacted]'"
                else:
                    # Otherwise, the element is safe to show.
                    info_str = f"Type: '{control_type}', Title: '{text or ''}'"
                
                # Add to list if we haven't seen this exact element before.
                if info_str not in unique_elements:
                    element_info.append(info_str)
                    unique_elements.add(info_str)
                    
        return "\n".join(element_info) if element_info else "No interactable elements found."
    except Exception as e:
        return f"Error getting window elements for title '{window_title}': {e}"


def interact_with_element(window_title: str, action: str, element_title: str = None, control_type: str = None, value: str = "") -> str:
    """Interacts with a specific element using a hybrid approach."""
    try:
        target_window = _get_target_window(window_title)
        criteria = {}
        if element_title: criteria['title_re'] = f"(?i).*{re.escape(element_title)}.*"
        if control_type: criteria['control_type'] = control_type
        if not criteria: return "Error: Must provide 'element_title' and/or 'control_type'."
        control = target_window.child_window(found_index=0, **criteria)
        control.wait('visible', timeout=10)
        if action.lower() == 'click':
            is_browser = any(browser in window_title.lower() for browser in ["chrome", "firefox", "edge"])
            if is_browser:
                coords = control.rectangle().mid_point()
                pyautogui.click(coords.x, coords.y)
            else:
                control.click_input()
            return f"Successfully clicked the element matching {criteria}."
        elif action.lower() == 'type':
            control.set_focus()
            pyperclip.copy(value or "")
            control.type_keys('^a^v', pause=0.05)
            return f"Successfully pasted text into the element matching {criteria}."
        else:
            return f"Error: Unknown action '{action}'."
    except Exception as e:
        return f"Error interacting with element matching criteria {locals().get('criteria', {})} in window '{window_title}': {e}"

def press_key(window_title: str, key: str) -> str:
    """Brings a window to the front and sends a keystroke using pyautogui."""
    try:
        target_window = _get_target_window(window_title)
        target_window.set_focus()
        time.sleep(0.5)
        keys_to_press = key.lower().replace('^', 'ctrl+').replace('%', 'alt+').replace('+', ' ').split()
        pyautogui.hotkey(*keys_to_press)
        time.sleep(1)
        return f"Sent key(s) '{key}' to window '{window_title}'."
    except Exception as e:
        return f"Error pressing key on window '{window_title}': {e}"