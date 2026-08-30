"""Generate checked-in PNG and ICO application assets."""

from pathlib import Path

from PIL import Image, ImageDraw


def draw_icon(size: int) -> Image.Image:
    """Create the FrameTick capture-frame mark at the requested size."""
    image = Image.new("RGBA", (size, size), (15, 20, 27, 255))
    draw = ImageDraw.Draw(image)
    stroke, margin, corner = max(2, size // 16), size // 7, size // 4
    color = (243, 246, 249, 255)
    lines = (
        (margin, margin + corner, margin, margin, margin + corner, margin),
        (
            size - margin - corner,
            margin,
            size - margin,
            margin,
            size - margin,
            margin + corner,
        ),
        (
            margin,
            size - margin - corner,
            margin,
            size - margin,
            margin + corner,
            size - margin,
        ),
        (
            size - margin - corner,
            size - margin,
            size - margin,
            size - margin,
            size - margin,
            size - margin - corner,
        ),
    )
    for points in lines:
        draw.line(points, fill=color, width=stroke, joint="curve")
    radius, center = size // 7, size // 2
    draw.ellipse(
        (center - radius, center - radius, center + radius, center + radius),
        fill=(154, 168, 182, 255),
    )
    return image


def main() -> None:
    """Write the icon files used by the window and PyInstaller."""
    assets = Path(__file__).resolve().parents[1] / "assets"
    assets.mkdir(exist_ok=True)
    icon = draw_icon(256)
    icon.save(assets / "frametick.png")
    icon.save(
        assets / "frametick.ico",
        sizes=[
            (16, 16),
            (24, 24),
            (32, 32),
            (48, 48),
            (64, 64),
            (128, 128),
            (256, 256),
        ],
    )


if __name__ == "__main__":
    main()
