"""Compatibility entry point for the shared bounded compiled GUI runtime."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime.core_v1.compiled_gui import run, validate, YIELD_REASONS
