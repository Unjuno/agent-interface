"""Independent, stdlib-only audit of one candidate result JSON."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
PINNED = {
    "research/live_control/input_owner_v10.py": "341b3c01649943ddaad5f28431a792c4889cc36e",
    "research/live_control/input_transition_owner_v3.py": "0ea631abcf6272f0538a9ef9198ad8069b47b464",
    "research/live_control/owner_keyup_release_semantics_5156_v2/release_protocol_v2.py":
        "55272e127073a84c9eb541bc650fee74f3fc7123",
}
AUTO = {"stop_requested", "expired", "surface_changed", "focus_changed", "cancelled", "thread_exit"}
POSITIVE = {*(f"auto.{x}" for x in AUTO), "explicit.key_up.string", "explicit.button_up.integer"}
NEGATIVE = {
    "unknown_reason", "missing_identity", "wrong_identity", "extra_identity", "bool_button",
    "out_of_range_button", "authority_true", "authority_missing", "missing_caller_bracket",
    "inverted_caller_bracket", "auto_caller_timestamp", "auto_request_id", "auto_explicit_operation",
    "explicit_autonomous_reason", "duplicate_owner_sequence", "omitted_positive", "duplicated_positive",
    "source_drift", "output_collision",
}


def blob_id(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True)
    args = parser.parse_args()
    result_path = Path(args.result).resolve()
    raw = result_path.read_bytes()
    result = json.loads(raw)
    failures = []
    if set(result.get("positive_case_ids", [])) != POSITIVE or len(result.get("positive_case_ids", [])) != len(POSITIVE):
        failures.append("positive case multiset differs")
    if set(result.get("positive_outcomes", {})) != POSITIVE or not all(result["positive_outcomes"].values()):
        failures.append("positive outcomes incomplete or rejected")
    if set(result.get("negative_case_ids", [])) != NEGATIVE or len(result.get("negative_case_ids", [])) != len(NEGATIVE):
        failures.append("negative case multiset differs")
    if set(result.get("negative_rejected", {})) != NEGATIVE or not all(result["negative_rejected"].values()):
        failures.append("negative control accepted or omitted")
    if result.get("status") != "PASS_SYNTHETIC_SCHEMA_COMPATIBILITY_ONLY":
        failures.append("candidate did not report scoped pass")
    if result.get("scope") != "SYNTHETIC_SCHEMA_COMPATIBILITY_ONLY":
        failures.append("scope claim missing")
    if result.get("authority_grants") != 0 or result.get("x11_observed") is not False:
        failures.append("authority/X11 boundary differs")
    if result.get("source_blob_ids") != PINNED:
        failures.append("pinned source blob map differs")
    for rel, expected in PINNED.items():
        source = (ROOT / rel).read_bytes()
        if blob_id(source) != expected:
            failures.append("pinned source drift: " + rel)
        if result.get("source_sha256", {}).get(rel) != hashlib.sha256(source).hexdigest():
            failures.append("source SHA-256 mismatch: " + rel)
    report = {"status": "PASS_INDEPENDENT_AUDIT" if not failures else "FAIL_INDEPENDENT_AUDIT",
              "result_path": str(result_path), "result_sha256": hashlib.sha256(raw).hexdigest(),
              "positive_case_count": len(result.get("positive_case_ids", [])),
              "negative_case_count": len(result.get("negative_case_ids", [])),
              "failures": failures, "authority_grants": 0, "x11_observed": False}
    print(json.dumps(report, sort_keys=True))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
