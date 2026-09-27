"""Independent stdlib audit of the retained one-nanosecond boundary result."""
import json
import hashlib
from pathlib import Path

RESULT = Path(__file__).with_name("results") / "result.json"
ROOT = Path(__file__).parent


def verify_manifest():
    manifest = ROOT / "SHA256SUMS.txt"
    entries = {}
    for line in manifest.read_text().splitlines():
        digest, relative = line.split("  ", 1)
        assert relative not in entries and not relative.startswith("/")
        path = ROOT / relative
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        entries[relative] = digest
    assert set(entries) == {
        "PLAN.md", "RESULT.md", "experiment.py", "audit.py",
        "test_experiment.py", "results/result.json"}
    return True


def audit(value):
    assert value["experiment"] == "map01-action-validity-time-boundary-v1"
    assert value["classification"] == "FAIL_GUARD_LOCAL_FAIL_CLOSED_BOUNDARY"
    provenance = value["provenance"]
    assert provenance["main_commit"] == "a778bdd577b149a5ec964bbe19da533311335e2f"
    assert provenance["source_blobs"] == {
        "action_validity_admission_v1.py": "31bd30bd9baf6b7d56494cc3a18b2c6c70ffbc5e",
        "running_action_guard_v1.py": "d54047e78bc76f53ef47c6f70fd4a3be6318f09c",
        "test_running_action_guard_v1.py": "a4a423da1118f2da8cca08e9965419fac322461a",
        "test_action_validity_admission_v1.py": "9d5dbf119fcb56c75ac1732da60b18832876e1a5"}
    assert provenance["container_image"] == "issue2679-map01-runtime@sha256:029e1867aeb843f2d63080343bfbb61540b64852ce00d4d99ec0be51796a093e"
    assert provenance["platform"] == "linux/arm64"
    assert provenance["network"] == "none"
    assert provenance["root_filesystem"] == "read-only"
    assert provenance["source_mount"] == "read-only"
    assert len(value["rows"]) == 4
    rows = {row["case"]: row for row in value["rows"]}
    assert set(rows) == {
        "active_decision_after_capture",
        "active_decision_equal_capture",
        "active_decision_one_ns_before_capture",
        "between_decision_one_ns_before_capture",
    }
    for case in ("active_decision_after_capture", "active_decision_equal_capture"):
        row = rows[case]
        assert row["outcome"] == "receipt"
        assert row["state"] == "INPUT_ACTIVE"
        assert row["current_input_authority"] is True
        assert row["invalidation"] is None
    row = rows["active_decision_one_ns_before_capture"]
    assert row["outcome"] == "exception"
    assert row["exception_type"] == "ValueError"
    assert row["message"] == "controller decision precedes current snapshot"
    assert row["state_after"] == "INPUT_ACTIVE"
    assert row["current_input_authority_after"] is True
    assert row["invalidation_after"] is None
    row = rows["between_decision_one_ns_before_capture"]
    assert row["outcome"] == "exception"
    assert row["exception_type"] == "ValueError"
    assert row["message"] == "controller decision precedes current snapshot"
    assert row["state_after"] == "BETWEEN_PROGRAMS_REQUIRES_FRESH_CHECK"
    assert row["current_input_authority_after"] is False
    assert row["invalidation_after"] is None
    return True


if __name__ == "__main__":
    verify_manifest()
    data = json.loads(RESULT.read_text())
    audit(data)
    print("PASS_RAW_AUDIT cases=4 classification=FAIL_GUARD_LOCAL_FAIL_CLOSED_BOUNDARY")
