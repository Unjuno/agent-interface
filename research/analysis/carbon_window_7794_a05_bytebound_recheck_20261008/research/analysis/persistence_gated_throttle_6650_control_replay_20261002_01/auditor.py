"""One-shot independent replay auditor for immutable Issue #6650 T0 output."""
from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

from replay import differences, reconstruct


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _corruption_controls(fixture: dict, expected: dict) -> dict[str, dict]:
    controls: dict[str, dict] = {}

    def reject(name: str, change) -> None:
        altered = deepcopy(expected)
        change(altered)
        delta = differences(reconstruct(fixture), altered)
        controls[name] = {"rejected": bool(delta), "difference_count": len(delta),
                          "first_difference": delta[0] if delta else None}

    reject("tier_at_offer", lambda x: x["traces"]["sustained_overload"]
           ["persistence"]["requests"][0].__setitem__("tier_at_offer", 99))
    reject("signal_value", lambda x: x["traces"]["sustained_overload"]
           ["persistence"]["states"][0].__setitem__("signal", True))
    reject("transition_timestamp", lambda x: x["traces"]["sustained_overload"]
           ["persistence"]["transitions"][0].__setitem__("at", 999))
    reject("suppression_decision", lambda x: x["traces"]["sustained_overload"]
           ["persistence"]["requests"][0].__setitem__("status", "SUPPRESSED"))
    reject("cross_session_contamination", lambda x: x["traces"]["session_isolation"]
           ["persistence"]["states"][0].__setitem__("session", "OTHER"))
    reject("mandatory_suppression", lambda x: next(
        row for row in x["traces"]["mandatory_flood"]["persistence"]["requests"]
        if row["kind"] == "mandatory").__setitem__("status", "SUPPRESSED"))
    reject("service_order", lambda x: x["traces"]["sustained_overload"]
           ["queue_length"]["services"].__setitem__(slice(0, 2),
           reversed(x["traces"]["sustained_overload"]["queue_length"]["services"][:2])))
    reject("generation_at_start", lambda x: x["traces"]["semantic_invalidation"]
           ["persistence"]["services"][0].__setitem__("generation_at_start", 55))
    reject("freshness_terminal", lambda x: x["traces"]["sustained_overload"]
           ["fixed"]["services"][0].__setitem__("outcome", "SERVICED_WITHIN_FRESHNESS"))
    return controls


def execute(package: Path) -> dict:
    freeze = json.loads((package / "FREEZE.json").read_text())
    fixture_path = package.parent / "persistence_gated_throttle_6650_t0_v1" / "fixture.json"
    raw_path = package.parent / "persistence_gated_throttle_6650_t0_v1" / "RAW.json"
    replay_path = package / "replay.py"
    auditor_path = package / "auditor.py"
    for path, key in ((fixture_path, "fixture_sha256"), (raw_path, "raw_sha256"),
                      (replay_path, "replay_sha256"), (auditor_path, "auditor_sha256")):
        if sha256(path) != freeze[key]:
            raise ValueError(f"frozen hash mismatch: {key}")
    fixture = json.loads(fixture_path.read_text())
    raw = json.loads(raw_path.read_text())
    expected = reconstruct(fixture)
    errors = differences(expected, raw)
    controls = _corruption_controls(fixture, expected)
    return {
        "allocation": freeze["allocation"],
        "result": "PASS_AUDIT_REPLAY_SCOPED" if not errors and all(
            item["rejected"] for item in controls.values()) else "FAIL_AUDIT_REPLAY",
        "fixture_sha256": sha256(fixture_path), "raw_sha256": sha256(raw_path),
        "expected_sha256": hashlib.sha256(json.dumps(
            expected, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "trace_count": len(fixture["traces"]),
        "policy_replays": len(fixture["traces"]) * 4,
        "mismatch_count": len(errors), "mismatches": errors[:100],
        "mutation_controls": controls,
    }


if __name__ == "__main__":
    output_path = Path(sys.argv[2])
    result = execute(Path(sys.argv[1]))
    output_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"allocation": result["allocation"], "result": result["result"],
                      "policy_replays": result["policy_replays"],
                      "mismatch_count": result["mismatch_count"],
                      "mutations_rejected": sum(x["rejected"] for x in
                                                 result["mutation_controls"].values())},
                     sort_keys=True))
    raise SystemExit(0 if result["result"] == "PASS_AUDIT_REPLAY_SCOPED" else 1)
