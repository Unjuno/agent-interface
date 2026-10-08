from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from fixtures import cases

HERE = Path(__file__).resolve().parent
UPSTREAM = HERE.parent / "map01_r133_recovery_coast_t1_v1" / "decision_rule_construction_v2" / "adjudicator.py"
FREEZE = HERE / "FREEZE.json"
OUT = HERE / "results" / "construction-01"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_adjudicator():
    spec = importlib.util.spec_from_file_location("frozen_upstream_adjudicator", UPSTREAM)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.adjudicate


def main() -> int:
    if OUT.exists():
        print(json.dumps({"status": "STOP_OUTPUT_EXISTS"}))
        return 2
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    for relative, expected in freeze["pinned_sha256"].items():
        path = (HERE / relative).resolve() if not relative.startswith("upstream/") else UPSTREAM
        if sha(path) != expected:
            print(json.dumps({"status": "STOP_SOURCE_DRIFT", "path": relative}))
            return 3
    adjudicate = load_adjudicator()
    OUT.mkdir(parents=True, exist_ok=False)
    raw_cases = []
    for name, original, _status, _reason in cases():
        wire = json.dumps(original, sort_keys=True, separators=(",", ":"))
        parsed = json.loads(wire)
        decision = adjudicate(parsed)
        raw_cases.append({
            "case_id": name,
            "wire_json": wire,
            "parsed_rows": parsed,
            "decision": decision,
        })
    raw = {
        "schema": "map01-json-boundary-host-raw-v1",
        "main_sha": freeze["main_sha"],
        "upstream_adjudicator_sha256": freeze["pinned_sha256"]["upstream/adjudicator.py"],
        "freeze_sha256": sha(FREEZE),
        "candidate_sha256": sha(HERE / "candidate.py"),
        "candidate_invocations": 1,
        "cases": raw_cases,
    }
    raw_bytes = (json.dumps(raw, sort_keys=True, indent=2) + "\n").encode()
    (OUT / "RAW.json").write_bytes(raw_bytes)
    run = {"schema": "map01-json-boundary-host-run-v1", "status": "CANDIDATE_EXIT_0",
           "candidate_exit_code": 0, "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
           "raw_bytes": len(raw_bytes), "case_count": len(raw_cases)}
    (OUT / "RUN.json").write_text(json.dumps(run, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(run, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
