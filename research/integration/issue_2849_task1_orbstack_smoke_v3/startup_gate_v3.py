"""No-model dependency + GUI startup gate for the task-1 successor image."""
from __future__ import annotations

import os
from pathlib import Path
import runpy
import sys

REPO = Path(os.environ["ISSUE_2849_REPO"]).resolve()
V2 = REPO / "research/integration/issue_2849_task1_orbstack_smoke_v2"
for root in (V2, REPO, REPO / "research/live_control",
             REPO / "research/observation_tiles",
             REPO / "research/observation_gating",
             REPO / "research/real_apps_v1", REPO / "runtime"):
    sys.path.insert(0, str(root))

# Exercise the exact import chain which stopped preregistration 5751505437,
# while keeping the host-model callback entirely dormant.
from run_integrated_efficiency_live_v1 import run_task
from docker_model_call_backend_v1 import call as selected_docker_call
from runtime.docker_schema_preflight_v1 import validate_model_response
from referencing import Registry

if not callable(run_task) or not callable(selected_docker_call) or not Registry:
    raise RuntimeError("STOP_SUCCESSOR_IMPORT_GATE")

# Then run the already-frozen, read-only task-runtime startup gate. It starts
# Chromium and takes one observation only; it never calls the model or submits.
Path(os.environ["ISSUE_2849_STARTUP_DIR"]).rmdir()
runpy.run_path(str(V2 / "startup_check.py"), run_name="__main__")
