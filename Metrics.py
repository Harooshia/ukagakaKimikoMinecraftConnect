import psutil
import time
import threading
import pynput.mouse
import pynput.keyboard
import pygetwindow as gw
import win32process

# Global metrics
metrics = {
    "keystrokes": 0,
    "mouse_clicks": 0,
    "scroll_distance": 0,
    "mouse_distance": 0.0
}

# Track mouse
last_mouse_pos = None
def on_move(x, y):
    global last_mouse_pos
    if last_mouse_pos:
        dx = x - last_mouse_pos[0]
        dy = y - last_mouse_pos[1]
        metrics["mouse_distance"] += (dx**2 + dy**2) ** 0.5
    last_mouse_pos = (x, y)

def on_click(x, y, button, pressed):
    if pressed:
        metrics["mouse_clicks"] += 1

def on_scroll(x, y, dx, dy):
    metrics["scroll_distance"] += abs(dy)

# Track keyboard
def on_press(key):
    metrics["keystrokes"] += 1

# Start listeners
mouse_listener = pynput.mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
keyboard_listener = pynput.keyboard.Listener(on_press=on_press)
mouse_listener.start()
keyboard_listener.start()

# Friendly name mapping
FRIENDLY_NAMES = {
    "code": "Visual Studio Code",
    "opera": "Opera GX",
    "chrome": "Google Chrome",
    "msedge": "Microsoft Edge",
    "discord": "Discord",
    "explorer": "File Explorer"
}

# Exclude system/irrelevant processes
EXCLUDE = {"program manager", "applicationframehost", "nvcontainer", "nvidia overlay"}

def get_app_from_hwnd(hwnd):
    """Return process name from window handle"""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        return proc.name()
    except Exception:
        return None

def clean_name(exe_name):
    """Remove .exe and map to friendly names"""
    if not exe_name:
        return None
    name = exe_name.replace(".exe", "").lower()
    if name in EXCLUDE:
        return None
    return FRIENDLY_NAMES.get(name, name.capitalize())

def list_open_programs():
    programs = []
    for window in gw.getAllWindows():
        if window.visible and window.title.strip():  # your fix
            exe = get_app_from_hwnd(window._hWnd)
            pretty = clean_name(exe)
            if pretty and pretty.lower() != "settings":  # block Settings explicitly
                programs.append(pretty)
    # Remove duplicates and sort
    return sorted(set(programs), key=str.lower)

def monitor():
    while True:
        print("\n=== Metrics ===")
        print(f"Keystrokes: {metrics['keystrokes']}")
        print(f"Mouse Clicks: {metrics['mouse_clicks']}")
        print(f"Scroll Distance: {metrics['scroll_distance']}")
        print(f"Mouse Distance (pixels): {metrics['mouse_distance']:.2f}")

        print("\n=== Open Programs ===")
        for prog in list_open_programs():
            print(f"- {prog}")

        time.sleep(5)

if __name__ == "__main__":
    monitor_thread = threading.Thread(target=monitor)
    monitor_thread.start()
