"""Run the immutable predecessor runner under a new allocation identity."""

from __future__ import annotations

import sys
from pathlib import Path

V1 = Path(__file__).resolve().parents[1] / "needle_role_skill_lifecycle_4916_v2"
sys.path.insert(0, str(V1))

import run_experiment as frozen_runner  # noqa: E402

frozen_runner.ALLOCATION = "needle-role-skill-lifecycle-4916-v3-20260928-02"


if __name__ == "__main__":
    raise SystemExit(frozen_runner.main())
