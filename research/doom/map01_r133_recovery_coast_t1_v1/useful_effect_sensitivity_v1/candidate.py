#!/usr/bin/env python3
"""One-shot finite sensitivity sweep using the unchanged frozen comparator."""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FREEZE = HERE / "FREEZE.json"
FIXTURE = HERE / "FIXTURE.json"
OUT = HERE / "results" / "sensitivity-01"
SOURCE = ROOT / "research/doom/map01_r133_recovery_coast_t1_v1/decision_rule_construction_v2/adjudicator.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_comparator():
    spec = importlib.util.spec_from_file_location("frozen_adjudicator", SOURCE)
    if spec is None or spec.loader is None:
        raise SystemExit("STOP_SOURCE_LOAD")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if OUT.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    pinned = freeze["pinned_sha256"]
    paths = {"PLAN.md": HERE / "PLAN.md", "FIXTURE.json": FIXTURE,
             "candidate.py": Path(__file__), "audit.py": HERE / "audit.py",
             "adjudicator.py": SOURCE}
    for name, path in paths.items():
        if sha(path) != pinned[name]:
            raise SystemExit("STOP_SOURCE_DRIFT:" + name)
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    adjudicator = load_comparator()
    OUT.mkdir(parents=True, exist_ok=False)
    rows = []
    patterns = fixture["arm_event_patterns"]
    for progress in itertools.product(fixture["progress_signs"], repeat=3):
        for exposure in itertools.product(fixture["exposure_signs"], repeat=3):
            for pattern, membership in patterns.items():
                recovery = membership["recovery"]
                coast = membership["coast"]
                rows.append({
                    "progress_signs": list(progress),
                    "exposure_signs": list(exposure),
                    "event_pattern": pattern,
                    "recovery_positive": recovery,
                    "coast_positive": coast,
                    "legacy_useful_present": recovery or coast,
                    "recovery_useful_present": recovery,
                    "legacy_status": adjudicator.comparative(
                        list(progress), list(exposure), True, recovery or coast),
                    "recovery_gated_status": adjudicator.comparative(
                        list(progress), list(exposure), True, recovery),
                })
    controls = {
        "no_threat_positive_event": adjudicator.comparative([1, 1, 0], [-1, -1, 0], False, True),
        "no_event_with_threat": adjudicator.comparative([1, 1, 0], [-1, -1, 0], True, False),
        "positive_control": adjudicator.comparative([1, 1, 0], [-1, -1, 0], True, True),
    }
    raw = {
        "schema": "r133-useful-effect-sensitivity-raw-v1",
        "freeze_sha256": sha(FREEZE),
        "fixture_sha256": sha(FIXTURE),
        "adjudicator_sha256": sha(SOURCE),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "rows": rows,
        "row_count": len(rows),
        "controls": controls,
        "candidate_invocations": 1,
        "candidate_exit_code": 0,
        "container": "NOT_USED",
    }
    raw_bytes = (json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n").encode()
    (OUT / "RAW.json").write_bytes(raw_bytes)
    run = {"status": "CANDIDATE_EXIT_0", "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
           "raw_bytes": len(raw_bytes), "row_count": len(rows), "candidate_invocations": 1,
           "container": "NOT_USED"}
    (OUT / "RUN.json").write_text(json.dumps(run, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(run, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
