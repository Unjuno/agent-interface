"""Audit the saved baseline/candidate receipt comparison without rerunning it."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
COMMIT = "6a22a43ce6ed3a3acc687c561e0dfcc37a5f294b"


def audit():
    for line in (HERE / "FILES.sha256").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        actual = hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        assert actual == expected, (name, actual, expected)
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    assert freeze["source_commit"] == COMMIT
    for path, expected in freeze["sources"].items():
        source = subprocess.check_output(["git", "show", f"{COMMIT}:{path}"])
        actual = hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest()
        assert actual == expected, (path, actual, expected)
    for path, expected in freeze["tested_sources"].items():
        actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        assert actual == expected, (path, actual, expected)
    fixture = freeze["fixture"]
    fixture_source = subprocess.check_output(
        ["git", "show", f"{fixture['commit']}:{fixture['path']}"])
    fixture_blob = hashlib.sha1(
        b"blob " + str(len(fixture_source)).encode() + b"\0" + fixture_source).hexdigest()
    assert fixture_blob == fixture["blob"]
    result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8-sig"))
    candidate_patch = (HERE / "CANDIDATE.patch").read_text(encoding="utf-8")
    assert "call_release_with_receipt" in candidate_patch
    assert "release_transition_interval_ns" in candidate_patch
    assert result["sources"] == freeze["sources"]
    assert result["fixture"] == fixture
    for path, expected in result["candidate_worktree_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    oracle = freeze["integration_oracle"]
    assert result["candidate_worktree_sha256"][oracle["path"]] == oracle["sha256"]
    unit = json.loads((HERE / "V11_UNIT_TEST.json").read_text(encoding="utf-8-sig"))
    assert unit["status"] == "PASS" and unit["tests"] == 12
    assert unit["failures"] == 0 and unit["errors"] == 0
    assert unit["tested_sources"] == freeze["tested_sources"]
    legacy = result["legacy_v10_compatibility"]
    assert legacy["key_up_return"] is None
    assert legacy["button_up_return"] is None
    assert legacy["admission"]["keycode"] == 87
    baseline = result["baseline_aliased"]
    assert baseline["release_receipts"][1]["x11_release_and_sync_completed_before_return"] is True
    assert baseline["repeated_up_receipt"]["x11_release_and_sync_completed_before_return"] is True
    assert baseline["button_noop_receipt"]["x11_release_and_sync_completed_before_return"] is True
    assert baseline["counts_after_releases"]["key_release_requests"] == 1
    assert baseline["counts_after_releases"]["sync_calls"] == 3
    assert baseline["counts_after_repeated_up"] == baseline["counts_after_releases"]
    assert baseline["counts_after_button_noop"] == baseline["counts_after_releases"]
    for arm, expected_codes in ((result["candidate_injective"], [87, 65]),
                                (result["candidate_aliased"], [77, 77])):
        assert [row["keycode"] for row in arm["admissions"]] == expected_codes
        for receipt in arm["release_receipts"]:
            applied = receipt["release_applied"]
            assert receipt["x11_release_request_issued"] is applied
            assert receipt["x11_sync_completed_before_return"] is applied
            assert receipt["x11_release_and_sync_completed_before_return"] is applied
            assert (receipt["release_transition_interval_ns"] is not None) is applied
            assert receipt["keycode"] in expected_codes
    alias = result["candidate_aliased"]
    noop_key = alias["release_receipts"][1]
    noop_repeat = alias["repeated_up_receipt"]
    noop_button = alias["button_noop_receipt"]
    for receipt in (noop_key, noop_repeat, noop_button):
        assert receipt["release_applied"] is False
        assert receipt["release_transition_interval_ns"] is None
        assert receipt["interval_width_ns"] is None
        assert len(receipt["call_interval_ns"]) == 2
    assert noop_key["keycode"] == 77
    assert noop_button["button"] == 1
    counts = alias["counts_after_button_noop"]
    assert counts["key_release_requests"] == 1
    assert counts["button_release_requests"] == 0
    assert counts["sync_calls"] == 3
    typed = result["typed_backend_integration"]
    assert [row["step"] for row in typed["events"]] == [0, 1, 2, 3]
    typed_releases = [row for row in typed["events"]
                      if row["event"] == "input_release_rpc"]
    assert [row["release_applied"] for row in typed_releases] == [True, False]
    assert [row["step"] for row in typed_releases] == [2, 3]
    assert typed["counts"] == {"key_release_requests": 1, "sync_calls": 3}
    assert len(typed["reconciled_intervals"]) == 1
    assert typed["reconciled_intervals"][0]["keys"] == ["A", "W"]
    assert typed["reconciled_intervals"][0]["keycode"] == 77
    sys.path.insert(0, str(ROOT / "research/doom"))
    from map01_feedback_release_contract_v1 import reconcile_key_intervals
    owner_id = alias["release_receipts"][0]["owner_id"]
    events = []
    for step, admission in enumerate(alias["admissions"]):
        events.append(dict(admission, id="plan", step=step, owner_id=owner_id,
                           intent_token="probe-intent"))
    for step, receipt in enumerate(alias["release_receipts"]):
        events.append(dict(receipt, id="plan", step=step))
    events.append(dict(alias["repeated_up_receipt"], id="plan", step=1))
    reconciled = reconcile_key_intervals(events)
    assert len(reconciled) == 1
    assert reconciled[0]["keys"] == ["A", "W"]
    assert reconciled[0]["keycode"] == 77
    assert reconciled[0]["admission_count"] == 2
    return {
        "schema": "map01-v11-release-receipt-repair-audit-v1",
        "status": "PASS_SCOPED",
        "checks": [
            "artifact SHA256 inventory",
            "pinned V10/V11 source blobs",
            "pinned fake-Xlib fixture blob",
            "legacy V10 up/button-up return values remain None",
            "V11 and typed backend contract tests pass against checked-out sources",
            "baseline false-success key/button no-op receipts",
            "candidate applied key releases match request and sync counts",
            "candidate no-op receipts have no release interval or false success",
            "failure-free candidate receipts reconcile into one aliased keycode interval",
            "actual V11-to-typed-backend-to-oracle path joins across release-step provenance",
            "synthetic scope only",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
