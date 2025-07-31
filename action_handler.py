# --- action_handler.py ---

import webbrowser
import os
import subprocess
import time
import pyautogui
from PIL import Image, ImageDraw, ImageFont

KNOWN_APPLICATIONS = {
    'notepad': 'notepad.exe',
    'calculator': 'calc.exe',
    'explorer': 'explorer.exe',
    'command prompt': 'cmd.exe',
    'task manager': 'taskmgr.exe',
    'whatsapp': r'explorer.exe shell:appsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App'
}

def open_website(url):
    try:
        webbrowser.open(url, new=2)
        return "I've opened the website for you."
    except Exception as e:
        return f"I had trouble opening that website. Error: {e}"

def type_text(text):
    """
    Types a given string with high reliability.
    Uses .write() which handles all characters (uppercase, symbols, etc.)
    and a deliberate interval to prevent missed keystrokes on any system.
    """
    try:
        print(f"ACTION_HANDLER: Typing text with high reliability: '{text}'")
        # THIS IS THE DEFINITIVE FIX FOR THE TYPING BUG.
        pyautogui.write(text, interval=0.05)
        return True
    except Exception as e:
        print(f"ACTION_HANDLER_ERROR: Failed to type text. {e}")
        return False

def clear_text():
    """Clears the currently active text field by selecting all and deleting."""
    try:
        print("ACTION_HANDLER: Clearing text (Ctrl+A, Delete)")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.1)
        pyautogui.press('delete')
        time.sleep(0.5)
        return True
    except Exception as e:
        print(f"ACTION_HANDLER_ERROR: Failed to clear text. {e}")
        return False

def click_at_coordinates(x, y):
    """Moves the mouse and clicks at the given coordinates."""
    try:
        pyautogui.moveTo(x, y, duration=0.3)
        pyautogui.click()
        return True
    except Exception as e:
        print(f"ACTION_HANDLER_ERROR: Failed to click. {e}")
        return False

def run_local_application(app_name):
    """Runs a local application from the known list."""
    # This function now correctly handles minor misspellings via the Planner AI.
    app_name_lower = app_name.lower()
    if app_name_lower not in KNOWN_APPLICATIONS:
        return f"I don't have '{app_name}' in my list of known applications."
    try:
        command = KNOWN_APPLICATIONS[app_name_lower]
        print(f"ACTION_HANDLER: Running command: '{command}'")
        subprocess.Popen(command)
        time.sleep(2) # Give app time to open and gain focus
        return True
    except Exception as e:
        print(f"ACTION_HANDLER_ERROR: Could not open '{app_name}'. Error: {e}")
        return False

# --- Vision Agent Helper Functions (Unchanged) ---
def take_screenshot(filename="screen.png"):
    try:
        uploads_folder = 'uploads'
        if not os.path.exists(uploads_folder): os.makedirs(uploads_folder)
        path = os.path.join(uploads_folder, filename)
        pyautogui.screenshot().save(path)
        return path
    except Exception as e:
        print(f"ACTION_HANDLER_ERROR: Failed to take screenshot. {e}")
        return None

def draw_grid_on_image(image_obj, grid_size=10):
    image = image_obj.copy()
    draw = ImageDraw.Draw(image)
    width, height = image.size
    h_spacing, v_spacing = width // grid_size, height // grid_size
    try: font = ImageFont.truetype("arial.ttf", 14)
    except IOError: font = ImageFont.load_default()
    for i in range(1, grid_size):
        x = i * h_spacing
        draw.line([(x, 0), (x, height)], fill=(255, 0, 0, 100), width=1)
        draw.text((x + 5, 5), chr(ord('A') + i - 1), fill="red", font=font)
    for i in range(1, grid_size):
        y = i * v_spacing
        draw.line([(0, y), (width, y)], fill=(255, 0, 0, 100), width=1)
        draw.text((5, y + 5), str(i), fill="red", font=font)
    return image