import json
from pathlib import Path

ROOT = Path(__file__).parent
RESULT = ROOT / "result.json"


def audit(data):
    rows = data["samples"]
    assert len(rows) == 3
    for row in rows:
        before, capture, after, decided = (
            row["host_before_ns"], row["container_capture_ns"],
            row["host_after_ns"], row["host_decided_ns"])
        assert after >= before
        assert row["host_minus_container_interval_ns"] == [before-capture, after-capture]
        assert row["decision_minus_capture_ns"] == decided-capture
        assert decided >= after
    assert all(row["decision_minus_capture_ns"] > 0 for row in rows)
    assert data["independent_recomputation"]["final_container_capture_minus_first_ns"] == (
        rows[-1]["container_capture_ns"] - rows[0]["container_capture_ns"])
    final = rows[-1]
    age = final["host_decided_ns"] - final["container_capture_ns"]
    assert age == data["independent_recomputation"]["final_controller_minus_container_capture_ns"]
    threshold = data["controls"]["cross_domain"]["configured_max_current_age_ms"] * 1_000_000
    assert threshold == data["independent_recomputation"]["stale_threshold_ns"]
    assert data["independent_recomputation"]["final_container_capture_minus_first_ns"] < threshold
    assert age > threshold
    assert data["controls"]["host_host"] == {
        "outcome": "receipt", "state": "INPUT_ACTIVE", "current_input_authority": True}
    cross = data["controls"]["cross_domain"]
    assert cross["outcome"] == "receipt" and cross["exception"] is None
    assert cross["state"] == "CANCEL_REQUIRED"
    assert cross["current_input_authority"] is False
    assert cross["physical_release_verified"] is False
    assert cross["requires_new_decision"] is True
    assert cross["validity_status"] == "REJECTED_STALE"
    assert cross["validity_reason"] == "current_snapshot_too_old"
    assert data["disposition"]["pre_registered_exception_gate"] == (
        "HOLD_EXPECTED_INVERSION_NOT_REPRODUCED")
    return {"samples": len(rows), "offsets_consistent": True,
            "result": "PASS_INDEPENDENT_NUMERIC_AND_GUARD_RECEIPT_AUDIT_SCOPED"}


if __name__ == "__main__":
    print(json.dumps(audit(json.loads(RESULT.read_text())), sort_keys=True))
