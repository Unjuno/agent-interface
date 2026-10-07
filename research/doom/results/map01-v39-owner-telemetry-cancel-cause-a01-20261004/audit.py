"""Independent saved-result and source-binding audit for A01."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def sha(data): return hashlib.sha256(data).hexdigest()


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    raw = json.loads((HERE / "RAW.json").read_text())
    parent = subprocess.check_output([
        "git", "show", f"{freeze['base_commit']}:research/live_control/input_owner_v12.py"])
    candidate = (ROOT / "research/live_control/input_owner_v12.py").read_bytes()
    assert sha(parent) == freeze["base_owner_sha256"] == raw["base_owner_sha256"]
    assert sha(candidate) == freeze["candidate_owner_sha256"] == raw["candidate_owner_sha256"]
    assert sha((HERE / "candidate.py").read_bytes()) == freeze["candidate_runner_sha256"]
    cases = raw["cases"]
    baseline = cases["parent_forced_post_sample_cancel"]
    fixed = cases["candidate_forced_post_sample_cancel"]
    ordinary = cases["candidate_ordinary_release"]
    telemetry = cases["candidate_explicit_up_telemetry"]
    assert baseline["reason"] == "release"
    assert fixed["reason"] == "cancelled"
    assert ordinary["reason"] == "release"
    for row in (baseline, fixed, ordinary):
        assert row["verified"] is True and row["keys_down"] == []
        assert row["buttons_down"] == [] and row["release_reply_verified"] is True
        assert row["physical_events"] == [[2, 38], [3, 38]]
    assert baseline["cancel_sampled_ns"] < baseline["cancel_visible_ns"]
    assert fixed["cancel_sampled_ns"] < fixed["cancel_visible_ns"]
    assert baseline["setter_finished"] and fixed["setter_finished"]
    assert telemetry["event"] == "input_release_rpc"
    assert (type(telemetry["interval"]) is list and len(telemetry["interval"]) == 2
            and all(type(value) is int for value in telemetry["interval"])
            and telemetry["interval"][0] <= telemetry["interval"][1])
    assert telemetry["intent_token"] == "intent-a01"
    assert telemetry["grants_input_authority"] is False
    assert telemetry["parent_owner_module"] == "input_owner_v11"
    assert telemetry["physical_events"] == [[2, 38], [3, 38]]
    result = {"status": "PASS_AUDIT", "checks": 21,
              "parent_false_classification": baseline["reason"],
              "candidate_classification": fixed["reason"],
              "ordinary_control": ordinary["reason"],
              "release_verified_empty_cases": 3,
              "telemetry_schema": telemetry["event"],
              "candidate_source_sha256": sha(candidate),
              "scope": "saved raw/source linkage and deterministic fake-Xlib receipt contract only"}
    (HERE / "AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__": main()
