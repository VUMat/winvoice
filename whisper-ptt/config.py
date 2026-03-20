"""Loads config.yaml with sensible defaults."""

import os
import yaml

DEFAULTS = {
    "hotkey": "ctrl+`",
    "whisper_model": "small.en",
    "device": "cpu",
    "sample_rate": 16000,
    "channels": 1,
    "beep_enabled": True,
    "ai_cleanup": {
        "enabled": False,
        "provider": "ollama",
        "model": "llama3.2:3b",
        "api_key": "",
        "endpoint": "http://localhost:11434/api/generate",
    },
}

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")


def load_config(path=None):
    """Load config from YAML file, falling back to defaults for missing keys."""
    path = path or CONFIG_PATH
    cfg = dict(DEFAULTS)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            user_cfg = yaml.safe_load(f) or {}
        # Merge top-level keys
        for key, val in user_cfg.items():
            if key == "ai_cleanup" and isinstance(val, dict):
                merged = dict(DEFAULTS["ai_cleanup"])
                merged.update(val)
                cfg["ai_cleanup"] = merged
            else:
                cfg[key] = val
    return cfg
