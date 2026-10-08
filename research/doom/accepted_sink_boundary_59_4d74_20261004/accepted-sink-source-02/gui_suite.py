"""Compatibility shim for the retained flat-import GUI route.

The historical session imports gui_suite from research/live_control while the
canonical implementation is maintained under research/observation_gating.
Install that directory on sys.path before importing so its legacy exact_gate
import remains resolvable. No GUI is started and no authority is granted by
this module import.
"""
from pathlib import Path
import sys

_GATE_ROOT = Path(__file__).resolve().parents[1] / "observation_gating"
if str(_GATE_ROOT) not in sys.path:
    sys.path.insert(0, str(_GATE_ROOT))
from research.observation_gating.gui_suite import *
