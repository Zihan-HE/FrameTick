"""Data models shared by the application components."""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

CaptureKind = Literal["display", "window"]
PLAYBACK_FRAMES_PER_SECOND = 10


@dataclass(frozen=True)
class CaptureTarget:
    """A display or top-level window that can be captured."""

    kind: CaptureKind
    identifier: int
    label: str


@dataclass(frozen=True)
class MediaSettings:
    """Validated settings used only when a recording is rendered as media."""

    output_size: tuple[int, int]
    output_format: str
    output_stem: str
    gif_compression: str


@dataclass(frozen=True)
class RecordingSettings:
    """Validated settings for a single capture session."""

    interval_seconds: float
    capture_duration_seconds: float
    image_directory: Path
    target: CaptureTarget
    media: Optional[MediaSettings]

    @property
    def generates_media(self) -> bool:
        """Return whether the session stores temporary frames for a media export."""
        return self.media is not None

    @property
    def estimated_frame_count(self) -> int:
        """Estimate frames captured before the configured real-time stop point."""
        return max(1, math.ceil(self.capture_duration_seconds / self.interval_seconds))

    @property
    def estimated_media_duration_seconds(self) -> float:
        """Return the media duration with the fixed, smooth playback cadence."""
        return self.estimated_frame_count / PLAYBACK_FRAMES_PER_SECOND


@dataclass(frozen=True)
class CaptureEvent:
    """A thread-safe status event emitted by a recording worker."""

    kind: str
    message: str
    frame_count: Optional[int] = None
