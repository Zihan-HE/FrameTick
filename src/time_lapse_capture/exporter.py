"""Media encoding utilities that resample captured frames to the desired duration."""

from collections.abc import Sequence
from pathlib import Path
from typing import Callable

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageOps

ProgressCallback = Callable[[int, int], None]
GIF_COMPRESSION_PRESETS = {
    "High quality": (256, False),
    "Balanced": (128, True),
    "Small file": (64, True),
}


def build_frame_plan(source_count: int, output_count: int) -> list[int]:
    """Map output positions evenly across source frame indexes."""
    if source_count < 1:
        raise ValueError("At least one captured frame is required.")
    if output_count < 1:
        raise ValueError("At least one output frame is required.")
    if output_count == 1:
        return [0]
    return [
        round(index * (source_count - 1) / (output_count - 1))
        for index in range(output_count)
    ]


def fit_frame(image: Image.Image, output_size: tuple[int, int]) -> Image.Image:
    """Resize while preserving aspect ratio and add black letterboxing if needed."""
    width, height = output_size
    if width < 1 or height < 1:
        raise ValueError("Output dimensions must be positive.")
    normalized = ImageOps.exif_transpose(image).convert("RGB")
    contained = ImageOps.contain(normalized, output_size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", output_size, "black")
    left = (width - contained.width) // 2
    top = (height - contained.height) // 2
    canvas.paste(contained, (left, top))
    return canvas


def export_media(
    source_frames: Sequence[Path],
    destination: Path,
    output_frame_count: int,
    frames_per_second: int,
    output_size: tuple[int, int],
    gif_compression: str,
    progress_callback: ProgressCallback,
) -> None:
    """Create GIF or video media from disk-backed source frames.

    Video frames are streamed one at a time. GIF export retains quantized frames
    in memory and is intended for short clips.
    """
    if frames_per_second < 1:
        raise ValueError("Frame rate must be at least 1 FPS.")
    plan = build_frame_plan(len(source_frames), output_frame_count)
    destination.parent.mkdir(parents=True, exist_ok=True)
    suffix = destination.suffix.lower()
    if suffix == ".gif":
        _export_gif(
            source_frames,
            plan,
            destination,
            frames_per_second,
            output_size,
            gif_compression,
            progress_callback,
        )
        return
    if suffix not in {".mp4", ".webm", ".avi"}:
        raise ValueError("Supported formats are MP4, WebM, AVI, and GIF.")
    _export_video(
        source_frames,
        plan,
        destination,
        frames_per_second,
        output_size,
        progress_callback,
    )


def _read_output_frame(source_path: Path, output_size: tuple[int, int]) -> Image.Image:
    """Open one source image safely and return a detached resized image."""
    with Image.open(source_path) as source_image:
        return fit_frame(source_image, output_size)


def _export_gif(
    source_frames: Sequence[Path],
    plan: Sequence[int],
    destination: Path,
    frames_per_second: int,
    output_size: tuple[int, int],
    gif_compression: str,
    progress_callback: ProgressCallback,
) -> None:
    """Encode a GIF. GIF needs its frames at save time, so use it for short clips."""
    try:
        color_count, optimize = GIF_COMPRESSION_PRESETS[gif_compression]
    except KeyError as error:
        raise ValueError("Choose a supported GIF compression preset.") from error
    frames = []
    for position, source_index in enumerate(plan, start=1):
        image = _read_output_frame(source_frames[source_index], output_size)
        frames.append(
            image.quantize(colors=color_count, method=Image.Quantize.MEDIANCUT)
        )
        progress_callback(position, len(plan))
    duration_ms = max(1, round(1000 / frames_per_second))
    frames[0].save(
        destination,
        format="GIF",
        append_images=frames[1:],
        save_all=True,
        duration=duration_ms,
        loop=0,
        optimize=optimize,
        disposal=2,
    )


def _export_video(
    source_frames: Sequence[Path],
    plan: Sequence[int],
    destination: Path,
    frames_per_second: int,
    output_size: tuple[int, int],
    progress_callback: ProgressCallback,
) -> None:
    """Stream encoded frames to FFmpeg through ImageIO."""
    # H.264 supports arbitrary even dimensions. Disabling ImageIO's 16-pixel
    # macroblock resize preserves the resolution selected in the application.
    writer_options = {"fps": frames_per_second, "macro_block_size": 1}
    if destination.suffix.lower() == ".mp4":
        writer_options.update({"codec": "libx264", "quality": 8})
    elif destination.suffix.lower() == ".webm":
        writer_options.update({"codec": "libvpx-vp9", "quality": 8})
    else:
        writer_options.update({"codec": "mpeg4", "quality": 8})
    with imageio.get_writer(destination, format="FFMPEG", **writer_options) as writer:
        for position, source_index in enumerate(plan, start=1):
            image = _read_output_frame(source_frames[source_index], output_size)
            writer.append_data(np.asarray(image))
            progress_callback(position, len(plan))

    # A short FFmpeg job can fail on close without raising in ImageIO. Decode a
    # frame before reporting success or allowing the caller to delete sources.
    with imageio.get_reader(destination, format="FFMPEG") as reader:
        reader.get_data(0)
