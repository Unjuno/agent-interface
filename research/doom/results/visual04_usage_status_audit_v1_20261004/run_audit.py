#!/usr/bin/env python3
"""Run status-aware interpretation on the byte-pinned visual04 usage records."""

import hashlib
import json
from pathlib import Path

from usage_audit import audit_usage

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SOURCE = REPO / "research/doom/v16_visual_readmission_59_4d74_20261004"
OUT = HERE / "out/a01"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    freeze = load_json(HERE / "FREEZE.json")
    actual = {}
    for relative, expected in freeze["raw_files"].items():
        path = SOURCE / relative
        raw = path.read_bytes()
        actual[relative] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        if actual[relative] != expected:
            raise SystemExit("source_pin_mismatch:" + relative)
    report = load_json(SOURCE / "run/episode/report.json")
    host_rows = [json.loads(line) for line in (SOURCE / "run/host.stdout.jsonl").read_text(encoding="utf-8").splitlines() if line]
    result = audit_usage(report, host_rows)
    result["source_commit"] = freeze["source_commit"]
    result["raw_file_hashes"] = actual
    if result["disposition"] != "PASS_STATUS_AWARE_RECORD_JOIN":
        raise SystemExit(json.dumps(result, indent=2, sort_keys=True))
    if OUT.exists():
        raise SystemExit("refusing_to_overwrite:" + str(OUT))
    OUT.mkdir(parents=True)
    (OUT / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": result["disposition"], "turns": len(result["turn_usage"]),
                      "completed_snapshot_sum": result["completed_turn_last_snapshot_sum"],
                      "unknown_interrupted_turns": result["unknown_interrupted_turns"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
