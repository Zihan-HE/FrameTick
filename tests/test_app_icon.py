"""Tests for the application activity indicator."""

from time_lapse_capture.app import TEXT, create_app_icon, normalize_output_stem


def test_activity_icons_have_distinct_center_colors() -> None:
    """Idle, recording, and processing states remain visually distinct."""
    center = (32, 32)
    colors = {
        create_app_icon(state).getpixel(center)
        for state in ("idle", "recording", "processing")
    }
    assert len(colors) == 3


def test_activity_titles_are_localized() -> None:
    """Both supported languages expose recording and processing titles."""
    assert TEXT["zh"]["title_recording"].endswith("（录制中）")
    assert TEXT["zh"]["title_processing"].endswith("（处理中）")
    assert TEXT["en"]["title_recording"].endswith("(Recording)")
    assert TEXT["en"]["title_processing"].endswith("(Processing)")
    assert TEXT["zh"]["notification_folder"].startswith("保存位置")
    assert TEXT["en"]["notification_folder"].startswith("Saved in")


def test_output_stem_removes_accidental_extensions() -> None:
    """The UI cannot generate names such as example.gif.gif by accident."""
    assert normalize_output_stem("screen.gif") == "screen"
    assert normalize_output_stem("screen.gif.mp4") == "screen"
    assert normalize_output_stem("screen capture") == "screen capture"
