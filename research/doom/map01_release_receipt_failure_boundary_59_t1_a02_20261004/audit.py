from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    for line in (HERE / "FILES.sha256").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == expected, name
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
    for path, expected in freeze["sources"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    fixture = freeze["fixture"]
    import subprocess
    raw = subprocess.check_output(["git", "show", f"{fixture['commit']}:{fixture['path']}"], cwd=ROOT)
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    assert blob == fixture["blob"]
    baseline = freeze["oracle_baseline"]
    for path, expected in baseline["sources"].items():
        source = subprocess.check_output(["git", "show", f"{baseline['commit']}:{path}"], cwd=ROOT)
        assert hashlib.sha256(source).hexdigest() == expected, path
    assert result["status"] == "PASS_SCOPED"
    before, after = result["cases"]
    assert before["failed_call"] and after["failed_call"]
    assert before["after_failure"]["fake_server_key_down"] is True
    assert after["after_failure"]["fake_server_key_down"] is False
    assert before["after_failure"]["trace"]["release_attempts"] == 1
    assert before["after_retry"]["trace"]["release_attempts"] == 2
    assert after["after_failure"]["trace"]["release_attempts"] == 1
    retry = after["retry_receipt"]
    assert retry["release_applied"] is True
    assert retry["x11_release_request_issued"] is True
    assert retry["x11_sync_completed_before_return"] is True
    assert after["after_retry"]["fake_server_key_down"] is False
    assert after["after_retry"]["trace"]["release_attempts"] == 2
    import types
    import sys
    sys.path.insert(0, str(ROOT / "research/doom"))
    oracle_source = subprocess.check_output([
        "git", "show",
        f"{baseline['commit']}:research/doom/map01_feedback_release_contract_v1.py"],
        cwd=ROOT)
    oracle_module = types.ModuleType("frozen_a02_oracle")
    exec(compile(oracle_source, "frozen_a02_oracle.py", "exec"), oracle_module.__dict__)
    retry_receipt = dict(after["retry_receipt"], id="plan", step=1)
    admission = dict(after["admission"], id="plan", step=0,
                     owner_id=retry_receipt["owner_id"],
                     intent_token=retry_receipt["intent_token"])
    intervals = oracle_module.reconcile_key_intervals([admission, retry_receipt])
    assert len(intervals) == 1
    assert intervals[0]["release_transition_interval_ns"] == retry_receipt["release_transition_interval_ns"]
    assert after["after_failure"]["fake_server_key_down"] is False
    return {"schema": "map01-release-receipt-failure-boundary-audit-v1",
            "status": "PASS_SCOPED",
            "checks": ["artifact SHA256 inventory", "current source SHA256", "pinned fake-Xlib blob",
                       "XTest failure returns no receipt and retains held state",
                       "XSync failure after server application returns no receipt",
                       "oracle accepts retry as an interval although key was already up"]}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True))
