#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path


PRODUCTION_SCRIPT = Path("/Users/jinbo/AutomationCenter/scripts/transcribe_media_batch.py")


def main() -> None:
    if not PRODUCTION_SCRIPT.is_file():
        raise SystemExit(f"Production ASR script not found: {PRODUCTION_SCRIPT}")
    os.execv(sys.executable, [sys.executable, str(PRODUCTION_SCRIPT), *sys.argv[1:]])


if __name__ == "__main__":
    main()
