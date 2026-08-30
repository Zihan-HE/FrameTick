"""Windows display and top-level window discovery helpers."""

from typing import Optional

from .models import CaptureTarget


def list_displays() -> list[CaptureTarget]:
    """Return all physical displays exposed by MSS, excluding virtual desktop."""
    import mss

    with mss.mss() as screenshotter:
        monitors = screenshotter.monitors[1:]

    targets = []
    for index, monitor in enumerate(monitors, start=1):
        label = (
            f"Display {index} ({monitor['width']}x{monitor['height']} at "
            f"{monitor['left']},{monitor['top']})"
        )
        targets.append(CaptureTarget("display", index, label))
    return targets


def list_windows() -> list[CaptureTarget]:
    """Return visible, non-minimized top-level windows with a title."""
    import win32con
    import win32gui

    windows: list[CaptureTarget] = []

    def add_window(handle: int, _context: object) -> bool:
        if not win32gui.IsWindowVisible(handle) or win32gui.IsIconic(handle):
            return True
        title = win32gui.GetWindowText(handle).strip()
        if not title:
            return True
        ex_style = win32gui.GetWindowLong(handle, win32con.GWL_EXSTYLE)
        if ex_style & win32con.WS_EX_TOOLWINDOW:
            return True
        windows.append(CaptureTarget("window", handle, title))
        return True

    win32gui.EnumWindows(add_window, None)
    return sorted(windows, key=lambda item: item.label.casefold())


def window_bounds(handle: int) -> Optional[tuple[int, int, int, int]]:
    """Return a window's outer rectangle, or None if it is unusable."""
    import win32gui

    if not win32gui.IsWindow(handle) or win32gui.IsIconic(handle):
        return None
    left, top, right, bottom = win32gui.GetWindowRect(handle)
    if right <= left or bottom <= top:
        return None
    return left, top, right - left, bottom - top


def target_size(target: CaptureTarget) -> Optional[tuple[int, int]]:
    """Return the current pixel dimensions of a display or available window."""
    if target.kind == "window":
        bounds = window_bounds(target.identifier)
        return None if bounds is None else (bounds[2], bounds[3])
    import mss

    with mss.mss() as screenshotter:
        monitor = screenshotter.monitors[target.identifier]
    return monitor["width"], monitor["height"]
