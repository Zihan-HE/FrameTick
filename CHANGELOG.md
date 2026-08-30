# Changelog / 更新记录

## 0.5.6 - 2026-08-30

- Replaced the small native temporary-frame checkbox with a prominent 20-pixel
  custom checkbox and bold label.
- Increased the initial window size and minimum height so the recording action
  remains visible when first opening media settings.

## 0.5.5 - 2026-08-30

- Aligned the duration and interval entry/drop-down pairs to the same grid,
  including their vertical position and unit-field width.
- Increased the recording button's exact circular corner radius for a smoother,
  more intentional camera-control shape.

## 0.5.4 - 2026-08-30

- Added a default-on option to delete temporary media frames after export.
  When disabled, frames are moved from the system temporary directory into a
  dated `_frames` folder beside the generated media.
- Normalized accidental `.gif`, `.mp4`, `.webm`, and `.avi` suffixes entered
  in the file-prefix field, preventing doubled extensions.
- Used a conservative GIF frame-disposal mode for better animated-GIF
  compatibility.

## 0.5.3 - 2026-08-30

- Added a three-state application and system-tray indicator: gray while idle,
  red while recording, and yellow while creating video or GIF output.
- Added localized window and tray titles for Recording/录制中 and
  Processing/处理中.
- Kept the red recording state visible until capture has fully stopped, then
  transitioned directly to yellow when media processing starts.
- Added localized native Windows completion notifications that show the output
  folder after image capture or video/GIF processing.

## 0.5.2 - 2026-08-30

- Added seconds, minutes, and hours to the capture-interval selector.
- Persisted the selected interval unit and converted it safely to seconds internally.

## 0.5.1 - 2026-08-29

- Replaced distorted smoothed polygons with exact symmetric rounded rectangles.
- Reduced the button corner treatment to a restrained six-pixel radius.

## 0.5.0 - 2026-08-29

- Reworked the layout as a compact native Windows form instead of nested cards.
- Matched duration and interval fields, unit selectors, typography, and heights.
- Returned numeric fields to the normal body size with bold emphasis only.
- Added restrained rounded action buttons and larger drop-down arrows.
- Kept resizing predictable: only long fields expand while controls stay fixed.

## 0.4.1 - 2026-08-29

- Restored a clean light interface with restrained typography and spacing.
- Removed the decorative subtitle and redundant timing descriptions.
- Replaced partial dynamic font scaling with stable, consistent control sizing.
- Hid the media progress indicator unless an export is actually running.

## 0.4.0 - 2026-08-29

- Rebuilt the interface with a clean, camera-inspired dark design.
- Added responsive font scaling when the window is enlarged.
- Replaced the media checkbox with Images, Video, and GIF modes.
- Added mode-specific settings and automatic export after recording.
- Added current-target dimensions to the Auto resolution option.
- Added a system-tray icon whose center turns red while recording.
- Added application icons and renamed the Chinese product name to “拾刻”.

## 0.3.0 - 2026-08-29

- Added Chinese and English interfaces, real recording duration units, resolution presets, and output estimates.
- Made the main window resizable and added the first recording-state logo.

## 0.2.1 - 2026-08-29

- Fixed the packaged executable entry point and relative-import startup failure.

## 0.2.0 - 2026-08-29

- Added timestamp-named PNG output, optional media creation, and GIF compression presets.

## 0.1.0 - 2026-08-29

- Initial monitor/window capture, low-overhead scheduling, and MP4/WebM/AVI/GIF export.
