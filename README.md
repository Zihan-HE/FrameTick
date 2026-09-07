# FrameTick / 拾刻

轻量、离线的 Windows 定时截屏与延时影像工具。

FrameTick is a lightweight, offline Windows utility for scheduled screenshots and time-lapse media.

## 中文

当前版本：**v0.5.8**。[下载 Windows 免安装版](https://github.com/Zihan-HE/FrameTick/releases/latest)。
使用 v0.5.6 遇到视频生成失败，请下载新版并完整解压到新文件夹。

### 功能

- 选择任意显示器，支持多显示器和负坐标布局。
- 选择一个可见的应用窗口，并在窗口移动后继续跟踪拍摄。
- 自定义录制时长与截图间隔，两者均支持秒、分钟和小时。
- 三种输出模式：按时间命名的 PNG 图片、视频、GIF。
- 视频支持 MP4、WebM 和 AVI；GIF 提供常用压缩档位。
- 自动读取拍摄目标分辨率，也可选择常见分辨率或自定义尺寸。
- 录制前估算帧数、成片时长和文件大小。
- 视频/GIF 在录制完成后自动生成；默认删除临时帧，也可选择将其保留到输出目录的 `_frames` 文件夹。
- 图片录制或视频/GIF 处理完成后发送 Windows 通知并显示保存位置。
- 可隐藏到 Windows 系统托盘：待机为灰色、录制为红色、生成视频/GIF
  或压缩时为黄色，并显示对应的中英文状态标题。
- 中英文界面，默认中文。
- 完全本地处理，不联网、不上传、不收集遥测数据。

### 普通用户

下载 Release 中的 Windows 压缩包，完整解压后双击 `FrameTick.exe`。不要只复制 EXE；同目录的 `_internal` 文件夹是运行所需组件。支持 64 位 Windows 10/11，无需安装 Python。

### 开发与运行

需要 Windows 10/11 和 Python 3.9 或更高版本：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
frame-tick
```

### 构建免安装版

```powershell
.\scripts\build-exe.ps1
```

构建结果位于 `dist\FrameTick\FrameTick.exe`。发布时应分发整个 `dist\FrameTick` 文件夹。

### 开发检查

```powershell
python -m pytest
python -m ruff check .
```

## English

Current release: **v0.5.8**. [Download for Windows](https://github.com/Zihan-HE/FrameTick/releases/latest).
If video export fails in v0.5.6, download the latest build and extract it into a new folder.

### Features

- Capture any connected display or a selected visible application window.
- Configure recording duration and capture interval in seconds, minutes, or hours.
- Choose timestamped PNG images, MP4/WebM/AVI video, or GIF output.
- Use the target's native resolution, a common preset, or a custom size.
- Estimate frame count, media duration, and output size before recording.
- Export video/GIF automatically; delete temporary frames by default or keep
  them in a `_frames` folder beside the output.
- Show a Windows notification with the destination folder after capture or
  media processing finishes.
- Keep the app in the Windows system tray with gray idle, red recording, and
  yellow media-processing indicators plus localized state titles.
- Switch between Chinese and English.
- Work completely offline with no uploads, telemetry, or network requests.

### Run and build

Follow the Chinese development commands above. The packaged build supports 64-bit Windows 10/11 and does not require Python on the destination computer.

## Project documentation

- [CHANGELOG.md](CHANGELOG.md): release-by-release changes.
- [DEVELOPMENT.md](DEVELOPMENT.md): architecture, design decisions, and development history.
- [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md): bundled dependency notices.

## Privacy

Screen capture reads pixels from the selected display or window. Screenshots, temporary frames, and exported media remain on the local computer.

## License

Released under the [MIT License](LICENSE). Third-party components retain their own licenses.
