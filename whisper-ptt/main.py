"""Whisper PTT — Push-to-talk voice-to-text with system tray icon."""

import argparse
import glob
import logging
import os
import sys
import tempfile
import threading
import time

import keyboard
from PIL import Image, ImageDraw

from config import load_config
from recorder import Recorder
from transcriber import Transcriber
from injector import inject_text
from ai_cleanup import cleanup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("whisper-ptt")

# ── State ──────────────────────────────────────────────────────────────────────
IDLE = "idle"
RECORDING = "recording"
TRANSCRIBING = "transcribing"
DONE = "done"

STATE_COLORS = {
    IDLE: "grey",
    RECORDING: "red",
    TRANSCRIBING: "orange",
    DONE: "green",
}


def _cleanup_stale_wavs():
    """Remove any orphaned whisper-ptt temp WAV files from previous runs."""
    tmp_dir = tempfile.gettempdir()
    stale = glob.glob(os.path.join(tmp_dir, "tmp*.wav"))
    for f in stale:
        try:
            # Only remove files older than 1 hour to avoid deleting active recordings
            if time.time() - os.path.getmtime(f) > 3600:
                os.unlink(f)
                logger.info("Cleaned up stale temp file: %s", f)
        except OSError:
            pass


class App:
    def __init__(self, config):
        _cleanup_stale_wavs()
        self.config = config
        self.state = IDLE
        self.recorder = Recorder(
            sample_rate=config["sample_rate"],
            channels=config["channels"],
        )
        self.transcriber = None  # lazy-loaded
        self._lock_mode = False  # double-tap lock-on mode
        self._last_hotkey_time = 0.0
        self._double_tap_threshold = 0.35  # seconds
        self._tray_icon = None
        self._stop_event = threading.Event()

    # ── Tray icon ──────────────────────────────────────────────────────────

    def _make_icon_image(self, color="grey"):
        """Generate a simple mic-shaped icon."""
        img = Image.new("RGBA", 64, 64)
        draw = ImageDraw.Draw(img)
        # Background
        draw.rectangle([0, 0, 63, 63], fill=(40, 40, 40, 255))
        # Mic body (ellipse)
        draw.ellipse([20, 8, 44, 38], fill=color)
        # Mic stand
        draw.rectangle([29, 38, 35, 50], fill=color)
        draw.rectangle([18, 50, 46, 54], fill=color)
        return img

    def _update_tray(self, state):
        """Update tray icon color to reflect current state."""
        self.state = state
        if self._tray_icon is not None:
            self._tray_icon.icon = self._make_icon_image(STATE_COLORS.get(state, "grey"))

    def _show_toast(self, msg):
        """Show a Windows toast notification via the tray icon."""
        if self._tray_icon is not None:
            try:
                self._tray_icon.notify(msg, "Whisper PTT")
            except Exception:
                pass

    # ── Beep cues ──────────────────────────────────────────────────────────

    def _beep(self, freq=800, duration=100):
        if not self.config.get("beep_enabled", True):
            return
        try:
            import winsound
            winsound.Beep(freq, duration)
        except Exception:
            pass

    # ── Model loading ──────────────────────────────────────────────────────

    def _ensure_model(self):
        if self.transcriber is None:
            self.transcriber = Transcriber(
                model_size=self.config["whisper_model"],
                device=self.config["device"],
            )

    # ── Recording flow ─────────────────────────────────────────────────────

    def _start_recording(self):
        self.recorder.start()
        self._update_tray(RECORDING)
        self._show_toast("Recording...")
        self._beep(800, 100)

    def _stop_and_transcribe(self):
        self._beep(600, 100)
        wav_path = self.recorder.stop()
        if wav_path is None:
            self._update_tray(IDLE)
            return

        self._update_tray(TRANSCRIBING)
        self._show_toast("Transcribing...")

        def _worker():
            try:
                self._ensure_model()
                text = self.transcriber.transcribe(wav_path)
                text = cleanup(text, self.config)
                if text:
                    inject_text(text)
                self._update_tray(DONE)
                time.sleep(0.8)
            except Exception:
                logger.exception("Transcription failed")
            finally:
                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
                self._update_tray(IDLE)

        threading.Thread(target=_worker, daemon=True).start()

    def _cancel_recording(self):
        self.recorder.cancel()
        self._update_tray(IDLE)
        self._beep(400, 200)
        self._show_toast("Recording cancelled")

    # ── Hotkey handlers ────────────────────────────────────────────────────

    def _on_hotkey_down(self):
        now = time.time()
        # Double-tap detection
        if now - self._last_hotkey_time < self._double_tap_threshold:
            if self._lock_mode:
                # Already in lock mode — stop
                self._lock_mode = False
                self._stop_and_transcribe()
            else:
                # Enter lock mode
                self._lock_mode = True
                if not self.recorder.is_recording:
                    self._start_recording()
                self._show_toast("Lock-on recording (tap hotkey to stop)")
            self._last_hotkey_time = 0.0
            return

        self._last_hotkey_time = now

        if self._lock_mode:
            # In lock mode, hotkey press stops recording
            self._lock_mode = False
            self._stop_and_transcribe()
            return

        if not self.recorder.is_recording:
            self._start_recording()

    def _on_hotkey_up(self):
        # In lock mode, releasing the key does nothing
        if self._lock_mode:
            return
        if self.recorder.is_recording:
            self._stop_and_transcribe()

    def _on_escape(self):
        if self.recorder.is_recording:
            self._lock_mode = False
            self._cancel_recording()

    # ── Main loop ──────────────────────────────────────────────────────────

    def run(self):
        import pystray

        hotkey = self.config["hotkey"]
        logger.info("Registering hotkey: %s", hotkey)

        # Register hotkey press/release
        keyboard.on_press_key(
            hotkey.split("+")[-1],
            lambda e: self._on_hotkey_down()
            if all(keyboard.is_pressed(k) for k in hotkey.split("+")[:-1])
            else None,
            suppress=False,
        )
        keyboard.on_release_key(
            hotkey.split("+")[-1],
            lambda e: self._on_hotkey_up(),
            suppress=False,
        )
        keyboard.on_press_key("esc", lambda e: self._on_escape(), suppress=False)

        # Tray icon
        menu = pystray.Menu(
            pystray.MenuItem("Whisper PTT", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", lambda icon, item: self._quit()),
        )
        self._tray_icon = pystray.Icon(
            "whisper-ptt",
            self._make_icon_image("grey"),
            "Whisper PTT",
            menu,
        )

        logger.info("Whisper PTT running. Hold %s to record.", hotkey)
        self._tray_icon.run()

    def _quit(self):
        if self.recorder.is_recording:
            self.recorder.cancel()
        keyboard.unhook_all()
        if self._tray_icon is not None:
            self._tray_icon.stop()


# ── CLI ────────────────────────────────────────────────────────────────────────


def _get_startup_shortcut_path():
    """Return the path to the Windows Startup folder shortcut."""
    startup_dir = os.path.join(
        os.environ.get("APPDATA", ""),
        "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
    )
    return os.path.join(startup_dir, "Whisper PTT.lnk")


def install_startup():
    """Create a shortcut in the Windows Startup folder."""
    try:
        import winshell
        from win32com.client import Dispatch
    except ImportError:
        # Fallback without winshell
        from win32com.client import Dispatch

    shortcut_path = _get_startup_shortcut_path()
    shell = Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = sys.executable
    shortcut.Arguments = f'"{os.path.abspath(__file__)}"'
    shortcut.WorkingDirectory = os.path.dirname(os.path.abspath(__file__))
    shortcut.Description = "Whisper PTT — push-to-talk voice-to-text"
    shortcut.save()
    print(f"Startup shortcut created: {shortcut_path}")
    print("Whisper PTT will now start with Windows.")
    print("You can also manage it in Task Manager > Startup tab.")


def remove_startup():
    """Remove the shortcut from the Windows Startup folder."""
    shortcut_path = _get_startup_shortcut_path()
    if os.path.exists(shortcut_path):
        os.unlink(shortcut_path)
        print(f"Startup shortcut removed: {shortcut_path}")
        print("Whisper PTT will no longer start with Windows.")
    else:
        print("No startup shortcut found — nothing to remove.")


def test_mic(config):
    """Record 3 seconds, transcribe, and print the result."""
    import time as _time

    rec = Recorder(sample_rate=config["sample_rate"], channels=config["channels"])
    print("Recording for 3 seconds...")
    rec.start()
    _time.sleep(3)
    wav_path = rec.stop()
    if wav_path is None:
        print("No audio captured.")
        return

    print("Transcribing...")
    t = Transcriber(model_size=config["whisper_model"], device=config["device"])
    text = t.transcribe(wav_path)
    os.unlink(wav_path)
    print(f"Result: {text}")


def main():
    parser = argparse.ArgumentParser(description="Whisper PTT — push-to-talk voice-to-text")
    parser.add_argument("--config", action="store_true", help="Print current config and exit")
    parser.add_argument("--model", type=str, help="Override whisper model for this session")
    parser.add_argument("--test-mic", action="store_true", help="3-second test recording + transcription")
    parser.add_argument("--install-startup", action="store_true", help="Add to Windows startup apps")
    parser.add_argument("--remove-startup", action="store_true", help="Remove from Windows startup apps")
    args = parser.parse_args()

    cfg = load_config()

    if args.model:
        cfg["whisper_model"] = args.model

    if args.config:
        import json
        print(json.dumps(cfg, indent=2))
        return

    if args.install_startup:
        install_startup()
        return

    if args.remove_startup:
        remove_startup()
        return

    if args.test_mic:
        test_mic(cfg)
        return

    app = App(cfg)
    app.run()


if __name__ == "__main__":
    main()
