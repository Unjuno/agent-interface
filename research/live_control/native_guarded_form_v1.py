"""Compatibility entry point for the shared scoped X11 runtime."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime.guarded_x11_v1.form import fill_and_submit
