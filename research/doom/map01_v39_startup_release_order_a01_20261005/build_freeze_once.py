"""Guarded entry point for the historical freeze generator."""
from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    package = Path(__file__).resolve().parent
    freeze = package / "FREEZE.json"
    if freeze.exists():
        raise SystemExit(f"refusing to overwrite existing frozen evidence: {freeze}")
    runpy.run_path(str(package / "build_freeze.py"), run_name="__main__")


if __name__ == "__main__":
    main()
