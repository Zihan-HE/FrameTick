"""Tests for deterministic frame planning and image sizing."""

from PIL import Image

from time_lapse_capture.exporter import build_frame_plan, export_media, fit_frame


def test_build_frame_plan_spans_all_source_frames() -> None:
    """A resampling plan retains the beginning and end of a recording."""
    assert build_frame_plan(5, 9) == [0, 0, 1, 2, 2, 2, 3, 4, 4]


def test_build_frame_plan_rejects_empty_input() -> None:
    """An export cannot be produced without recorded material."""
    try:
        build_frame_plan(0, 1)
    except ValueError as error:
        assert "captured frame" in str(error)
    else:
        raise AssertionError("Empty input should raise ValueError.")


def test_fit_frame_preserves_aspect_ratio_with_padding() -> None:
    """Wide content receives top and bottom letterboxing in a square output."""
    source = Image.new("RGB", (4, 2), "red")
    output = fit_frame(source, (4, 4))
    assert output.size == (4, 4)
    assert output.getpixel((0, 0)) == (0, 0, 0)
    assert output.getpixel((0, 2)) == (255, 0, 0)


def test_gif_export_rejects_unknown_compression_preset(tmp_path) -> None:
    """GIF output accepts only the small, documented set of compression presets."""
    source = tmp_path / "source.png"
    destination = tmp_path / "output.gif"
    Image.new("RGB", (2, 2), "blue").save(source)
    try:
        export_media(
            [source],
            destination,
            output_frame_count=1,
            frames_per_second=1,
            output_size=(2, 2),
            gif_compression="Unknown preset",
            progress_callback=lambda _current, _total: None,
        )
    except ValueError as error:
        assert "GIF compression" in str(error)
    else:
        raise AssertionError("An unknown GIF compression preset should fail.")


def test_gif_export_creates_a_standard_animated_gif(tmp_path) -> None:
    """GIF output has an animated GIF container and the requested frame count."""
    first, second = tmp_path / "first.png", tmp_path / "second.png"
    destination = tmp_path / "output.gif"
    Image.new("RGB", (4, 4), "red").save(first)
    Image.new("RGB", (4, 4), "blue").save(second)

    export_media(
        [first, second],
        destination,
        output_frame_count=2,
        frames_per_second=10,
        output_size=(4, 4),
        gif_compression="Balanced",
        progress_callback=lambda _current, _total: None,
    )

    with Image.open(destination) as output:
        assert output.format == "GIF"
        assert output.n_frames == 2
