"""Camera-inspired desktop interface for FrameTick."""

from __future__ import annotations

import contextlib
import ctypes
import math
import queue
import re
import threading
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from PIL import Image, ImageDraw, ImageTk

from .capture import CaptureSession
from .config import load_preferences, save_preferences
from .exporter import export_media
from .models import (
    PLAYBACK_FRAMES_PER_SECOND,
    CaptureEvent,
    CaptureTarget,
    MediaSettings,
    RecordingSettings,
)
from .targets import list_displays, list_windows, target_size

COLORS = {
    "bg": "#ffffff",
    "card": "#ffffff",
    "field": "#ffffff",
    "border": "#d6dbe1",
    "text": "#20242a",
    "muted": "#68717d",
    "soft": "#eef1f4",
    "red": "#e5484d",
    "red_dark": "#b92f35",
    "yellow": "#e5a72e",
}
VIDEO_FORMATS = ("mp4", "webm", "avi")
EXTENSIONS = {"mp4": ".mp4", "webm": ".webm", "avi": ".avi", "gif": ".gif"}
RESOLUTIONS = ("1280x720", "1366x768", "1920x1080", "2560x1440", "3840x2160")
UNITS = {"seconds": 1, "minutes": 60, "hours": 3600}
GIF_VALUES = {"high": "High quality", "balanced": "Balanced", "small": "Small file"}

TEXT = {
    "zh": {
        "title": "拾刻 FrameTick",
        "title_recording": "拾刻 FrameTick（录制中）",
        "title_processing": "拾刻 FrameTick（处理中）",
        "language": "语言",
        "capture": "拍摄目标",
        "display": "显示器",
        "window": "窗口",
        "refresh": "刷新",
        "duration": "录制时长",
        "interval": "截图间隔",
        "seconds": "秒",
        "minutes": "分钟",
        "hours": "小时",
        "mode": "输出模式",
        "images": "保留图片",
        "video": "视频",
        "gif": "GIF",
        "mode_images": "按拍摄时间命名 PNG 图片，直接保存到文件夹。",
        "mode_video": "录制结束后自动生成视频。",
        "mode_gif": "录制结束后自动生成 GIF。",
        "media": "成片设置",
        "resolution": "输出分辨率",
        "auto": "自动（{size}）",
        "auto_unknown": "自动（当前目标）",
        "custom": "自定义…",
        "custom_size": "自定义尺寸",
        "format": "视频格式",
        "compression": "GIF 压缩",
        "delete_frames": "生成后删除临时图片",
        "high": "高质量",
        "balanced": "平衡",
        "small": "小文件",
        "estimate": "预计 {frames} 帧 · 成片 {duration} 秒 · 约 {size}",
        "estimate_unknown": "设置有效参数后显示成片时长与文件大小估算。",
        "folder": "保存位置",
        "browse": "选择文件夹",
        "file_name": "文件名前缀",
        "record": "开始录制",
        "stop": "停止录制",
        "ready": "准备就绪",
        "found": "已找到 {count} 个可拍摄目标",
        "recording": "正在录制 · 已拍摄 {count} 帧",
        "stopping": "正在停止…",
        "exporting": "正在生成成片… {progress}",
        "saved_images": "完成：已保存 {count} 张图片",
        "saved_media": "完成：已保存到 {path}",
        "frames_kept": "完成：已保存到 {path}；图片保留在 {folder}",
        "tray_show": "显示拾刻",
        "tray_start": "开始录制",
        "tray_stop": "停止录制",
        "tray_exit": "退出",
        "tray_hint": "拾刻仍在系统托盘运行。",
        "notification_recording_done": "录制完成",
        "notification_processing_done": "处理完成",
        "notification_folder": "保存位置：{folder}",
        "settings_error": "请检查设置",
        "capture_error": "截屏失败",
        "export_error": "生成失败",
        "select_target": "请选择一个拍摄目标。",
        "valid_interval": "截图间隔必须是不小于 0.2 秒的数字。",
        "valid_duration": "录制时长必须在 0.2 秒到 24 小时之间。",
        "valid_folder": "请选择一个存在的保存文件夹。",
        "valid_resolution": "分辨率应为 宽x高，例如 1920x1080。",
        "valid_even": "视频宽度和高度都必须是偶数。",
        "valid_name": "文件名前缀为空或包含 Windows 不允许的字符。",
        "target_size_error": "无法读取目标分辨率，请选择固定分辨率。",
    },
    "en": {
        "title": "FrameTick",
        "title_recording": "FrameTick (Recording)",
        "title_processing": "FrameTick (Processing)",
        "language": "Language",
        "capture": "Capture target",
        "display": "Display",
        "window": "Window",
        "refresh": "Refresh",
        "duration": "Recording duration",
        "interval": "Capture interval",
        "seconds": "Seconds",
        "minutes": "Minutes",
        "hours": "Hours",
        "mode": "Output mode",
        "images": "Images only",
        "video": "Video",
        "gif": "GIF",
        "mode_images": "Save timestamped PNG images directly to the folder.",
        "mode_video": "Build a video automatically after recording.",
        "mode_gif": "Build a GIF automatically after recording.",
        "media": "Media settings",
        "resolution": "Output resolution",
        "auto": "Auto ({size})",
        "auto_unknown": "Auto (current target)",
        "custom": "Custom…",
        "custom_size": "Custom size",
        "format": "Video format",
        "compression": "GIF compression",
        "delete_frames": "Delete temporary images after export",
        "high": "High quality",
        "balanced": "Balanced",
        "small": "Small file",
        "estimate": "About {frames} frames · {duration}s media · {size}",
        "estimate_unknown": "Enter valid settings to estimate media length and size.",
        "folder": "Save to",
        "browse": "Choose folder",
        "file_name": "File prefix",
        "record": "Start recording",
        "stop": "Stop recording",
        "ready": "Ready",
        "found": "Found {count} capture target(s)",
        "recording": "Recording · {count} frame(s) captured",
        "stopping": "Stopping…",
        "exporting": "Creating media… {progress}",
        "saved_images": "Finished: saved {count} image(s)",
        "saved_media": "Finished: saved to {path}",
        "frames_kept": "Finished: saved to {path}; images kept in {folder}",
        "tray_show": "Show FrameTick",
        "tray_start": "Start recording",
        "tray_stop": "Stop recording",
        "tray_exit": "Exit",
        "tray_hint": "FrameTick is still running in the system tray.",
        "notification_recording_done": "Recording finished",
        "notification_processing_done": "Processing finished",
        "notification_folder": "Saved in: {folder}",
        "settings_error": "Check settings",
        "capture_error": "Capture failed",
        "export_error": "Export failed",
        "select_target": "Choose a capture target.",
        "valid_interval": "Capture interval must be at least 0.2 seconds.",
        "valid_duration": (
            "Recording duration must be between 0.2 seconds and 24 hours."
        ),
        "valid_folder": "Choose an existing output folder.",
        "valid_resolution": "Use WIDTHxHEIGHT, for example 1920x1080.",
        "valid_even": "Video width and height must both be even.",
        "valid_name": "The file prefix is empty or contains invalid characters.",
        "target_size_error": "Target resolution is unavailable; choose a fixed size.",
    },
}


