"""Run the v2 frozen task harness with v3 image and seed 284903."""
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

if os.environ.get("ISSUE_2849_SEED") != "284903":
    raise RuntimeError("STOP_SUCCESSOR_SEED_MISMATCH")
runpy.run_path(str(V2 / "run_task1_smoke.py"), run_name="__main__")
