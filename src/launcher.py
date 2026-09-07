"""Standalone application entry point used by the Windows bundle."""

import sys
from pathlib import Path

from time_lapse_capture.app import main
from time_lapse_capture.diagnostics import check_exports

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--check-exports":
        raise SystemExit(check_exports(Path(sys.argv[2])))
    main()
