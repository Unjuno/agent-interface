"""Frozen allocation-02 entrypoint; independent replay remains in replay.py."""
from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

from replay import differences, reconstruct


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_once(package: Path) -> dict:
    freeze = json.loads((package / "FREEZE-02.json").read_text())
    analysis = package.parent
    prior = analysis / "persistence_gated_throttle_6650_t0_v1"
    fixture_path, raw_path = prior / "fixture.json", prior / "RAW.json"
    sources = {"fixture_sha256": fixture_path, "raw_sha256": raw_path,
               "replay_sha256": package / "replay.py",
               "auditor_sha256": package / "auditor_02.py",
               "test_replay_sha256": package / "test_replay.py",
               "preregistration_sha256": package / "PREREGISTRATION-02.md"}
    for key, path in sources.items():
        want = freeze["inputs"].get(key) if key in ("fixture_sha256", "raw_sha256") else freeze["auditor_sources"].get(key)
        if want != digest(path):
            raise ValueError(f"frozen hash mismatch: {key}")

    fixture = json.loads(fixture_path.read_text())
    raw = json.loads(raw_path.read_text())
    expected = reconstruct(fixture)
    mismatch = differences(expected, raw)
    controls: dict[str, dict] = {}

    def reject(name: str, edit) -> None:
        changed = deepcopy(expected)
        edit(changed)
        delta = differences(reconstruct(fixture), changed)
        controls[name] = {"rejected": bool(delta), "difference_count": len(delta),
                          "first_difference": delta[0] if delta else None}

    reject("tier_at_offer", lambda x: x["traces"]["sustained_overload"]["persistence"]["requests"][0].__setitem__("tier_at_offer", 99))
    reject("signal_value", lambda x: x["traces"]["sustained_overload"]["persistence"]["states"][0].__setitem__("signal", True))
    reject("transition_timestamp", lambda x: x["traces"]["sustained_overload"]["persistence"]["transitions"][0].__setitem__("at", 999))
    reject("suppression_decision", lambda x: x["traces"]["sustained_overload"]["persistence"]["requests"][0].__setitem__("status", "SUPPRESSED"))
    reject("cross_session_contamination", lambda x: x["traces"]["session_isolation"]["persistence"]["states"][0].__setitem__("session", "OTHER"))
    reject("mandatory_suppression", lambda x: next(row for row in x["traces"]["mandatory_flood"]["persistence"]["requests"] if row["kind"] == "mandatory").__setitem__("status", "SUPPRESSED"))
    reject("service_order", lambda x: x["traces"]["sustained_overload"]["queue_length"]["services"].__setitem__(slice(0, 2), reversed(x["traces"]["sustained_overload"]["queue_length"]["services"][:2])))
    reject("generation_at_start", lambda x: x["traces"]["semantic_invalidation"]["persistence"]["services"][0].__setitem__("generation_at_start", 55))
    reject("freshness_terminal", lambda x: x["traces"]["sustained_overload"]["fixed"]["services"][7].__setitem__("outcome", "SERVICED_WITHIN_FRESHNESS"))

    passed = not mismatch and len(controls) == 9 and all(row["rejected"] for row in controls.values())
    return {"allocation": freeze["allocation"],
            "result": "PASS_AUDIT_REPLAY_SCOPED" if passed else "FAIL_AUDIT_REPLAY",
            "fixture_sha256": digest(fixture_path), "raw_sha256": digest(raw_path),
            "trace_count": len(fixture["traces"]), "policy_replays": len(fixture["traces"]) * 4,
            "mismatch_count": len(mismatch), "mismatches": mismatch,
            "mutation_controls": controls,
            "candidate_runs": 0, "auditor_runs": 1, "retries": 0}


if __name__ == "__main__":
    package = Path(sys.argv[1])
    out = Path(sys.argv[2])
    result = audit_once(package)
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"allocation": result["allocation"], "result": result["result"],
                      "policy_replays": result["policy_replays"],
                      "mismatch_count": result["mismatch_count"],
                      "mutations_rejected": sum(x["rejected"] for x in result["mutation_controls"].values())},
                     sort_keys=True))
    raise SystemExit(0 if result["result"] == "PASS_AUDIT_REPLAY_SCOPED" else 1)
