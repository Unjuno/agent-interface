"""Independent saved-raw audit for A06."""

import hashlib
import json
import sys
from pathlib import Path


EXPECTED_SOURCES = {
    "caller": "8517d130d7336b27e6ddfc0ee06629d2b1183070cf845c3ef4ada8adc3cd79ca",
    "compiled": "d22160919ad7fc00d8a1c6e1da3240a316b024738362d714fafa68b772005014",
    "adapter": "0856ad8d7a522ee239040e0c878d43472e6211a7360e4dad3195032fac9d713e",
}


def main():
    raw_path, out_path = map(Path, sys.argv[1:3])
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    assert raw["schema"] == "compiled-form-field-semantic-counterexample-a06-v1"
    assert raw["source_sha256"] == EXPECTED_SOURCES
    assert raw["scenario"] == {
        "expected_field_value": "task-token-991081-1",
        "observed_field_value": "",
        "field_pixels_changed_after_entry": True,
        "submit_target_present": True,
    }
    assert raw["actions"] == ["enter_exact_token", "activate_submit"]
    receipt = raw["compiled_receipt"]
    assert receipt["outcome"] == "TASK_SUCCEEDED"
    assert receipt["completed_transitions"] == 2
    assert all(row["release_verified"] for row in receipt["transitions"])
    assert receipt["transitions"][1]["matched_conditions"] == {
        "field_pixels_changed": True, "submit_target_present": True,
    }
    report = {
        "status": "FAIL_FIELD_SEMANTIC_PREDICATE",
        "scope": "source-pinned test-double contract counterexample; no GUI/model/provider/input/network calls",
        "finding": "pixel change with empty requested field admits Submit and produces TASK_SUCCEEDED under successful downstream test doubles",
        "source_sha256": EXPECTED_SOURCES,
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "assertions": {
            "source_freeze_matches": True,
            "task_value_absent": True,
            "field_pixels_changed": True,
            "submit_was_admitted": True,
            "test_double_success_was_misleading": True,
            "live_application_claim": False,
        },
    }
    out_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
