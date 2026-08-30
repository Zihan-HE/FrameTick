"""Low-overhead periodic screen capture worker."""

import queue
import shutil
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import CaptureEvent, CaptureTarget
from .targets import window_bounds


class CaptureSession:
    """Capture frames on a worker thread and write each one directly to disk."""

    def __init__(
        self,
        target: CaptureTarget,
        interval_seconds: float,
        max_duration_seconds: Optional[float] = None,
        image_directory: Optional[Path] = None,
    ) -> None:
        """Create a session that uses temporary or timestamped permanent frames.

        Passing ``image_directory`` enables direct image-save mode. Omitting it
        stores temporary frames for a later video or GIF export.
        """
        self._target = target
        self._interval_seconds = interval_seconds
        self._max_duration_seconds = max_duration_seconds
        self._image_directory = image_directory
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.events: queue.Queue[CaptureEvent] = queue.Queue()
        self.frame_directory = (
            None
            if image_directory is not None
            else Path(tempfile.mkdtemp(prefix="time-lapse-capture-"))
        )
        self.frame_count = 0

    @property
    def saves_images_directly(self) -> bool:
        """Return whether frames are being retained in the user-selected folder."""
        return self._image_directory is not None

    @property
    def running(self) -> bool:
        """Return whether the worker thread is currently active."""
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Start the periodic worker. A session instance can only run once."""
        if self._thread is not None:
            raise RuntimeError("A capture session cannot be started twice.")
        self._thread = threading.Thread(
            target=self._capture_loop,
            name="time-lapse-capture",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Request a clean, prompt stop without blocking the UI thread."""
        self._stop_event.set()

    def frame_paths(self) -> list[Path]:
        """Return the saved frames in capture order."""
        if self.frame_directory is None:
            return []
        return sorted(self.frame_directory.glob("frame_*.png"))

    def discard(self) -> None:
        """Remove stored source frames after the worker has stopped."""
        if self.running:
            raise RuntimeError("Stop recording before discarding frames.")
        if self.frame_directory is None:
            return
        for frame_path in self.frame_directory.glob("frame_*.png"):
            frame_path.unlink(missing_ok=True)
        self.frame_directory.rmdir()

    def preserve_frames(self, destination: Path) -> Path:
        """Move temporary media frames to a user-visible output directory."""
        if self.running:
            raise RuntimeError("Stop recording before preserving frames.")
        if self.frame_directory is None:
            raise RuntimeError("This session does not use temporary media frames.")
        if destination.exists():
            raise FileExistsError("The destination frame folder already exists.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(self.frame_directory), str(destination))
        self.frame_directory = destination
        return destination

    def _capture_loop(self) -> None:
        """Capture on a monotonic schedule, avoiding UI-thread work and busy waits."""
        import mss
        import mss.tools

        started_at = time.monotonic()
        stop_at = (
            None
            if self._max_duration_seconds is None
            else started_at + self._max_duration_seconds
        )
        next_capture_at = started_at
        self.events.put(CaptureEvent("started", "Recording started."))
        try:
            with mss.mss() as screenshotter:
                while not self._stop_event.is_set():
                    if stop_at is not None and time.monotonic() >= stop_at:
                        break
                    capture_area = self._capture_area(screenshotter.monitors)
                    if capture_area is None:
                        self.events.put(
                            CaptureEvent(
                                "error",
                                "The selected window is closed or minimized. "
                                "Recording stopped.",
                            )
                        )
                        break
                    image = screenshotter.grab(capture_area)
                    self.frame_count += 1
                    destination = self._frame_destination()
                    mss.tools.to_png(image.rgb, image.size, output=str(destination))
                    self.events.put(
                        CaptureEvent(
                            "frame",
                            f"Captured frame {self.frame_count}.",
                            self.frame_count,
                        )
                    )
                    next_capture_at += self._interval_seconds
                    wait_seconds = max(0.0, next_capture_at - time.monotonic())
                    if stop_at is not None:
                        wait_seconds = min(
                            wait_seconds,
                            max(0.0, stop_at - time.monotonic()),
                        )
                    if self._stop_event.wait(wait_seconds):
                        break
        except Exception as error:  # The UI must remain usable after capture errors.
            self.events.put(CaptureEvent("error", f"Capture failed: {error}"))
        finally:
            self.events.put(
                CaptureEvent(
                    "stopped",
                    self._stop_message(),
                    self.frame_count,
                )
            )

    def _frame_destination(self) -> Path:
        """Return a non-conflicting path for the next captured PNG frame."""
        if self.frame_directory is not None:
            return self.frame_directory / f"frame_{self.frame_count:08d}.png"
        if self._image_directory is None:
            raise RuntimeError("A capture destination was not configured.")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]
        destination = self._image_directory / f"{timestamp}.png"
        suffix = 1
        while destination.exists():
            destination = self._image_directory / f"{timestamp}-{suffix:02d}.png"
            suffix += 1
        return destination

    def _stop_message(self) -> str:
        """Describe whether the stopped session saved images or awaits export."""
        if self.saves_images_directly:
            return f"Recording stopped. Saved {self.frame_count} image(s)."
        return f"Recording stopped. {self.frame_count} frame(s) are ready to export."

    def _capture_area(self, monitors: list[dict]) -> Optional[dict]:
        """Resolve current pixels for a display or movable selected window."""
        if self._target.kind == "display":
            return monitors[self._target.identifier]
        bounds = window_bounds(self._target.identifier)
        if bounds is None:
            return None
        left, top, width, height = bounds
        return {"left": left, "top": top, "width": width, "height": height}
