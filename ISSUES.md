# Known Usability Issues

Tracked issues for Whisper PTT. These should be filed as GitHub Issues when repo access is available.

---

### 1. No progress indicator during first-run model download

**Priority:** High

The first whisper model load takes 30-60s+ (download + initialization). The tray icon sits grey with no feedback — the app looks frozen. Should show a toast like "Loading whisper model..." or add a `LOADING` state with a distinct tray icon color.

**File:** `whisper-ptt/main.py` — `_ensure_model()`

---

### 2. No microphone device selection

**Priority:** Medium

Always uses the system default microphone. Users with multiple audio devices (headset, webcam mic, USB mic) have no way to select one without changing Windows defaults.

Add a `mic_device` config option — `sounddevice` already supports device selection by name or index.

**File:** `whisper-ptt/recorder.py`, `whisper-ptt/config.yaml`

---

### 3. Text injection visibly slow for long transcriptions

**Priority:** High

`pyautogui.typewrite(interval=0.01)` types at ~100 chars/sec. For longer transcriptions (50+ words), this is noticeably slow and distracting. Should default to clipboard-paste (`Ctrl+V`) for all text, not just Unicode, with an optional `inject_method: clipboard|typewrite` config option.

**File:** `whisper-ptt/injector.py`

---

### 4. Double-tap lock-on threshold not configurable

**Priority:** Low

The 0.35s double-tap threshold for lock-on mode is hardcoded. Different users have different reaction speeds. Add a `double_tap_threshold` config option.

**File:** `whisper-ptt/main.py` — `App.__init__()`, `whisper-ptt/config.yaml`

---

### 5. Errors silently swallowed — no user feedback on failure

**Priority:** High

Multiple `except: pass` blocks in beep, toast, and transcription code paths. If the microphone fails, model loading errors, or transcription crashes, the user gets zero feedback — the app just silently returns to idle. Should show a toast notification on failure at minimum.

**Files:** `whisper-ptt/main.py`, `whisper-ptt/recorder.py`

---

### 6. Clipboard restoration race condition after paste injection

**Priority:** Medium

After injecting text via `Ctrl+V`, the original clipboard content is restored after a fixed 0.5s delay. Slow applications (especially Electron-based apps like VS Code, Slack, Discord) may not have consumed the paste yet, causing the wrong text to appear or clipboard corruption.

Consider increasing the delay, making it configurable, or using a smarter detection mechanism.

**File:** `whisper-ptt/injector.py`
