# Whisper PTT

A lightweight Windows push-to-talk voice-to-text tool. Hold a hotkey, speak, release — your words are transcribed locally via faster-whisper and pasted into the focused window. 100% offline.

## Install

```
cd whisper-ptt
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```
python main.py                  # Start with console window (useful for debugging)
pythonw run.pyw                 # Start without console window (tray-only, recommended)
python main.py --test-mic       # 3-second mic test + transcription
python main.py --config         # Print current configuration
python main.py --model base.en  # Override model for this session
python main.py --install-startup  # Add to Windows startup apps
python main.py --remove-startup   # Remove from Windows startup
```

You can also double-click `run.pyw` in Explorer to launch the tray-only mode.

## How It Works

1. **Hold** `Ctrl+`` ` to record (push-to-talk)
2. **Double-tap** the hotkey to lock-on recording (hands-free); tap again to stop
3. **Esc** cancels the current recording
4. On release, audio is transcribed locally and pasted into the active window

## Configuration

Edit `config.yaml` to change the hotkey, whisper model, or enable AI cleanup:

```yaml
hotkey: "ctrl+`"
whisper_model: "small.en"    # tiny.en / base.en / small.en / medium.en
device: "cpu"                # cpu or cuda
sample_rate: 16000
channels: 1
beep_enabled: true
beep_volume: 0.1             # 0.0 (silent) to 1.0 (full volume)
ai_cleanup:
  enabled: false
  provider: "ollama"         # ollama / openai / anthropic
  model: "llama3.2:3b"
```

## Requirements

- Windows 10/11
- Python 3.10+
- ~500 MB RAM for small.en model (idle CPU usage ~0%)

## Startup

To start Whisper PTT with Windows:
```
python main.py --install-startup
```
This creates a shortcut in your Windows Startup folder. You can then enable/disable it from **Task Manager > Startup** tab like any other startup app.

To remove:
```
python main.py --remove-startup
```
