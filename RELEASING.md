# Releasing FrameTick

This project publishes source code through GitHub and portable Windows builds
through GitHub Releases. Do not commit packaged builds, virtual environments,
or generated screenshots to the repository.

## Release checklist

1. Update the version in `pyproject.toml`, `src/time_lapse_capture/__init__.py`,
   and `CHANGELOG.md`.
2. Run `python -m pytest` and `python -m ruff check .`.
3. Run `./scripts/build-exe.ps1` in PowerShell.
4. Test `dist/FrameTick/FrameTick.exe` on Windows.
   Run `FrameTick.exe --check-exports <new-output-directory>` and verify that
   `report.json` has `"ok": true`. This uses synthetic portrait frames to test
   single-frame and multi-frame MP4, WebM, AVI, and GIF in the frozen executable.
5. Zip the complete `dist/FrameTick` directory as
   `FrameTick-vX.Y.Z-Windows-x64.zip`.
6. Create a GitHub Release with tag `vX.Y.Z`, attach that zip, and summarize the
   corresponding `CHANGELOG.md` section.

## User-facing release note

Chinese: 完整解压压缩包后运行 `FrameTick.exe`。请不要只复制 EXE，`_internal`
文件夹也是运行所需内容。

English: Extract the complete archive, then run `FrameTick.exe`. Do not copy
only the EXE: the `_internal` folder is required.
