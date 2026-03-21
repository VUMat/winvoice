"""Windowless launcher — runs main.py without a console window.

Use pythonw.exe (or double-click this .pyw file) to start Whisper PTT
as a tray-only app with no terminal.
"""

import os
import sys

# Ensure the whisper-ptt directory is on the import path and is the cwd
_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_dir)
if _dir not in sys.path:
    sys.path.insert(0, _dir)

try:
    from main import main
    main()
except Exception:
    # pythonw swallows stderr — log crashes to a file so they're not invisible
    import traceback
    log_path = os.path.join(_dir, "crash.log")
    with open(log_path, "w", encoding="utf-8") as f:
        traceback.print_exc(file=f)
