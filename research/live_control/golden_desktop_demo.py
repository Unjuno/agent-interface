"""Current-tree import shim for the retained golden route source.

The implementation remains frozen under the historical source bundle.  This
module executes that source with the current-tree filename so its relative
ROOT/RESEARCH paths resolve against the current repository.
"""

from __future__ import annotations

from pathlib import Path

_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "analysis"
    / "full_golden_ipc_2705_v2"
    / "historical_route_source"
    / "golden_desktop_demo.py"
)
_CODE = compile(_SOURCE.read_text(encoding="utf-8"), str(Path(__file__).resolve()), "exec")
_GLOBALS = globals()
_GLOBALS["__file__"] = str(Path(__file__).resolve().parents[2] / "runtime" / "golden_desktop_demo.py")
_GLOBALS["__package__"] = ""
exec(_CODE, _GLOBALS, _GLOBALS)
