"""Opt-in packaged export smoke test using synthetic images, never screenshots."""

import json
import traceback
from pathlib import Path
from tempfile import TemporaryDirectory

import imageio.v2 as imageio
from PIL import Image

from . import __version__
from .exporter import export_media


def check_exports(output_directory: Path) -> int:
    """Exercise the real frozen export dependencies and save a JSON report."""
    output_directory.mkdir(parents=True, exist_ok=True)
    results = []
    try:
        with TemporaryDirectory(prefix="frametick-check-") as source_directory:
            paths = []
            for index, color in enumerate(("red", "blue")):
                path = Path(source_directory) / f"{index}.png"
                Image.new("RGB", (1440, 2560), color).save(path)
                paths.append(path)
            for extension in ("mp4", "webm", "avi", "gif"):
                for count in (1, 2):
                    destination = output_directory / f"check-{count}.{extension}"
                    export_media(
                        paths[:count],
                        destination,
                        count,
                        10,
                        (1440, 2560),
                        "Balanced",
                        lambda _current, _total: None,
                    )
                    if extension == "gif":
                        with Image.open(destination) as decoded:
                            assert decoded.n_frames == count
                            assert decoded.size == (1440, 2560)
                    else:
                        with imageio.get_reader(destination, format="FFMPEG") as reader:
                            assert reader.count_frames() == count
                            assert reader.get_data(0).shape == (2560, 1440, 3)
                    results.append({"file": destination.name, "frames": count})
    except Exception:
        report = {
            "version": __version__,
            "ok": False,
            "results": results,
            "error": traceback.format_exc(),
        }
    else:
        report = {"version": __version__, "ok": True, "results": results}
    (output_directory / "report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return 0 if report["ok"] else 1
