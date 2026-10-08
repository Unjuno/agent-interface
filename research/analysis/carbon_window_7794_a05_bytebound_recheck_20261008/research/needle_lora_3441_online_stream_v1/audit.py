"""Independent result auditor; does not import or execute the experiment runner."""
import base64, gzip, hashlib, json, math, sys

EXPECTED_RUNNER_SHA256 = "62c74d80aed3c0932967fa42bdf9eda00aea64d33a3bb7c6066ed903bb3d61d6"
EXPECTED_ROWS = 4096
EXPECTED_FEEDBACK = 16
EXPECTED_STEPS = 128
EXPECTED_CONTROLS = {
    "unknown_role": "YIELD",
    "stale_epoch": "YIELD",
    "wrong_version": "YIELD",
    "missing_adapter": "YIELD",
}

def audit(envelope):
    compressed = base64.b64decode(envelope["result_gzip_b64"], validate=True)
    raw = gzip.decompress(compressed)
    assert hashlib.sha256(raw).hexdigest() == envelope["result_sha256"]
    data = json.loads(raw)
    assert data["allocation"] == "needle-lora-3441-online-stream-v1"
    assert data["environment"]["device"] == "cpu"
    assert data["environment"]["deterministic_algorithms"] is True
    assert data["frozen_design"]["online_feedback_rows"] == EXPECTED_FEEDBACK
    assert data["frozen_design"]["online_total_steps"] == EXPECTED_STEPS
    assert data["frozen_design"]["batch_steps"] == EXPECTED_STEPS
    assert data["frozen_design"]["heldout_per_role"] == EXPECTED_ROWS

    metrics = data["routed_metrics"]
    for role in ("A", "B_ONLINE", "B_BATCH"):
        row = metrics[role]
        expected, predicted = row["expected"], row["predictions"]
        assert len(expected) == EXPECTED_ROWS and len(predicted) == EXPECTED_ROWS
        correct = sum(a == b for a, b in zip(expected, predicted))
        assert correct == row["correct"]
        assert correct / EXPECTED_ROWS == row["accuracy"]
        assert row["n"] == EXPECTED_ROWS

    times = data["timing_ms"]
    assert len(times["online_per_feedback"]) == EXPECTED_FEEDBACK
    assert all(isinstance(x, (int, float)) and x >= 0 for x in times["online_per_feedback"])
    sorted_times = sorted(times["online_per_feedback"])
    p95 = sorted_times[math.ceil(0.95 * len(sorted_times)) - 1]
    assert p95 == times["online_feedback_p95"]
    controls_ok = data["invalid_route_controls"] == EXPECTED_CONTROLS
    integrity_ok = all(data["snapshot"][k] is True for k in (
        "full_state_roundtrip_exact", "full_state_rollback_exact", "base_immutable"))
    quality_ok = (
        metrics["A"]["accuracy"] >= 0.90
        and metrics["B_ONLINE"]["accuracy"] >= 0.90
        and metrics["B_BATCH"]["accuracy"] >= 0.90
        and metrics["B_ONLINE"]["accuracy"] >= metrics["B_BATCH"]["accuracy"] - 0.03
        and p95 <= 60.0
    )
    if not controls_ok or not integrity_ok:
        disposition = "FAIL_ROUTE_OR_SNAPSHOT_INTEGRITY"
    elif quality_ok:
        disposition = "PASS_ONLINE_ROLE_ADAPTATION_SCOPED"
    else:
        disposition = "FAIL_ONLINE_ADAPTATION_QUALITY"

    return {
        "disposition": disposition,
        "result_sha256": envelope["result_sha256"],
        "rows_recomputed": {"A": EXPECTED_ROWS, "B_ONLINE": EXPECTED_ROWS,
                            "B_BATCH": EXPECTED_ROWS},
        "metrics": {
            "base_A_accuracy": metrics["A"]["accuracy"],
            "online_B_accuracy": metrics["B_ONLINE"]["accuracy"],
            "batch_B_accuracy": metrics["B_BATCH"]["accuracy"],
            "online_feedback_p95_ms": p95,
        },
        "controls_yield": controls_ok,
        "full_state_integrity": integrity_ok,
        "runner_sha256_frozen": EXPECTED_RUNNER_SHA256,
    }

if __name__ == "__main__":
    envelope = json.load(sys.stdin)
    print(json.dumps(audit(envelope), sort_keys=True, separators=(",", ":")))
