"""Tests for safe preference handling."""

import json

from time_lapse_capture import config


def test_load_preferences_rejects_non_object_json(monkeypatch, tmp_path) -> None:
    """Unexpected local JSON cannot break application startup."""
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
    monkeypatch.setattr(config, "settings_path", lambda: settings_file)
    assert config.load_preferences() == {}


def test_save_preferences_writes_json(monkeypatch, tmp_path) -> None:
    """Preference writes create their parent directory and remain readable."""
    settings_file = tmp_path / "nested" / "settings.json"
    monkeypatch.setattr(config, "settings_path", lambda: settings_file)
    config.save_preferences({"fps": "12"})
    assert json.loads(settings_file.read_text(encoding="utf-8")) == {"fps": "12"}
