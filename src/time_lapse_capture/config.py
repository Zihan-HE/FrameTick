"""Small, defensive persistence layer for user preferences."""

import json
import os
from pathlib import Path
from typing import Any

APP_DIRECTORY_NAME = "TimeLapseCapture"
SETTINGS_FILE_NAME = "settings.json"


def settings_path() -> Path:
    """Return the platform-appropriate path for user preferences."""
    app_data = os.environ.get("APPDATA")
    base_directory = Path(app_data) if app_data else Path.home() / ".config"
    return base_directory / APP_DIRECTORY_NAME / SETTINGS_FILE_NAME


def load_preferences() -> dict[str, Any]:
    """Load preferences, returning an empty dictionary for invalid local data."""
    path = settings_path()
    try:
        with path.open("r", encoding="utf-8") as settings_file:
            data = json.load(settings_file)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_preferences(preferences: dict[str, Any]) -> None:
    """Atomically save JSON-serializable preferences to the user profile."""
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".tmp")
    with temporary_path.open("w", encoding="utf-8") as settings_file:
        json.dump(preferences, settings_file, indent=2, ensure_ascii=False)
    temporary_path.replace(path)
