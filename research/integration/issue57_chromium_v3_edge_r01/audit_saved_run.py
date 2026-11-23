"""Saved-data-only audit for Chromium caller-v3 smoke R01."""
import hashlib
import json
from pathlib import Path
import sys


def audit(packet):
    packet = Path(packet).resolve(strict=True)
    raw = packet / "raw"
    conditions = json.loads((raw / "conditions.json").read_text(encoding="utf-8"))
    result = json.loads((raw / "run.json").read_text(encoding="utf-8"))
    cleanup = json.loads((raw / "cleanup.json").read_text(encoding="utf-8"))
    repo = packet.parents[2]
    source_match = all(
        hashlib.sha256((repo / path).read_bytes()).hexdigest() == digest
        for path, digest in conditions["source_hashes_sha256"].items())
    captures_match = all(
        hashlib.sha256((raw / row["capture_file"]).read_bytes()).hexdigest()
        == row["capture_sha256"]
        for row in result["ocr_observations"])
    receipt = result["compiled_execution_receipt"]
    checks = {
        "source_hashes_match": source_match,
        "retained_capture_hashes_match": captures_match,
        "one_attempt_and_usage_retained": (
            result["accounting"]["attempted_calls"] == 1
            and result["accounting"]["completed_calls"] == 1
            and result["accounting"]["usage_totals"]["input_tokens"] == 0
            and result["accounting"]["usage_totals"]["output_tokens"] == 0),
        "exact_ocr_on_every_observation": bool(result["ocr_observations"])
            and all(row["state"] is True for row in result["ocr_observations"]),
        "one_submit_and_exact_post": (
            result["dispatched_operations"] == ["activate_submit"]
            and len(result["server_posts"]) == 1
            and result["server_posts"][0]["exact"] is True
            and result["server_posts"][0]["raw_body_utf8"] == "value=t991025-1"),
        "outer_effect_and_core_release": (
            result["outcome"] == "TASK_SUCCEEDED"
            and result["task_effect"] == "succeeded"
            and receipt["outcome"] == "TASK_SUCCEEDED"
            and receipt["completed_transitions"] == 1
            and len(receipt["transitions"]) == 1
            and receipt["transitions"][0]["release_verified"] is True),
        "owned_process_and_profile_cleanup": (
            cleanup["browser_close_returncode"] == 0
            and cleanup["launcher_returncode"] == 0
            and cleanup["profile_exists_after_cleanup"] is False
            and cleanup["owned_temp_root_exists_after_cleanup"] is False),
    }
    disposition = "PASS_SCOPED_EDGE_CALLER_V3_SMOKE" if all(checks.values()) else "HOLD"
    return {"disposition": disposition, "checks": checks,
            "scope": "one local headless Edge form submit; not matched efficiency or runtime readiness"}


if __name__ == "__main__":
    result = audit(sys.argv[1] if len(sys.argv) == 2 else Path(__file__).parent)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["disposition"].startswith("PASS") else 1)
