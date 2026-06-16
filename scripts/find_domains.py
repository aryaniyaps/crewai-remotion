#!/usr/bin/env python3
"""CLI entrypoint for the brandable domain finder."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from domain_finder.run import main

if __name__ == "__main__":
    raise SystemExit(main())
