"""Windowless launcher — runs main.py without a console window.

Use pythonw.exe (or double-click this .pyw file) to start Whisper PTT
as a tray-only app with no terminal.
"""

import runpy
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.argv = sys.argv[:1]  # strip launcher name, keep only flags if any

runpy.run_module("main", run_name="__main__", alter_sys=True)
