import importlib.util
import json
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("audit_v3", HERE / "audit_map01_recovery_cover_mechanism_v3.py")
audit_v3 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_v3)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def build(root, *, negative=0, reduction=0.20):
    write(root / "construction.json", {"allocation_id": "map01-recovery-cover-mechanism-live-v3-01", "model_calls": 0})
    pairs = []
    for index in (1, 2, 3):
        coast = 600_000_000
        recovery = int(coast * (1 - reduction))
        pairs.append({
            "pair_index": index,
            "failures": [],
            "coast_no_retained_input_upper_ns": coast,
            "recovery_no_retained_input_upper_ns": recovery,
            "recovery_negative_event_count": negative if index == 1 else 0,
            "recovery_positive_event_count": 0,
        })
        for arm in ("coast_control", "bounded_recovery"):
            runtime = root / f"pair-{index:02d}" / arm / "runtime"
            runtime.mkdir(parents=True)
            rows = [{"event": "ready"}]
            encoded = "\n".join(map(json.dumps, rows)) + "\n"
            (runtime / "events.jsonl").write_text(encoded, encoding="utf-8")
            (runtime / "delivered.jsonl").write_text(encoded, encoding="utf-8")
            write(runtime / "scorer-summary.json", {"scheduler": {"missed_sample_periods": 0}})
            write(root / f"pair-{index:02d}" / arm / "terminal-score-audit.json", {"pass": True})
    write(root / "summary.json", {"pairs": pairs})


def test_pass_mechanism_only():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        build(root)
        result = audit_v3.audit(root)
        assert result["pass"] is True
        assert result["decision"] == "PASS_MECHANISM_ONLY"


def test_threshold_is_hold():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        build(root, reduction=0.05)
        result = audit_v3.audit(root)
        assert result["pass"] is False
        assert result["decision"] == "HOLD"
        assert "median_reduction_below_10pct" in result["failures"]


def test_negative_recovery_event_is_fail():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        build(root, negative=1)
        result = audit_v3.audit(root)
        assert result["pass"] is False
        assert result["decision"] == "FAIL"


if __name__ == "__main__":
    tests = [test_pass_mechanism_only, test_threshold_is_hold, test_negative_recovery_event_is_fail]
    for test in tests:
        test()
    print(f"PASS {len(tests)} mechanism-v3 audit tests")
