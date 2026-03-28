"""Settings persistence and runtime configuration helpers for Kimiko.

This module centralizes settings access so both the Flask settings UI and the
main AI runtime can share one source of truth.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import threading
from typing import Any

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_FILE = PROJECT_ROOT / "settings.json"
UPLOADS_DIR = PROJECT_ROOT / "webui" / "static" / "uploads"
GHOSTS_DIR = PROJECT_ROOT / "webui" / "static" / "ghosts"

DEFAULT_SETTINGS: dict[str, Any] = {
    "modules": {
        "consciousness": [],
        "speech": {
            "voice": "default",
            "enabled": True,
        },
        "minecraft_mode": False,
    },
    "model": {
        "ghost_image": "default.svg",
    },
    "memory": {
        "context_modules": [],
    },
    "data": {
        "stored": True,
    },
}

# Shared runtime object that other modules can import for latest settings.
GLOBAL_CONFIG: dict[str, Any] = deepcopy(DEFAULT_SETTINGS)


class SettingsManager:
    """Loads, updates, and persists JSON settings with thread safety."""

    def __init__(self, settings_path: Path | None = None) -> None:
        self.settings_path = settings_path or SETTINGS_FILE
        self._lock = threading.RLock()
        self.settings: dict[str, Any] = {}
        self.load_settings()

    def _deep_merge(self, base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
        merged = deepcopy(base)
        for key, value in incoming.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _sync_global(self) -> None:
        GLOBAL_CONFIG.clear()
        GLOBAL_CONFIG.update(deepcopy(self.settings))

    def load_settings(self) -> dict[str, Any]:
        with self._lock:
            if not self.settings_path.exists():
                self.settings = deepcopy(DEFAULT_SETTINGS)
                self.save_settings(self.settings)
                return deepcopy(self.settings)

            try:
                loaded = json.loads(self.settings_path.read_text(encoding="utf-8"))
                if not isinstance(loaded, dict):
                    raise ValueError("settings.json must contain an object")
                self.settings = self._deep_merge(DEFAULT_SETTINGS, loaded)
            except (json.JSONDecodeError, OSError, ValueError, TypeError):
                self.settings = deepcopy(DEFAULT_SETTINGS)
                self.save_settings(self.settings)

            self._sync_global()
            return deepcopy(self.settings)

    def save_settings(self, new_settings: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            if new_settings is not None:
                self.settings = self._deep_merge(DEFAULT_SETTINGS, new_settings)
            self.settings_path.write_text(
                json.dumps(self.settings, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            self._sync_global()
            return deepcopy(self.settings)

    def get(self, key: str | None = None) -> Any:
        with self._lock:
            if key is None:
                return deepcopy(self.settings)
            current: Any = self.settings
            for part in key.split("."):
                if not isinstance(current, dict):
                    return None
                current = current.get(part)
                if current is None:
                    return None
            return deepcopy(current)

    def set(self, key: str, value: Any) -> dict[str, Any]:
        with self._lock:
            current: Any = self.settings
            parts = key.split(".")
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
            return self.save_settings(self.settings)

    def update(self, partial_settings: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self.settings = self._deep_merge(self.settings, partial_settings)
            return self.save_settings(self.settings)

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self.settings = deepcopy(DEFAULT_SETTINGS)
            return self.save_settings(self.settings)


SETTINGS = SettingsManager()


def get_settings_manager() -> SettingsManager:
    return SETTINGS


def list_voices() -> list[dict[str, str]]:
    """Return pyttsx3 voices in a UI-friendly format."""
    if pyttsx3 is None:
        return []

    engine = pyttsx3.init()
    voices: list[dict[str, str]] = []
    for voice in engine.getProperty("voices"):
        voices.append(
            {
                "id": str(getattr(voice, "id", "")),
                "name": str(getattr(voice, "name", "Unknown")),
            }
        )
    return voices


def speak(text: str) -> None:
    """Speak text using pyttsx3 when speech is enabled in settings."""
    if not text:
        return

    if pyttsx3 is None:
        return

    settings = SETTINGS.get()
    speech_settings = settings.get("modules", {}).get("speech", {})
    if not speech_settings.get("enabled", True):
        return

    engine = pyttsx3.init()
    selected_voice = speech_settings.get("voice", "default")
    if selected_voice != "default":
        for voice in engine.getProperty("voices"):
            if getattr(voice, "id", "") == selected_voice:
                engine.setProperty("voice", selected_voice)
                break

    engine.say(text)
    engine.runAndWait()
