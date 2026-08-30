"""Tests for safe direct image-save capture behavior."""

import re

from time_lapse_capture.capture import CaptureSession
from time_lapse_capture.models import CaptureTarget, RecordingSettings


def test_direct_capture_uses_timestamped_png_names(tmp_path) -> None:
    """Direct image mode stores a sortable local timestamp without temporary frames."""
    session = CaptureSession(
        CaptureTarget("display", 1, "Test display"),
        interval_seconds=1,
        image_directory=tmp_path,
    )
    destination = session._frame_destination()
    assert session.saves_images_directly
    assert session.frame_paths() == []
    assert destination.parent == tmp_path
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}-\d{3}\.png", destination.name
    )


def test_discard_never_removes_user_saved_images(tmp_path) -> None:
    """Direct capture mode does not treat the user-selected folder as temporary."""
    saved_image = tmp_path / "2026-08-29_12-00-00-000.png"
    saved_image.write_bytes(b"image")
    session = CaptureSession(
        CaptureTarget("display", 1, "Test display"),
        interval_seconds=1,
        image_directory=tmp_path,
    )
    session.discard()
    assert saved_image.exists()


def test_preserve_frames_moves_temporary_media_images(tmp_path) -> None:
    """Retained media frames leave the system temporary directory."""
    session = CaptureSession(
        CaptureTarget("display", 1, "Test display"), interval_seconds=1
    )
    assert session.frame_directory is not None
    source_frame = session.frame_directory / "frame_00000001.png"
    source_frame.write_bytes(b"image")
    destination = tmp_path / "recording_frames"

    kept_directory = session.preserve_frames(destination)

    assert kept_directory == destination
    assert (destination / source_frame.name).read_bytes() == b"image"


def test_recording_estimate_uses_real_duration_and_second_interval(tmp_path) -> None:
    """Media duration is derived from captured frames, not a user-entered FPS."""
    settings = RecordingSettings(
        interval_seconds=5,
        capture_duration_seconds=61,
        image_directory=tmp_path,
        target=CaptureTarget("display", 1, "Test display"),
        media=None,
    )
    assert settings.estimated_frame_count == 13
    assert settings.estimated_media_duration_seconds == 1.3
