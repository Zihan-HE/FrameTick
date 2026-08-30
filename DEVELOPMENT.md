# Development record / 开发过程记录

## Project goal

FrameTick started as a small Windows utility for low-overhead periodic screen capture. The product deliberately separates real-world recording duration from capture interval and supports both archival screenshots and generated time-lapse media.

## Architecture

- `src/time_lapse_capture/app.py`: Tkinter interface, localization, validation, tray behavior, and worker coordination.
- `src/time_lapse_capture/capture.py`: monotonic low-overhead capture scheduler backed by MSS.
- `src/time_lapse_capture/targets.py`: Windows display and top-level-window discovery.
- `src/time_lapse_capture/exporter.py`: disk-backed frame processing and MP4/WebM/AVI/GIF export.
- `src/time_lapse_capture/models.py`: immutable capture and media settings.
- `src/time_lapse_capture/config.py`: small atomic JSON preference store.
- `src/launcher.py`: stable PyInstaller entry point.
- `tests/`: capture scheduling, configuration, frame planning, fitting, and export tests.

## Design decisions

- Frames are written to disk instead of accumulated in memory, keeping long recordings predictable.
- Scheduling uses a monotonic clock so system clock changes do not alter capture cadence.
- Images mode writes timestamped PNG files directly to the selected folder.
- Video and GIF modes use temporary frames and clean them after a successful automatic export.
- Playback uses an internal fixed cadence; users configure meaningful capture intervals rather than FPS.
- All processing is local. The application has no network or telemetry code.
- Display and window selection are refreshed on demand to avoid constant background polling.

## Iteration history

- `0.1.0`: first monitor/window capture and MP4/WebM/AVI/GIF export.
- `0.2.0`: timestamped PNG mode and GIF compression presets.
- `0.2.1`: corrected the PyInstaller launcher and relative-import crash.
- `0.3.0`: bilingual interface, duration units, resolution presets, and output estimates.
- `0.4.0`: output modes, automatic export, app icon, and system tray.
- `0.4.1`: restored a stable light interface and removed partial font scaling.
- `0.5.0`: compact Windows form layout and aligned timing controls.
- `0.5.1`: corrected custom button corner geometry.
- `0.5.2`: seconds/minutes/hours support for capture intervals.
- `0.5.3`: synchronized gray/red/yellow window and tray activity states with
  localized recording and processing titles, plus native completion notices.
- `0.5.4`: added user-controlled temporary-frame retention, normalized output
  suffixes, and strengthened animated GIF export coverage.

See `CHANGELOG.md` for the detailed release notes.

## Quality workflow

Every release should run:

```powershell
python -m ruff format src tests scripts
python -m ruff check src tests scripts
python -m pytest
.\scripts\build-exe.ps1
```

After packaging, launch `dist\FrameTick\FrameTick.exe` on Windows and verify display discovery, all three output modes, localization, tray behavior, and a short real capture.

## Future work

- Add signed installers and code signing when distribution volume justifies it.
- Add automated Windows release builds through GitHub Actions.
- Expand tests for tray lifecycle and window-close behavior.
- Consider region capture without increasing idle resource usage.
