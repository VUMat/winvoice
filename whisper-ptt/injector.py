"""Text injection via clipboard + keyboard shortcut or pyautogui.typewrite."""

import logging
import time

import pyautogui
import pyperclip

logger = logging.getLogger(__name__)

# Terminal process names that require clipboard paste instead of typewrite
TERMINAL_PROCESSES = {
    "windowsterminal.exe",
    "cmd.exe",
    "powershell.exe",
    "wt.exe",
    "alacritty.exe",
    "kitty.exe",
    "wezterm.exe",
    "conhost.exe",
}


def _get_focused_process_name():
    """Return the lowercase exe name of the focused window, or empty string."""
    try:
        import win32gui
        import win32process
        import psutil

        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        proc = psutil.Process(pid)
        return proc.name().lower()
    except Exception:
        return ""


def _is_terminal(process_name):
    return process_name in TERMINAL_PROCESSES


def inject_text(text):
    """Inject text into the currently focused window."""
    if not text:
        return

    # Save current clipboard
    try:
        old_clipboard = pyperclip.paste()
    except Exception:
        old_clipboard = ""

    process_name = _get_focused_process_name()
    logger.info("Focused process: %s", process_name or "(unknown)")

    if _is_terminal(process_name):
        _paste_via_clipboard(text)
    else:
        try:
            # For non-terminal apps, try typewrite first for better compatibility
            # typewrite only works with ASCII; fall back to clipboard for unicode
            if text.isascii():
                pyautogui.typewrite(text, interval=0.01)
            else:
                _paste_via_clipboard(text)
        except Exception:
            logger.warning("typewrite failed, falling back to clipboard paste")
            _paste_via_clipboard(text)

    # Restore clipboard after a short delay
    def _restore():
        time.sleep(0.5)
        try:
            pyperclip.copy(old_clipboard)
        except Exception:
            pass

    import threading
    threading.Thread(target=_restore, daemon=True).start()


def _paste_via_clipboard(text):
    """Copy text to clipboard and simulate Ctrl+V."""
    pyperclip.copy(text)
    time.sleep(0.05)
    pyautogui.hotkey("ctrl", "v")
