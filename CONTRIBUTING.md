# Contributing to FrameTick

Thank you for helping improve FrameTick.

## Development setup

Use Windows 10/11 with Python 3.9 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Before submitting a change

```powershell
python -m ruff format src tests scripts
python -m ruff check src tests scripts
python -m pytest
```

- Keep code and code comments in English.
- Keep UI strings in both Chinese and English.
- Add or update tests for behavior changes.
- Keep capture work off the Tk main thread.
- Avoid adding network access, telemetry, or unnecessary background polling.
- Update `CHANGELOG.md` for user-visible changes.

## Pull requests

Describe the problem, the chosen solution, manual verification, and any effect on performance, privacy, packaging, or compatibility. Keep unrelated changes in separate pull requests.
