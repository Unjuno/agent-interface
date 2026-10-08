"""Independent checks over the frozen inputs and generated result."""
import hashlib
import json
from pathlib import Path

from source.observable_signal_guard_v2 import ObservableSignalGuard


ROOT = Path(__file__).parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check():
    freeze = json.loads((ROOT / "FREEZE.json").read_text(encoding="utf-8"))
    inputs_path = ROOT / "INPUTS.json"
    source_path = ROOT / "source" / "observable_signal_guard_v2.py"
    assert sha(inputs_path) == freeze["inputs_sha256"]
    assert sha(source_path) == freeze["source_sha256"]
    inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    assert len(inputs["cases"]) == len(result["cases"]) == 2
    binding = {"surface": 1, "geometry": [0, 0, 640, 480]}
    for case, row in zip(inputs["cases"], result["cases"]):
        assert row["iteration"] == case["iteration"]
        for signal_id in ("health", "ammo"):
            source_value = case[f"{signal_id}_source"]
            hard_minimum = case[f"{signal_id}_hard_minimum"]
            cap = case["authored_max_source_age_ms"]
            age_ms = case["observed_age_ms"]
            guard = ObservableSignalGuard(
                {"op": "observable_signal_guard",
                 "guard_id": "independent-audit", "source_sequence": 10,
                 "signal_id": signal_id, "source_value": source_value,
                 "hard_minimum": hard_minimum, "max_source_age_ms": cap,
                 "on_soft_change": "preserve_existing_policy",
                 "on_hard_change": "needs_decision",
                 "on_unknown": "needs_decision"},
                {"status": "observed", "signal_id": signal_id,
                 "value": source_value, "sequence": 10,
                 "capture_ns": 1_000_000_000, "binding": binding}, binding)
            outcome = guard.evaluate(
                {"status": "observed", "signal_id": signal_id,
                 "value": case[f"{signal_id}_current"], "sequence": 11,
                 "capture_ns": 1_000_000_000 + round(age_ms * 1_000_000),
                 "binding": binding})
            recorded = row["retained_outcomes"][signal_id]
            assert recorded == {"status": outcome["status"],
                                "reason": outcome["reason"]}
            assert outcome["status"] == "UNKNOWN"
            assert outcome["reason"] == "source_expired"
        assert row["same_samples_age_cap_30000ms"]["health"]["status"] == "UNCHANGED"
        assert row["same_samples_age_cap_30000ms"]["ammo"]["status"] == "SOFT_CHANGED"
        assert row["health_below_hard_minimum_age_cap_30000ms"] == {
            "status": "HARD_INVALIDATED", "reason": "below_hard_minimum"}
    return {"status": "PASS", "cases": 2,
            "source_sha256": sha(source_path),
            "inputs_sha256": sha(inputs_path),
            "result_sha256": sha(ROOT / "RESULT.json")}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))
