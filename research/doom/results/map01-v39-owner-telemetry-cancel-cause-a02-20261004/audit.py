"""Audit A02 raw receipts and all pinned owner/runner source identities."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
A01 = HERE.parent / "map01-v39-owner-telemetry-cancel-cause-a01-20261004"


def sha(data): return hashlib.sha256(data).hexdigest()


def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text())
    raw = json.loads((HERE / "RAW.json").read_text())
    base = subprocess.check_output([
        "git", "show", f"{freeze['parent_commit']}:research/live_control/input_owner_v12.py"])
    candidate = (ROOT / "research/live_control/input_owner_v12.py").read_bytes()
    assert sha(base) == freeze["parent_owner_sha256"] == raw["base_owner_sha256"]
    assert sha(candidate) == freeze["candidate_owner_sha256"] == raw["candidate_owner_sha256"]
    assert sha((A01 / "candidate.py").read_bytes()) == freeze["inherited_candidate_source_sha256"]
    assert sha((HERE / "run_candidate.py").read_bytes()) == freeze["runner_sha256"]
    assert sha(Path(__file__).read_bytes()) == freeze["auditor_sha256"]
    cases = raw["cases"]
    before = cases["parent_forced_post_sample_cancel"]
    after = cases["candidate_forced_post_sample_cancel"]
    normal = cases["candidate_ordinary_release"]
    up = cases["candidate_explicit_up_telemetry"]
    assert before["reason"] == "release" and after["reason"] == "cancelled"
    assert normal["reason"] == "release"
    for item in (before, after, normal):
        assert item["verified"] is True and item["keys_down"] == []
        assert item["buttons_down"] == [] and item["release_reply_verified"] is True
        assert item["physical_events"] == [[2, 38], [3, 38]]
    assert before["cancel_sampled_ns"] < before["cancel_visible_ns"]
    assert after["cancel_sampled_ns"] < after["cancel_visible_ns"]
    assert before["setter_finished"] and after["setter_finished"]
    assert up["event"] == "input_release_rpc"
    assert type(up["interval"]) is list and len(up["interval"]) == 2
    assert all(type(value) is int for value in up["interval"])
    assert up["interval"][0] <= up["interval"][1]
    assert up["intent_token"] == "intent-a01"
    assert up["grants_input_authority"] is False
    assert up["parent_owner_module"] == "input_owner_v11"
    assert up["physical_events"] == [[2, 38], [3, 38]]
    result = {"status": "PASS_AUDIT", "checks": 24,
              "parent_reason": before["reason"], "candidate_reason": after["reason"],
              "ordinary_reason": normal["reason"], "empty_verified_cases": 3,
              "telemetry_event": up["event"], "checksums_bound": True,
              "auditor_sha256": sha(Path(__file__).read_bytes()),
              "scope": "saved raw/source identity and deterministic fake-Xlib receipt contract only"}
    (HERE / "AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__": main()
