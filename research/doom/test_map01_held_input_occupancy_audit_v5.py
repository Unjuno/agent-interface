import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "audit_v5", HERE / "audit_map01_held_input_occupancy_fulltrace_v5.py")
audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(audit)


def test_absent_normal_classification_flags_are_false():
    assert audit.flag({}, "no_input_before_admission") is False
    assert audit.flag({}, "partial_admission_before_keys_held") is False
    assert audit.flag({}, "cancel_raced_input_ack") is False


def test_only_literal_true_is_a_classification():
    assert audit.flag({"x": True}, "x") is True
    assert audit.flag({"x": 1}, "x") is False
    assert audit.flag({"x": None}, "x") is False


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_")]
    for test in tests:
        test()
    print(f"PASS {len(tests)} audit-v5 construction tests")
