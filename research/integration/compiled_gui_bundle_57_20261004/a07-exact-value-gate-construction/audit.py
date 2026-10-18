"""Saved-raw independent checks for the A07 exact-value gate construction."""

import hashlib
import json
import sys
from pathlib import Path


EXPECTED_SOURCES = {
    "adapter_v2": "f1f3f6b2a1f0487a9c6f65b51936fafc8b6101390b1e4070f8e31f741a28b6ef",
    "compiled_core": "d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014",
}
ROOT = Path(__file__).resolve().parents[4]


def main():
    raw_path, audit_path = map(Path, sys.argv[1:3])
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    assert raw["schema"] == "compiled-form-exact-value-gate-a07-v1"
    expected_sources = dict(EXPECTED_SOURCES)
    expected_sources["runner"] = hashlib.sha256((Path(__file__).parent / "run.py").read_bytes()).hexdigest()
    assert raw["source_sha256"] == expected_sources
    for name, relative in {
            "adapter_v2": "research/live_control/integrated_efficiency_compiled_adapter_v2.py",
            "compiled_core": "runtime/core_v1/compiled_gui.py"}.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == EXPECTED_SOURCES[name]
    assert raw["scope"] == "test-double construction only; no observer/image/GUI/model/input/network calls"

    mismatch = raw["cases"]["mismatch"]
    assert mismatch["exact_value_after_entry"] is False
    assert mismatch["actions"] == ["enter_exact_token"]
    assert mismatch["effect_verifier_calls"] == []
    assert mismatch["receipt"]["outcome"] == "SAFE_YIELD"
    assert mismatch["receipt"]["reason"] == "effect_failed"
    assert mismatch["receipt"]["completed_transitions"] == 1

    exact = raw["cases"]["exact_match"]
    assert exact["exact_value_after_entry"] is True
    assert exact["actions"] == ["enter_exact_token", "activate_submit"]
    assert exact["receipt"]["outcome"] == "TASK_SUCCEEDED"
    assert exact["receipt"]["completed_transitions"] == 2
    assert exact["receipt"]["transitions"][1]["matched_conditions"] == {
        "field_value_matches_task": True, "submit_target_present": True,
    }

    result = {
        "status": "PASS_EXACT_VALUE_GATE_CONSTRUCTION_SCOPED",
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "source_sha256": expected_sources,
        "audit_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "assertions": {
            "pixel_change_with_wrong_value_does_not_submit": True,
            "wrong_value_preserves_safe_stop_after_entry": True,
            "exact_value_and_submit_target_allow_submit": True,
            "completion_requires_separate_submission_predicate": True,
            "observer_exact_value_semantics_live_qualified": False,
            "efficiency_claim": False,
        },
    }
    audit_path.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                          encoding="utf-8")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
