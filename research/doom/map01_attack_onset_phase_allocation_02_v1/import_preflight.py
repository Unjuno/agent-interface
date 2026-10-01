"""Import-only environment gate. Does not initialize ViZDoom or run a session."""
from __future__ import annotations

import importlib
import json
import os
import platform
import sys
from importlib.metadata import version
from pathlib import Path

source = Path(os.environ["MAP01_SOURCE_ROOT"]).resolve()
v12 = Path(os.environ["MAP01_V12_ROOT"]).resolve()
experiment = Path(os.environ["MAP01_EXPERIMENT_ROOT"]).resolve()
for path in (
    source / "research/live_control",
    source / "research/observation_gating",
    source / "research/doom",
    v12,
    experiment,
):
    sys.path.insert(0, str(path))
# session_entry.py performs this final insertion immediately before importing
# the runtime backend; mirror that exact precedence to avoid a false circular
# import through the legacy research/doom/session_v7.py module of the same name.
sys.path.insert(0, str(source / "research/live_control"))

assert platform.machine() == "x86_64", platform.machine()
assert sys.version_info[:3] == (3, 13, 5), sys.version
expected = {
    "vizdoom": "1.3.0",
    "numpy": "2.5.3",
    "pillow": "12.3.0",
    "openpyxl": "3.1.5",
    "python-xlib": "0.33",
}
actual = {name: version(name) for name in expected}
assert actual == expected, actual

from Xlib.display import Display

display = Display()
display_name = display.get_display_name()
display.close()

backend = importlib.import_module("doom_retained_input_backend_v3")
owner = importlib.import_module("map01_v12_transition_owner").InputOwner
backend.InputOwner = owner
importlib.import_module("session_map01_v13")

print(json.dumps({
    "decision": "IMPORT_ONLY_READY",
    "science_sessions": 0,
    "physical_inputs": 0,
    "x_server_display": display_name,
    "platform": platform.machine(),
    "python": platform.python_version(),
    "packages": actual,
    "session_entry_graph": "imported_without calling main()",
}, sort_keys=True))