def create_app_icon(state: str = "idle", size: int = 64) -> Image.Image:
    """Draw the app icon with a center color matching the activity state."""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    stroke, margin, corner = max(2, size // 16), size // 7, size // 4
    color = (45, 52, 60, 255)
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
    fills = {
        "idle": (154, 168, 182, 255),
        "recording": (229, 72, 77, 255),
        "processing": (229, 167, 46, 255),
    }
    fill = fills.get(state, fills["idle"])
    draw.ellipse(
        (center - radius, center - radius, center + radius, center + radius), fill=fill
    )
    return image


def normalize_output_stem(value: str) -> str:
    """Remove accidental media extensions from a user-entered file prefix."""
    stem = value.strip()
    while True:
        suffix = next(
            (item for item in EXTENSIONS.values() if stem.lower().endswith(item)),
            None,
        )
        if suffix is None:
            return stem
        stem = stem[: -len(suffix)].rstrip()


class RoundedButton(tk.Canvas):
    """Small canvas button with restrained rounded corners and keyboard support."""

    def __init__(
        self,
        parent: tk.Widget,
        command,
        *,
        width: int = 112,
        height: int = 38,
        radius: int = 6,
        text: str = "",
        font=None,
        background: str = "#eef1f4",
        foreground: str = "#20242a",
        activebackground: str = "#e2e6ea",
        activeforeground: str = "#20242a",
        surface: str = "#ffffff",
    ) -> None:
        super().__init__(
            parent,
            width=width,
            height=height,
            background=surface,
            highlightthickness=0,
            borderwidth=0,
            cursor="hand2",
            takefocus=True,
        )
        self.command = command
        self.radius = radius
        self.button_text = text
        self.button_font = font
        self.normal_background = background
        self.normal_foreground = foreground
        self.active_background = activebackground
        self.active_foreground = activeforeground
        self.button_state = "normal"
        self.bind("<Button-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<Leave>", lambda _event: self._draw(False))
        self.bind("<Return>", lambda _event: self.invoke())
        self.bind("<space>", lambda _event: self.invoke())
        self._draw(False)

    def _rounded_rectangle(self, fill: str) -> None:
        width = int(self.cget("width"))
        height = int(self.cget("height"))
        radius = min(self.radius, (height - 2) // 2)
        left, top, right, bottom = 1, 1, width - 1, height - 1

        # Use exact circles and rectangles. A smoothed polygon distorts short
        # buttons because Tk interpolates its control points unevenly.
        self.create_rectangle(
            left + radius, top, right - radius, bottom, fill=fill, outline=""
        )
        self.create_rectangle(
            left, top + radius, right, bottom - radius, fill=fill, outline=""
        )
        diameter = radius * 2
        for x, y in (
            (left, top),
            (right - diameter, top),
            (left, bottom - diameter),
            (right - diameter, bottom - diameter),
        ):
            self.create_oval(
                x,
                y,
                x + diameter,
                y + diameter,
                fill=fill,
                outline="",
            )

    def _draw(self, active: bool) -> None:
        self.delete("all")
        disabled = self.button_state == "disabled"
        background = (
            "#e6e8eb"
            if disabled
            else self.active_background
            if active
            else self.normal_background
        )
        foreground = (
            "#9aa1aa"
            if disabled
            else self.active_foreground
            if active
            else self.normal_foreground
        )
        self._rounded_rectangle(background)
        self.create_text(
            int(self.cget("width")) // 2,
            int(self.cget("height")) // 2,
            text=self.button_text,
            fill=foreground,
            font=self.button_font,
        )

    def _press(self, _event: tk.Event) -> None:
        if self.button_state != "disabled":
            self._draw(True)

    def _release(self, event: tk.Event) -> None:
        self._draw(False)
        if (
            self.button_state == "normal"
            and 0 <= event.x <= int(self.cget("width"))
            and 0 <= event.y <= int(self.cget("height"))
        ):
            self.invoke()

    def invoke(self) -> None:
        if self.button_state == "normal" and self.command is not None:
            self.command()

    def configure(self, cnf=None, **kwargs):  # type: ignore[override]
        """Support the subset of button options used by the application."""
        options = dict(cnf or {})
        options.update(kwargs)
        mapping = {
            "text": "button_text",
            "font": "button_font",
            "background": "normal_background",
            "bg": "normal_background",
            "activebackground": "active_background",
            "foreground": "normal_foreground",
            "fg": "normal_foreground",
            "activeforeground": "active_foreground",
            "state": "button_state",
        }
        for key, attribute in mapping.items():
            if key in options:
                setattr(self, attribute, options.pop(key))
        if options:
            super().configure(options)
        self._draw(False)

    config = configure


class LargeCheckButton(tk.Canvas):
    """A readable, keyboard-accessible checkbox for important choices."""

    def __init__(
        self,
        parent: tk.Widget,
        variable: tk.BooleanVar,
        *,
        width: int = 320,
        height: int = 32,
        text: str = "",
        font=None,
        surface: str = "#ffffff",
    ) -> None:
        super().__init__(
            parent,
            width=width,
            height=height,
            background=surface,
            highlightthickness=0,
            borderwidth=0,
            cursor="hand2",
            takefocus=True,
        )
        self.variable = variable
        self.button_text = text
        self.button_font = font
        self.button_state = "normal"
        self.variable.trace_add("write", lambda *_args: self._draw())
        self.bind("<Button-1>", lambda _event: self.invoke())
        self.bind("<Return>", lambda _event: self.invoke())
        self.bind("<space>", lambda _event: self.invoke())
        self._draw()

    def _draw_box(self, left: int, top: int, fill: str, outline: str) -> None:
        """Draw a compact rounded square without relying on polygon smoothing."""
        size, radius = 20, 4
        right, bottom = left + size, top + size
        self.create_rectangle(
            left + radius,
            top,
            right - radius,
            bottom,
            fill=fill,
            outline=outline,
        )
        self.create_rectangle(
            left,
            top + radius,
            right,
            bottom - radius,
            fill=fill,
            outline=outline,
        )
        for x, y in (
            (left, top),
            (right - 2 * radius, top),
            (left, bottom - 2 * radius),
            (right - 2 * radius, bottom - 2 * radius),
        ):
            self.create_oval(
                x,
                y,
                x + 2 * radius,
                y + 2 * radius,
                fill=fill,
                outline=outline,
            )

    def _draw(self) -> None:
        self.delete("all")
        height = int(self.cget("height"))
        top = (height - 20) // 2
        disabled = self.button_state == "disabled"
        selected = bool(self.variable.get())
        fill = COLORS["red"] if selected and not disabled else COLORS["field"]
        outline = COLORS["red"] if selected and not disabled else COLORS["border"]
        self._draw_box(1, top, fill, outline)
        if selected:
            self.create_line(
                6,
                top + 10,
                10,
                top + 14,
                17,
                top + 6,
                fill="white" if not disabled else COLORS["muted"],
                width=2,
                capstyle="round",
                joinstyle="round",
            )
        self.create_text(
            30,
            height // 2,
            text=self.button_text,
            fill=COLORS["muted"] if disabled else COLORS["text"],
            font=self.button_font,
            anchor="w",
        )

    def invoke(self) -> None:
        """Toggle the value unless the control is disabled."""
        if self.button_state == "normal":
            self.variable.set(not self.variable.get())

    def configure(self, cnf=None, **kwargs):  # type: ignore[override]
        """Support the options needed by the main application."""
        options = dict(cnf or {})
        options.update(kwargs)
        for key, attribute in {
            "text": "button_text",
            "font": "button_font",
            "state": "button_state",
        }.items():
            if key in options:
                setattr(self, attribute, options.pop(key))
        if options:
            super().configure(options)
        self._draw()

    config = configure


class TimeLapseCaptureApp:
    """Responsive camera-style interface backed by worker threads."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.preferences = load_preferences()
        self.language_code = (
            self.preferences.get("language", "zh")
            if self.preferences.get("language") in TEXT
            else "zh"
        )
        self.language = tk.StringVar(
            value="中文" if self.language_code == "zh" else "English"
        )
        self.target_kind_code = self.preferences.get("target_kind", "display")
        self.target_kind = tk.StringVar()
        self.target_choice = tk.StringVar()
        self.duration = tk.StringVar(
            value=str(self.preferences.get("record_duration", "10"))
        )
        self.unit_code = self.preferences.get("duration_unit", "minutes")
        self.unit = tk.StringVar()
        self.interval = tk.StringVar(value=str(self.preferences.get("interval", "5")))
        self.interval_unit_code = self.preferences.get("interval_unit", "seconds")
        if self.interval_unit_code not in UNITS:
            self.interval_unit_code = "seconds"
        legacy_mode = (
            "images"
            if not self.preferences.get("generate_media", True)
            else ("gif" if self.preferences.get("output_format") == "gif" else "video")
        )
        self.mode = tk.StringVar(value=self.preferences.get("output_mode", legacy_mode))
        self.resolution_code = self.preferences.get("resolution", "auto")
        self.resolution = tk.StringVar()
        self.custom_resolution = tk.StringVar(
            value=self.preferences.get("custom_resolution", "1920x1080")
        )
        fmt = self.preferences.get("output_format", "mp4")
        self.video_format = tk.StringVar(value=fmt if fmt in VIDEO_FORMATS else "mp4")
        self.gif_preset = tk.StringVar(
            value=self.preferences.get("gif_compression", "balanced")
        )
        self.delete_frames = tk.BooleanVar(
            value=bool(self.preferences.get("delete_temporary_frames", True))
        )
        default_folder = Path.home() / "Videos"
        self.folder = tk.StringVar(
            value=self.preferences.get(
                "output_directory",
                str(default_folder if default_folder.exists() else Path.home()),
            )
        )
        self.file_prefix = tk.StringVar(
            value=self.preferences.get("output_name", "frame_tick")
        )
        self.status, self.estimate = tk.StringVar(), tk.StringVar()
        self.targets: dict[str, CaptureTarget] = {}
        self.session: Optional[CaptureSession] = None  # noqa: UP045
        self.settings: Optional[RecordingSettings] = None  # noqa: UP045
        self.export_events: queue.Queue[tuple[str, str]] = queue.Queue()
        self.exporting, self.tray_icon = False, None
        self.frames_destination: Optional[Path] = None  # noqa: UP045
        self.activity_state = "idle"
        self._configure_style()
        self._build()
        self._translate()
        self.refresh_targets()
        self._start_tray()
        self.root.protocol("WM_DELETE_WINDOW", self._hide)
        self.root.after(120, self._poll)

    def t(self, key: str, **values: object) -> str:
        return TEXT[self.language_code][key].format(**values)

    def _configure_style(self) -> None:
        self.root.geometry("1000x820")
        self.root.minsize(820, 700)
        self.root.configure(bg=COLORS["bg"])
        self.fonts = {
            "body": tkfont.Font(family="Microsoft YaHei UI", size=10),
            "bold": tkfont.Font(family="Microsoft YaHei UI", size=10, weight="bold"),
            "title": tkfont.Font(family="Microsoft YaHei UI", size=16, weight="bold"),
            "record": tkfont.Font(family="Microsoft YaHei UI", size=11, weight="bold"),
            "small": tkfont.Font(family="Microsoft YaHei UI", size=9),
        }
        style = ttk.Style(self.root)
        style.theme_use("clam")
        for name, bg in (("App.TFrame", COLORS["bg"]), ("Card.TFrame", COLORS["card"])):
            style.configure(name, background=bg)
        style.configure(
            "App.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["text"],
            font=self.fonts["body"],
        )
        style.configure(
            "Card.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["text"],
            font=self.fonts["body"],
        )
        style.configure(
            "Muted.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["muted"],
            font=self.fonts["small"],
        )
        style.configure(
            "Title.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["text"],
            font=self.fonts["title"],
        )
        style.configure(
            "Card.TCheckbutton",
            background=COLORS["bg"],
            foreground=COLORS["text"],
            font=self.fonts["body"],
        )
        style.configure(
            "TEntry",
            fieldbackground=COLORS["field"],
            foreground=COLORS["text"],
            insertcolor=COLORS["text"],
            bordercolor=COLORS["border"],
            padding=7,
            font=self.fonts["body"],
        )
        style.configure(
            "TCombobox",
            fieldbackground=COLORS["field"],
            background=COLORS["field"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["text"],
            bordercolor=COLORS["border"],
            padding=8,
            arrowsize=18,
            font=self.fonts["body"],
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", COLORS["field"])],
            foreground=[("readonly", COLORS["text"])],
        )
        style.configure(
            "Secondary.TButton",
            background=COLORS["field"],
            foreground=COLORS["text"],
            padding=(14, 8),
            font=self.fonts["bold"],
        )
        style.configure(
            "Horizontal.TProgressbar",
            background=COLORS["red"],
            troughcolor=COLORS["border"],
        )
        self.window_icon = ImageTk.PhotoImage(create_app_icon())
        self.root.iconphoto(True, self.window_icon)

    def _card(self, parent: tk.Widget) -> ttk.Frame:
        return ttk.Frame(parent, style="App.TFrame", padding=(8, 4))

    def _build(self) -> None:
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.content = ttk.Frame(self.root, style="App.TFrame", padding=(20, 16))
        self.content.grid(sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        header = ttk.Frame(self.content, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.columnconfigure(1, weight=1)
        self.logo = tk.Canvas(
            header, width=48, height=48, bg=COLORS["bg"], highlightthickness=0
        )
        self.logo.grid(row=0, column=0, padx=(0, 10))
        self.title_label = ttk.Label(header, style="Title.TLabel")
        self.title_label.grid(row=0, column=1, sticky="w")
        self.language_label = ttk.Label(header, style="App.TLabel")
        self.language_label.grid(row=0, column=2, padx=8)
        self.language_box = ttk.Combobox(
            header,
            textvariable=self.language,
            values=("中文", "English"),
            state="readonly",
            width=9,
        )
        self.language_box.grid(row=0, column=3)
        self.language_box.bind("<<ComboboxSelected>>", self._change_language)

        target = self._card(self.content)
        target.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        target.columnconfigure(2, weight=1)
        self.capture_label = ttk.Label(
            target, style="Card.TLabel", font=self.fonts["bold"]
        )
        self.capture_label.grid(row=0, column=0, padx=(0, 14))
        self.kind_box = ttk.Combobox(
            target, textvariable=self.target_kind, state="readonly", width=10
        )
        self.kind_box.grid(row=0, column=1, padx=(0, 8))
        self.kind_box.bind("<<ComboboxSelected>>", self._change_kind)
        self.target_box = ttk.Combobox(
            target, textvariable=self.target_choice, state="readonly"
        )
        self.target_box.grid(row=0, column=2, sticky="ew", padx=(0, 8))
        self.target_box.bind("<<ComboboxSelected>>", lambda _e: self._target_changed())
        self.refresh_button = RoundedButton(
            target,
            self.refresh_targets,
            width=94,
            text="",
            font=self.fonts["bold"],
            surface=COLORS["bg"],
        )
        self.refresh_button.grid(row=0, column=3)

        timing = ttk.Frame(self.content, style="App.TFrame")
        timing.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        timing.columnconfigure((0, 1), weight=1, uniform="time")
        duration_card = self._card(timing)
        duration_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        duration_card.columnconfigure(0, weight=1)
        duration_card.columnconfigure(1, minsize=146)
        self.duration_label = ttk.Label(
            duration_card, style="Card.TLabel", font=self.fonts["bold"]
        )
        self.duration_label.grid(row=0, column=0, columnspan=2, sticky="w")
        self.duration_entry = ttk.Entry(
            duration_card,
            textvariable=self.duration,
            font=self.fonts["bold"],
            width=8,
        )
        self.duration_entry.grid(
            row=1, column=0, sticky="ew", pady=(8, 0), padx=(0, 8), ipady=2
        )
        self.unit_box = ttk.Combobox(
            duration_card, textvariable=self.unit, state="readonly", width=9
        )
        self.unit_box.grid(row=1, column=1, sticky="ew", pady=(8, 0), ipady=2)
        self.unit_box.bind("<<ComboboxSelected>>", self._change_unit)
        interval_card = self._card(timing)
        interval_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        interval_card.columnconfigure(0, weight=1)
        interval_card.columnconfigure(1, minsize=146)
        self.interval_label = ttk.Label(
            interval_card, style="Card.TLabel", font=self.fonts["bold"]
        )
        self.interval_label.grid(row=0, column=0, columnspan=2, sticky="w")
        self.interval_entry = ttk.Entry(
            interval_card,
            textvariable=self.interval,
            font=self.fonts["bold"],
            width=8,
        )
        self.interval_entry.grid(
            row=1, column=0, sticky="ew", pady=(8, 0), padx=(0, 8), ipady=2
        )
        self.interval_unit = ttk.Combobox(
            interval_card,
            state="readonly",
            width=9,
        )
        self.interval_unit.grid(row=1, column=1, sticky="ew", pady=(8, 0), ipady=2)
        self.interval_unit.bind("<<ComboboxSelected>>", self._change_interval_unit)

        mode_card = self._card(self.content)
        mode_card.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        mode_card.columnconfigure(1, weight=1)
        self.mode_label = ttk.Label(
            mode_card, style="Card.TLabel", font=self.fonts["bold"]
        )
        self.mode_label.grid(row=0, column=0, padx=(0, 16))
        modes = ttk.Frame(mode_card, style="Card.TFrame")
        modes.grid(row=0, column=1, sticky="w")
        self.mode_buttons = {}
        for col, value in enumerate(("images", "video", "gif")):
            button = RoundedButton(
                modes,
                lambda v=value: self._set_mode(v),
                width=104,
                font=self.fonts["bold"],
                surface=COLORS["bg"],
            )
            button.grid(row=0, column=col, padx=(0, 5))
            self.mode_buttons[value] = button
        self.media_card = self._card(self.content)
        self.media_card.grid(row=4, column=0, sticky="ew", pady=(0, 12))
        self.media_card.columnconfigure(1, weight=1)
        self.media_label = ttk.Label(
            self.media_card, style="Card.TLabel", font=self.fonts["bold"]
        )
        self.media_label.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))
        self.resolution_label = ttk.Label(self.media_card, style="Card.TLabel")
        self.resolution_label.grid(row=1, column=0, padx=(0, 10))
        self.resolution_box = ttk.Combobox(
            self.media_card, textvariable=self.resolution, state="readonly", width=24
        )
        self.resolution_box.grid(row=1, column=1, sticky="ew", padx=(0, 14))
        self.resolution_box.bind("<<ComboboxSelected>>", self._change_resolution)
        self.custom_label = ttk.Label(self.media_card, style="Card.TLabel")
        self.custom_entry = ttk.Entry(
            self.media_card, textvariable=self.custom_resolution, width=16
        )
        self.format_label = ttk.Label(self.media_card, style="Card.TLabel")
        self.format_box = ttk.Combobox(
            self.media_card,
            textvariable=self.video_format,
            values=VIDEO_FORMATS,
            state="readonly",
            width=10,
        )
        self.format_box.bind("<<ComboboxSelected>>", lambda _e: self._estimate())
        self.compression_label = ttk.Label(self.media_card, style="Card.TLabel")
        self.compression_box = ttk.Combobox(self.media_card, state="readonly", width=14)
        self.compression_box.bind("<<ComboboxSelected>>", self._change_compression)
        self.delete_frames_check = LargeCheckButton(
            self.media_card,
            self.delete_frames,
            width=320,
            height=32,
            font=self.fonts["bold"],
            surface=COLORS["bg"],
        )
        self.delete_frames_check.grid(
            row=3, column=0, columnspan=4, sticky="w", pady=(10, 0)
        )
        self.estimate_label = ttk.Label(
            self.media_card, style="Muted.TLabel", textvariable=self.estimate
        )
        self.estimate_label.grid(row=4, column=0, columnspan=4, sticky="w", pady=(6, 0))

        output = self._card(self.content)
        output.grid(row=5, column=0, sticky="ew", pady=(0, 12))
        output.columnconfigure(1, weight=1)
        self.folder_label = ttk.Label(output, style="Card.TLabel")
        self.folder_label.grid(row=0, column=0, padx=(0, 12), pady=(0, 8))
        self.folder_entry = ttk.Entry(output, textvariable=self.folder)
        self.folder_entry.grid(row=0, column=1, sticky="ew", pady=(0, 8), padx=(0, 8))
        self.browse_button = RoundedButton(
            output,
            self._choose_folder,
            width=126,
            text="",
            font=self.fonts["bold"],
            surface=COLORS["bg"],
        )
        self.browse_button.grid(row=0, column=2, pady=(0, 8))
        self.name_label = ttk.Label(output, style="Card.TLabel")
        self.name_label.grid(row=1, column=0, padx=(0, 12))
        self.name_entry = ttk.Entry(output, textvariable=self.file_prefix)
        self.name_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8))

        footer = ttk.Frame(self.content, style="App.TFrame")
        footer.grid(row=6, column=0, sticky="ew")
        footer.columnconfigure((0, 2), weight=1)
        self.status_label = ttk.Label(
            footer,
            style="App.TLabel",
            textvariable=self.status,
            foreground=COLORS["muted"],
        )
        self.status_label.grid(row=0, column=0, sticky="w")
        self.record_button = RoundedButton(
            footer,
            self._toggle_recording,
            width=178,
            height=46,
            radius=10,
            font=self.fonts["record"],
            foreground="white",
            background=COLORS["red"],
            activebackground=COLORS["red_dark"],
            activeforeground="white",
            surface=COLORS["bg"],
        )
        self.record_button.grid(row=0, column=1, padx=16)
        self.progress = ttk.Progressbar(footer, mode="indeterminate", length=120)
        self.progress.grid(row=0, column=2, sticky="e")
        self.progress.grid_remove()
        for var in (self.duration, self.interval, self.custom_resolution):
            var.trace_add("write", lambda *_: self._estimate())

    def _translate(self) -> None:
        self.title_label.configure(text=self.t("title"))
        self.language_label.configure(text=self.t("language"))
        self.capture_label.configure(text=self.t("capture"))
        self.refresh_button.configure(text=self.t("refresh"))
        self.kind_box.configure(values=(self.t("display"), self.t("window")))
        self.target_kind.set(self.t(self.target_kind_code))
        self.duration_label.configure(text=self.t("duration"))
        self.interval_label.configure(text=self.t("interval"))
        self.interval_unit.configure(values=tuple(self.t(key) for key in UNITS))
        self.interval_unit.set(self.t(self.interval_unit_code))
        self.unit_box.configure(values=tuple(self.t(k) for k in UNITS))
        self.unit.set(self.t(self.unit_code))
        self.mode_label.configure(text=self.t("mode"))
        self.media_label.configure(text=self.t("media"))
        self.resolution_label.configure(text=self.t("resolution"))
        self.custom_label.configure(text=self.t("custom_size"))
        self.format_label.configure(text=self.t("format"))
        self.compression_label.configure(text=self.t("compression"))
        self.delete_frames_check.configure(text=self.t("delete_frames"))
        self.folder_label.configure(text=self.t("folder"))
        self.browse_button.configure(text=self.t("browse"))
        self.name_label.configure(text=self.t("file_name"))
        for value, button in self.mode_buttons.items():
            button.configure(text=self.t(value))
        self._resolution_values()
        self.compression_box.configure(values=tuple(self.t(k) for k in GIF_VALUES))
        self.compression_box.set(self.t(self.gif_preset.get()))
        self._update_mode()
        self._set_activity_state(self.activity_state)
        if not self.session and not self.exporting:
            self.status.set(self.t("ready"))

    def _change_language(self, _event=None) -> None:
        self.language_code = "zh" if self.language.get() == "中文" else "en"
        self._translate()
        self._update_tray()

    def _change_kind(self, _event=None) -> None:
        self.target_kind_code = (
            "display" if self.target_kind.get() == self.t("display") else "window"
        )
        self.refresh_targets()

    def _change_unit(self, _event=None) -> None:
        self.unit_code = next(
            (code for code in UNITS if self.unit.get() == self.t(code)), "seconds"
        )
        self._estimate()

    def _change_interval_unit(self, _event=None) -> None:
        """Store the selected capture-interval unit and refresh estimates."""
        self.interval_unit_code = next(
            (code for code in UNITS if self.interval_unit.get() == self.t(code)),
            "seconds",
        )
        self._estimate()

    def _change_resolution(self, _event=None) -> None:
        value = self.resolution.get()
        self.resolution_code = (
            "custom"
            if value == self.t("custom")
            else (
                "auto"
                if value.startswith(
                    self.t("auto_unknown").split("（")[0].split(" (")[0]
                )
                else value
            )
        )
        self._update_mode()
        self._estimate()

    def _change_compression(self, _event=None) -> None:
        self.gif_preset.set(
            next(
                (
                    code
                    for code in GIF_VALUES
                    if self.compression_box.get() == self.t(code)
                ),
                "balanced",
            )
        )
        self._estimate()

    def refresh_targets(self) -> None:
        try:
            items = (
                list_displays()
                if self.target_kind_code == "display"
                else list_windows()
            )
        except Exception as error:
            messagebox.showerror(self.t("capture_error"), str(error), parent=self.root)
            return
        self.targets = {item.label: item for item in items}
        self.target_box.configure(values=tuple(self.targets))
        if self.target_choice.get() not in self.targets:
            self.target_choice.set(next(iter(self.targets), ""))
        self.status.set(self.t("found", count=len(items)))
        self._target_changed()

    def _target_changed(self) -> None:
        self._resolution_values()
        self._estimate()

    def _auto_label(self) -> str:
        target = self.targets.get(self.target_choice.get())
        size = target_size(target) if target else None
        return (
            self.t("auto", size=f"{size[0]}x{size[1]}")
            if size
            else self.t("auto_unknown")
        )

    def _resolution_values(self) -> None:
        self.resolution_box.configure(
            values=(self._auto_label(), *RESOLUTIONS, self.t("custom"))
        )
        self.resolution.set(
            self._auto_label()
            if self.resolution_code == "auto"
            else self.t("custom")
            if self.resolution_code == "custom"
            else self.resolution_code
        )

    def _set_mode(self, value: str) -> None:
        self.mode.set(value)
        self._update_mode()
        self._estimate()

    def _update_mode(self) -> None:
        mode = self.mode.get()
        for value, button in self.mode_buttons.items():
            selected = value == mode
            button.configure(
                bg=COLORS["red"] if selected else COLORS["soft"],
                activebackground=COLORS["red"] if selected else COLORS["border"],
                fg="white" if selected else COLORS["muted"],
                activeforeground="white",
            )
        if mode == "images":
            self.media_card.grid_remove()
            self.name_label.grid_remove()
            self.name_entry.grid_remove()
            return
        self.media_card.grid()
        self.name_label.grid()
        self.name_entry.grid()
        if self.resolution_code == "custom":
            self.custom_label.grid(row=1, column=2, padx=(0, 8))
            self.custom_entry.grid(row=1, column=3)
        else:
            self.custom_label.grid_remove()
            self.custom_entry.grid_remove()
        if mode == "video":
            self.format_label.grid(row=2, column=0, pady=(10, 0))
            self.format_box.grid(row=2, column=1, sticky="w", pady=(10, 0))
            self.compression_label.grid_remove()
            self.compression_box.grid_remove()
        else:
            self.format_label.grid_remove()
            self.format_box.grid_remove()
            self.compression_label.grid(row=2, column=0, pady=(10, 0))
            self.compression_box.grid(row=2, column=1, sticky="w", pady=(10, 0))

    def _resolved_size(self, target: CaptureTarget) -> tuple[int, int]:
        if self.resolution_code == "auto":
            size = target_size(target)
            if not size:
                raise ValueError(self.t("target_size_error"))
            return size
        value = (
            self.custom_resolution.get()
            if self.resolution_code == "custom"
            else self.resolution_code
        )
        match = re.fullmatch(r"\s*(\d{2,5})\s*[xX×]\s*(\d{2,5})\s*", value)
        if not match:
            raise ValueError(self.t("valid_resolution"))
        size = tuple(map(int, match.groups()))
        if size[0] > 7680 or size[1] > 4320:
            raise ValueError(self.t("valid_resolution"))
        return size

    def _output_stem(self) -> str:
        """Normalize accidental media extensions in the file-prefix field."""
        return normalize_output_stem(self.file_prefix.get())

    def _read_settings(self) -> RecordingSettings:
        try:
            interval = float(self.interval.get()) * UNITS[self.interval_unit_code]
        except ValueError as error:
            raise ValueError(self.t("valid_interval")) from error
        if interval < 0.2:
            raise ValueError(self.t("valid_interval"))
        try:
            duration = float(self.duration.get()) * UNITS[self.unit_code]
        except ValueError as error:
            raise ValueError(self.t("valid_duration")) from error
        if not 0.2 <= duration <= 86400:
            raise ValueError(self.t("valid_duration"))
        folder = Path(self.folder.get()).expanduser()
        if not folder.is_dir():
            raise ValueError(self.t("valid_folder"))
        target = self.targets.get(self.target_choice.get())
        if not target:
            raise ValueError(self.t("select_target"))
        if self.mode.get() == "images":
            return RecordingSettings(interval, duration, folder, target, None)
        size, fmt, stem = (
            self._resolved_size(target),
            ("gif" if self.mode.get() == "gif" else self.video_format.get()),
            self._output_stem(),
        )
        if fmt != "gif" and (size[0] % 2 or size[1] % 2):
            raise ValueError(self.t("valid_even"))
        if not stem or any(c in stem for c in '<>:"/\\|?*'):
            raise ValueError(self.t("valid_name"))
        self.file_prefix.set(stem)
        return RecordingSettings(
            interval,
            duration,
            folder,
            target,
            MediaSettings(size, fmt, stem, GIF_VALUES[self.gif_preset.get()]),
        )

    def _toggle_recording(self) -> None:
        if self.session and self.session.running:
            self.session.stop()
            self.status.set(self.t("stopping"))
            return
        if self.exporting:
            return
        try:
            self.settings = self._read_settings()
        except ValueError as error:
            self._show()
            messagebox.showerror(self.t("settings_error"), str(error), parent=self.root)
            return
        self.session = CaptureSession(
            self.settings.target,
            self.settings.interval_seconds,
            self.settings.capture_duration_seconds,
            self.settings.image_directory if not self.settings.media else None,
        )
        self.session.start()
        self._controls(False)
        self._set_activity_state("recording")
        self.status.set(self.t("recording", count=0))
        self._save()

    def _controls(self, enabled: bool) -> None:
        normal, readonly = (
            ("normal", "readonly") if enabled else ("disabled", "disabled")
        )
        for widget in (
            self.language_box,
            self.kind_box,
            self.target_box,
            self.unit_box,
            self.interval_unit,
            self.resolution_box,
            self.format_box,
            self.compression_box,
        ):
            widget.configure(state=readonly)
        for widget in (
            self.refresh_button,
            self.duration_entry,
            self.interval_entry,
            self.custom_entry,
            self.folder_entry,
            self.browse_button,
            self.name_entry,
            self.delete_frames_check,
        ):
            widget.configure(state=normal)
        for button in self.mode_buttons.values():
            button.configure(state=normal)

    def _set_activity_state(self, state: str) -> None:
        """Synchronize window, logo, and tray visuals for the current activity."""
        if state not in {"idle", "recording", "processing"}:
            state = "idle"
        self.activity_state = state
        active = state == "recording"
        title_key = {
            "idle": "title",
            "recording": "title_recording",
            "processing": "title_processing",
        }[state]
        activity_title = self.t(title_key)
        self.root.title(activity_title)
        self.window_icon = ImageTk.PhotoImage(create_app_icon(state))
        self.root.iconphoto(True, self.window_icon)
        self.record_button.configure(
            text=("■  " if active else "●  ") + self.t("stop" if active else "record"),
            bg=COLORS["red_dark"] if active else COLORS["red"],
            activebackground=COLORS["red"],
        )
        self.logo.delete("all")
        for points in (
            (7, 18, 7, 7, 18, 7),
            (30, 7, 41, 7, 41, 18),
            (7, 30, 7, 41, 18, 41),
            (30, 41, 41, 41, 41, 30),
        ):
            self.logo.create_line(
                *points,
                fill=COLORS["text"],
                width=3,
                capstyle="round",
                joinstyle="round",
            )
        self.logo.create_oval(
            18,
            18,
            30,
            30,
            fill={
                "idle": COLORS["muted"],
                "recording": COLORS["red"],
                "processing": COLORS["yellow"],
            }[state],
            outline="",
        )
        if self.tray_icon:
            self.tray_icon.icon = create_app_icon(state)
            self.tray_icon.title = activity_title
            self._update_tray()

    def _poll(self) -> None:
        if self.session:
            while True:
                try:
                    event = self.session.events.get_nowait()
                except queue.Empty:
                    break
                self._capture_event(event)
        while True:
            try:
                kind, value = self.export_events.get_nowait()
            except queue.Empty:
                break
            if kind == "progress":
                self.status.set(self.t("exporting", progress=value))
                continue
            self.exporting = False
            self.progress.stop()
            self.progress.grid_remove()
            self._controls(True)
            self._set_activity_state("idle")
            if kind == "done":
                kept_frames = self._cleanup(delete_frames=self.delete_frames.get())
                self.status.set(
                    self.t("frames_kept", path=value, folder=kept_frames)
                    if kept_frames
                    else self.t("saved_media", path=value)
                )
                self._notify_completion(
                    "notification_processing_done", str(Path(value).parent)
                )
            else:
                self.status.set(self.t("export_error"))
                self._show()
                messagebox.showerror(self.t("export_error"), value, parent=self.root)
        self.root.after(120, self._poll)

    def _capture_event(self, event: CaptureEvent) -> None:
        if event.kind == "frame":
            self.status.set(self.t("recording", count=event.frame_count or 0))
        elif event.kind == "error":
            self._show()
            messagebox.showerror(
                self.t("capture_error"), event.message, parent=self.root
            )
        elif event.kind == "stopped":
            if self.session and self.session.saves_images_directly:
                self._set_activity_state("idle")
                self.status.set(self.t("saved_images", count=event.frame_count or 0))
                if self.settings:
                    self._notify_completion(
                        "notification_recording_done",
                        str(self.settings.image_directory),
                    )
                self.session = None
                self.settings = None
                self._controls(True)
            elif event.frame_count:
                self._export()
            else:
                self._set_activity_state("idle")
                self._cleanup()
                self._controls(True)

    def _export(self) -> None:
        if not self.session or not self.settings or not self.settings.media:
            return
        frames, media = self.session.frame_paths(), self.settings.media
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        destination = (
            self.settings.image_directory
            / f"{media.output_stem}_{timestamp}{EXTENSIONS[media.output_format]}"
        )
        self.frames_destination = (
            self.settings.image_directory / f"{media.output_stem}_{timestamp}_frames"
        )
        self.exporting = True
        self._set_activity_state("processing")
        self.progress.grid()
        self.progress.start(12)
        self.status.set(self.t("exporting", progress=""))
        threading.Thread(
            target=self._export_worker, args=(frames, destination, media), daemon=True
        ).start()

    def _export_worker(
        self, frames: list[Path], destination: Path, media: MediaSettings
    ) -> None:
        try:
            export_media(
                frames,
                destination,
                len(frames),
                PLAYBACK_FRAMES_PER_SECOND,
                media.output_size,
                media.gif_compression,
                lambda n, total: self.export_events.put(("progress", f"{n}/{total}")),
            )
        except Exception as error:
            self.export_events.put(("error", f"{type(error).__name__}: {error}"))
        else:
            self.export_events.put(("done", str(destination)))

    def _cleanup(self, *, delete_frames: bool = True) -> Path | None:
        """Discard temporary frames or move them next to the generated media."""
        kept_frames = None
        if self.session and not self.session.running:
            if delete_frames or self.frames_destination is None:
                with contextlib.suppress(OSError, RuntimeError):
                    self.session.discard()
            else:
                destination = self._available_frames_folder(self.frames_destination)
                with contextlib.suppress(OSError, RuntimeError):
                    kept_frames = self.session.preserve_frames(destination)
        self.session = None
        self.settings = None
        self.frames_destination = None
        return kept_frames

    @staticmethod
    def _available_frames_folder(destination: Path) -> Path:
        """Choose a non-conflicting frame-folder name beside the media file."""
        candidate, number = destination, 2
        while candidate.exists():
            candidate = destination.with_name(f"{destination.name}-{number}")
            number += 1
        return candidate

    def _estimate(self) -> None:
        if not hasattr(self, "estimate_label") or self.mode.get() == "images":
            return
        try:
            interval, duration = (
                float(self.interval.get()) * UNITS[self.interval_unit_code],
                float(self.duration.get()) * UNITS[self.unit_code],
            )
            target = self.targets.get(self.target_choice.get())
            if interval < 0.2 or duration < 0.2 or not target:
                raise ValueError
            width, height = self._resolved_size(target)
        except (ValueError, TypeError):
            self.estimate.set(self.t("estimate_unknown"))
            return
        frames, seconds = (
            max(1, math.ceil(duration / interval)),
            max(1, math.ceil(duration / interval)) / PLAYBACK_FRAMES_PER_SECOND,
        )
        if self.mode.get() == "gif":
            size = (
                width
                * height
                * frames
                * {"high": 0.14, "balanced": 0.08, "small": 0.045}[
                    self.gif_preset.get()
                ]
            )
        else:
            size = (
                {"mp4": 5.5, "webm": 4.0, "avi": 10.0}[self.video_format.get()]
                * width
                * height
                / (1920 * 1080)
                * 1e6
                * seconds
                / 8
            )
        pretty = (
            f"{size / 1024:.0f} KB" if size < 1024**2 else f"{size / 1024**2:.1f} MB"
        )
        self.estimate.set(
            self.t("estimate", frames=frames, duration=f"{seconds:.1f}", size=pretty)
        )

    def _choose_folder(self) -> None:
        value = filedialog.askdirectory(parent=self.root, initialdir=self.folder.get())
        if value:
            self.folder.set(value)

    def _save(self) -> None:
        save_preferences(
            {
                "language": self.language_code,
                "target_kind": self.target_kind_code,
                "record_duration": self.duration.get(),
                "duration_unit": self.unit_code,
                "interval": self.interval.get(),
                "interval_unit": self.interval_unit_code,
                "output_mode": self.mode.get(),
                "resolution": self.resolution_code,
                "custom_resolution": self.custom_resolution.get(),
                "output_format": self.video_format.get(),
                "gif_compression": self.gif_preset.get(),
                "delete_temporary_frames": self.delete_frames.get(),
                "output_directory": self.folder.get(),
                "output_name": self.file_prefix.get(),
            }
        )

    def _tray_menu(self):
        import pystray

        return pystray.Menu(
            pystray.MenuItem(
                lambda _i: self.t("tray_show"),
                lambda _icon, _item: self.root.after(0, self._show),
                default=True,
            ),
            pystray.MenuItem(
                lambda _i: self.t(
                    "tray_stop"
                    if self.session and self.session.running
                    else "tray_start"
                ),
                lambda _icon, _item: self.root.after(0, self._toggle_recording),
                enabled=lambda _i: not self.exporting,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                lambda _i: self.t("tray_exit"),
                lambda _icon, _item: self.root.after(0, self._exit),
            ),
        )

    def _start_tray(self) -> None:
        try:
            import pystray

            self.tray_icon = pystray.Icon(
                "FrameTick",
                create_app_icon(self.activity_state),
                self.t("title"),
                self._tray_menu(),
            )
            self.tray_icon.run_detached()
        except Exception:
            self.tray_icon = None

    def _update_tray(self) -> None:
        if self.tray_icon:
            with contextlib.suppress(Exception):
                self.tray_icon.menu = self._tray_menu()
                self.tray_icon.update_menu()

    def _notify_completion(self, title_key: str, folder: str) -> None:
        """Show a native Windows tray notification without adding a service."""
        if self.tray_icon:
            with contextlib.suppress(Exception):
                self.tray_icon.notify(
                    self.t("notification_folder", folder=folder), self.t(title_key)
                )

    def _show(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _hide(self) -> None:
        if self.tray_icon:
            self.root.withdraw()
            self.tray_icon.notify(self.t("tray_hint"), self.root.title())
        else:
            self._exit()

    def _exit(self) -> None:
        if self.session and self.session.running:
            self.session.stop()
        self._save()
        if self.tray_icon:
            with contextlib.suppress(Exception):
                self.tray_icon.stop()
        self.root.destroy()


def enable_dpi_awareness() -> None:
    """Enable crisp native scaling on high-DPI Windows displays."""
    if not hasattr(ctypes, "windll"):
        return
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        with contextlib.suppress(AttributeError, OSError):
            ctypes.windll.shcore.SetProcessDpiAwareness(2)


def main() -> None:
    enable_dpi_awareness()
    root = tk.Tk()
    TimeLapseCaptureApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
