"""Independent raw-trace auditor; deliberately does not import experiment.py."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

POLICIES = {"IMMEDIATE", "STAGE_1", "STAGE_2"}
EXPECTED = {
    "informative_signal_1": ("B", "A", ["B", "B"], True, 3),
    "uninformative": ("B", "A", ["UNKNOWN", "UNKNOWN"], True, 3),
    "informative_signal_2": ("B", "A", ["UNKNOWN", "B"], True, 3),
    "no_correction_route": ("B", "A", ["B", "B"], False, 3),
}


def audit(path: Path) -> dict:
    data = path.read_bytes()
    rows = [json.loads(line) for line in data.decode("utf-8").splitlines()]
    errors = []
    counts = defaultdict(lambda: {p: {"n": 0, "wrong": 0, "miss": 0} for p in POLICIES})
    seen = set()
    for index, row in enumerate(rows):
        sid = row.get("stratum")
        if sid not in EXPECTED:
            errors.append(f"row {index}: unknown stratum")
            continue
        truth, proposal, signals, route, deadline = EXPECTED[sid]
        policy = row.get("policy")
        if policy not in POLICIES:
            errors.append(f"row {index}: unknown policy")
            continue
        key = (sid, row.get("repetition"), policy)
        if key in seen:
            errors.append(f"row {index}: duplicate case")
        seen.add(key)
        if row.get("truth") != truth or row.get("proposal") != proposal or row.get("signals") != signals or row.get("correction_route") != route or row.get("deadline") != deadline:
            errors.append(f"row {index}: frozen input mismatch")
            continue
        t = {"IMMEDIATE": 0, "STAGE_1": 1, "STAGE_2": 2}[policy]
        if policy == "IMMEDIATE":
            committed = proposal
            expected_events = [{"t": 0, "op": "commit", "target": proposal}]
        else:
            observed = signals[:1] if policy == "STAGE_1" else signals
            known = next((x for x in reversed(observed) if x != "UNKNOWN"), proposal)
            committed = known if route else proposal
            expected_events = [{"t": 0, "op": "prepare", "target": proposal, "reversible": True}]
            expected_events += [{"t": i + 1, "op": "observe", "signal": signals[i]} for i in range(len(observed))]
            expected_events.append({"t": t, "op": "commit", "target": committed})
        expected = (committed, committed != truth, t > deadline)
        actual = (row.get("committed_target"), row.get("wrong_irreversible"), row.get("deadline_miss"))
        if row.get("events") != expected_events or actual != expected:
            errors.append(f"row {index}: trace/outcome mismatch")
        bucket = counts[sid][policy]
        bucket["n"] += 1
        bucket["wrong"] += int(committed != truth)
        bucket["miss"] += int(t > deadline)
    if len(rows) != 12 or len(seen) != 12:
        errors.append("expected exactly 12 unique first outcomes")
    for sid in EXPECTED:
        if any(counts[sid][p]["n"] != 1 for p in POLICIES):
            errors.append(f"{sid}: expected one case per policy")
    info1 = counts["informative_signal_1"]
    info2 = counts["informative_signal_2"]
    controls = ("uninformative", "no_correction_route")
    gates = {
        "stage1_beats_immediate_on_signal1": info1["STAGE_1"]["wrong"] < info1["IMMEDIATE"]["wrong"],
        "stage2_beats_stage1_on_signal2": info2["STAGE_2"]["wrong"] < info2["STAGE_1"]["wrong"],
        "control_no_error_reduction": all(counts[s]["STAGE_1"]["wrong"] == counts[s]["IMMEDIATE"]["wrong"] and counts[s]["STAGE_2"]["wrong"] == counts[s]["IMMEDIATE"]["wrong"] for s in controls),
        "no_deadline_misses": sum(v[p]["miss"] for v in counts.values() for p in POLICIES) == 0,
    }
    if not all(gates.values()):
        errors.append("one or more preregistered decision gates failed")
    return {"status": "PASS_SCOPED" if not errors else "FAIL_SCOPED", "rows": len(rows), "unique_cases": len(seen), "counts": counts, "gates": gates, "errors": errors, "raw_bytes": len(data), "raw_sha256": hashlib.sha256(data).hexdigest()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.raw)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "rows": result["rows"], "errors": len(result["errors"])}))


if __name__ == "__main__":
    main()
