# Known Usability Issues

Tracked issues for Whisper PTT. These should be filed as GitHub Issues when repo access is available.

---

### 1. ~~No progress indicator during first-run model download~~ ✓ Fixed

**Priority:** High

**Resolution:** Added `LOADING` state (blue tray icon) and toast notifications ("Loading whisper model..." / "Model loaded") during `_ensure_model()`.

---

### 2. ~~No microphone device selection~~ ✓ Fixed

**Priority:** Medium

**Resolution:** Added `mic_device` config option (null = system default, or device name/index). Passed through `Recorder` to `sd.InputStream(device=...)`.

---

### 3. ~~Text injection visibly slow for long transcriptions~~ ✓ Fixed

**Priority:** High

**Resolution:** Default injection method changed to `clipboard` (Ctrl+V). Added `inject_method` config option (`clipboard` or `typewrite`).

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
