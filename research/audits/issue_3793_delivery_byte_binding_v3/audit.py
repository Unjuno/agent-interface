"""Independent raw-only byte-binding audit for Issue #3816."""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

FROZEN_HEAD = "8bac49525c93835a69b6d441740a1c424faaecb2"
IMAGE = "python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"
PLAN_PATH = "research/integration/issue_3711_downstream_truncation_v1/audit-v2-successor-02/PLAN.md"
AUDITOR_PATH = "research/integration/issue_3711_downstream_truncation_v1/audit-v2-successor-02/audit.py"
EXPECTED = {
    "audit_freeze": "2d9b0e4ee289bad1402e5e6fe58f4734a788becd56d5e783dda1816518fbaf94",
    "audit_plan": "79741322f5c4b43d7d6a5a7b847bf3505bf94d2bc2f486ff27e40592515dd795",
    "audit_source": "ca3ccf5191d876eeda824555589c4580537dc04ec771fc52ef8914300ec289be",
    "audit_result": "4bb36c596ee85a48f79c21b18ae4dd6a08b09b7e6e72d351e89bb1188196ae54",
    "formal_freeze": "b7b2d2bebd24bfc54abc4a20bb00da452eafb084ed09fa7b2a2c57ad146658cd",
    "formal_raw": "3f51dc5a4c9c8acb48fc2929a8219260575271e5794cd5bd4afedf6f712afc73",
    "accepted": "e8ef9f6dd897325a22b1927d27e7fba2948051bb309cc472bbf2a1bfaba863d1",
    "delivered_prefix": "0450145d98f8ff197766d91827a438db1aa5800d556b4bee24eb57b33e168d4a",
    "audit_v1_result": "69454ea54a9c3b6b91ca6331645e4b0a7dc071cd9da4abb9b88bff7888afa7ca",
    "audit_v2_01_failure": "faeed58dc95b32ffc29add42f4e860ac5049db654b790d903b6ee3cb48931315",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value: dict) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def validate_freeze_source_hashes(freeze: dict) -> list[str]:
    hashes = freeze.get("sha256", {})
    errors = []
    if hashes.get(PLAN_PATH) != EXPECTED["audit_plan"]:
        errors.append("FROZEN_PLAN_HASH_MISMATCH")
    if hashes.get(AUDITOR_PATH) != EXPECTED["audit_source"]:
        errors.append("FROZEN_AUDITOR_HASH_MISMATCH")
    return errors


def load_inputs(root: Path, manifest_path: Path) -> tuple[dict, dict[str, bytes], list[str]]:
    errors: list[str] = []
    try:
        manifest = json.loads(manifest_path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}, {}, ["MANIFEST_MISSING_OR_INVALID"]
    if manifest.get("schema") != "agent-interface/issue-3816-audit-input-manifest-v1":
        errors.append("MANIFEST_SCHEMA_MISMATCH")
    if manifest.get("issue") != 3816 or manifest.get("allocation") != "issue3711-downstream-truncation-audit-v3-03":
        errors.append("MANIFEST_ALLOCATION_MISMATCH")
    if manifest.get("frozen_pr_head") != FROZEN_HEAD:
        errors.append("FROZEN_PR_HEAD_MISMATCH")
    if manifest.get("image") != IMAGE or manifest.get("platform") != "linux/arm64" or manifest.get("network") != "none":
        errors.append("FROZEN_CONTAINER_IDENTITY_MISMATCH")
    if manifest.get("formal_experiment_invocations") != 0:
        errors.append("FORMAL_EXPERIMENT_RERUN_FORBIDDEN")
    table = manifest.get("inputs")
    if not isinstance(table, dict) or set(table) != set(EXPECTED):
        errors.append("INPUT_MANIFEST_SET_MISMATCH")
        return manifest, {}, errors
    files: dict[str, bytes] = {}
    for key, expected_hash in EXPECTED.items():
        entry = table.get(key, {})
        if not isinstance(entry, dict) or entry.get("sha256") != expected_hash:
            errors.append(f"INPUT_MANIFEST_HASH_MISMATCH:{key}")
            continue
        rel = entry.get("path")
        if not isinstance(rel, str) or rel.startswith("/") or ".." in Path(rel).parts:
            errors.append(f"INPUT_PATH_INVALID:{key}")
            continue
        try:
            data = (root / rel).read_bytes()
        except OSError:
            errors.append(f"INPUT_MISSING:{key}")
            continue
        files[key] = data
        if sha(data) != expected_hash:
            errors.append(f"INPUT_SHA256_MISMATCH:{key}")
    return manifest, files, errors


def validate_history(files: dict[str, bytes]) -> list[str]:
    if set(files) != set(EXPECTED):
        return ["FROZEN_INPUT_SET_INCOMPLETE"]
    try:
        freeze = json.loads(files["audit_freeze"])
        formal_freeze = json.loads(files["formal_freeze"])
        raw = json.loads(files["formal_raw"])
        prior = json.loads(files["audit_result"])
        audit_v1 = json.loads(files["audit_v1_result"])
        audit_v2_01 = json.loads(files["audit_v2_01_failure"])
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ["FROZEN_JSON_INVALID"]
    errors = validate_freeze_source_hashes(freeze)
    checks = [
        (freeze.get("formal_raw_sha256") == sha(files["formal_raw"]), "AUDIT_FREEZE_RAW_BINDING_MISMATCH"),
        (freeze.get("formal_freeze_sha256") == sha(files["formal_freeze"]), "FORMAL_FREEZE_BINDING_MISMATCH"),
        (freeze.get("audit_v1_sha256") == sha(files["audit_v1_result"]), "AUDIT_V1_BINDING_MISMATCH"),
        (freeze.get("audit_v2_01_failure_sha256") == sha(files["audit_v2_01_failure"]), "AUDIT_V2_01_BINDING_MISMATCH"),
        (freeze.get("image") == IMAGE and freeze.get("image_digest") == IMAGE.split("@", 1)[1], "FROZEN_IMAGE_DIGEST_MISMATCH"),
        (freeze.get("platform") == "linux/arm64" and freeze.get("network") == "none", "FROZEN_PLATFORM_OR_NETWORK_MISMATCH"),
        (freeze.get("formal_base_commit") == formal_freeze.get("base_commit"), "FORMAL_BASE_COMMIT_MISMATCH"),
        (freeze.get("audit_source_commit") == freeze.get("audit_code_base_commit"), "AUDIT_SOURCE_COMMIT_MISMATCH"),
        (raw.get("base_commit") == freeze.get("formal_base_commit"), "RAW_BASE_COMMIT_MISMATCH"),
        (raw.get("image") == IMAGE and raw.get("image_digest") == freeze.get("image_digest"), "RAW_IMAGE_DIGEST_MISMATCH"),
        (raw.get("engine_platform") == "linux/arm64", "RAW_PLATFORM_MISMATCH"),
        (prior.get("disposition") == "PASS_V2_ARTIFACT_BINDING" and prior.get("errors") == [], "PRIOR_RESULT_MISMATCH"),
        (prior.get("formal_raw_sha256") == sha(files["formal_raw"]), "PRIOR_RAW_BINDING_MISMATCH"),
        (audit_v1.get("disposition") == "PASS_SCOPED_DOWNSTREAM_REJECTION_AND_READ_ONLY_RECOVERY", "AUDIT_V1_RESULT_MISMATCH"),
        (audit_v2_01.get("disposition") == "FAIL_AUDIT_V2" and audit_v2_01.get("errors") == ["ALLOCATION_OR_BASE_MISMATCH"], "AUDIT_V2_01_FAILURE_NOT_PRESERVED"),
    ]
    errors.extend(label for condition, label in checks if not condition)
    return errors


def delivery_errors(accepted: bytes, delivered: bytes, raw: dict) -> list[str]:
    errors: list[str] = []
    producer = raw.get("producer", {})
    downstream = raw.get("downstream", {})
    consumer = downstream.get("consumer", {})
    try:
        decoded = accepted.decode("utf-8")
        document = json.loads(decoded)
        if document.get("status") != "returned" or document.get("result", {}).get("scope") != "synthetic-only":
            errors.append("ACCEPTED_CONTENT_MISMATCH")
    except (UnicodeDecodeError, json.JSONDecodeError):
        decoded = None
        errors.append("ACCEPTED_JSON_INVALID")
    if sha(accepted) != producer.get("accepted_sha256"):
        errors.append("ACCEPTED_SHA256_MISMATCH")
    if decoded is not None:
        if producer.get("reported_character_count") != len(decoded):
            errors.append("ACCEPTED_CHARACTER_COUNT_MISMATCH")
        if producer.get("write_return_values") != [len(decoded)]:
            errors.append("PRODUCER_WRITE_RETURN_MISMATCH")
    if len(delivered) != downstream.get("delivered_bytes"):
        errors.append("DELIVERED_BYTES_MISMATCH")
    if sha(delivered) != downstream.get("delivered_sha256"):
        errors.append("DELIVERED_SHA256_MISMATCH")
    if not accepted.startswith(delivered) or len(delivered) >= len(accepted):
        errors.append("DELIVERED_NOT_STRICT_PREFIX")
    try:
        json.loads(delivered)
        error_type = None
        errors.append("TRUNCATED_PREFIX_ACCEPTED")
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        error_type = type(error).__name__
    if error_type != consumer.get("error_type"):
        errors.append("CONSUMER_ERROR_TYPE_MISMATCH")
    return errors


def adjudicate(files: dict[str, bytes], preflight_errors: list[str],
               history_errors: list[str], evaluator=delivery_errors) -> dict:
    source_errors = preflight_errors + history_errors
    if source_errors:
        return {"disposition": "STOP_SOURCE_OR_FREEZE_MISMATCH",
                "errors": source_errors, "baseline": None, "mutations": {}}
    raw = json.loads(files["formal_raw"])
    accepted = files["accepted"]
    delivered = files["delivered_prefix"]
    baseline_errors = evaluator(accepted, delivered, raw)
    needle = b"/out/attempt"
    occurrences = accepted.count(needle)
    mutated = accepted.replace(needle, b"/bad/attempt", 1)
    accepted_errors = evaluator(mutated, delivered, raw)
    truncated = delivered[:-1]
    prefix_errors = evaluator(accepted, truncated, raw)
    accepted_sound = (
        occurrences == 1 and len(mutated) == len(accepted)
        and "ACCEPTED_JSON_INVALID" not in accepted_errors
        and "ACCEPTED_CONTENT_MISMATCH" not in accepted_errors
        and "ACCEPTED_SHA256_MISMATCH" in accepted_errors
    )
    prefix_sound = (
        len(delivered) == 23 and len(truncated) == 22
        and accepted.startswith(truncated) and len(truncated) < len(accepted)
        and "DELIVERED_BYTES_MISMATCH" in prefix_errors
        and "DELIVERED_SHA256_MISMATCH" in prefix_errors
        and "DELIVERED_NOT_STRICT_PREFIX" not in prefix_errors
    )
    if baseline_errors:
        disposition = "FAIL_BASELINE_RECONSTRUCTION"
    elif not accepted_sound or not prefix_sound:
        disposition = "FAIL_MUTATION_BINDING"
    else:
        disposition = "PASS_AUDIT_BINDING_SCOPED"
    return {
        "disposition": disposition,
        "errors": baseline_errors,
        "baseline": {
            "raw_sha256": sha(files["formal_raw"]),
            "accepted_bytes": len(accepted),
            "accepted_sha256": sha(accepted),
            "delivered_bytes": len(delivered),
            "delivered_sha256": sha(delivered),
            "errors": baseline_errors,
        },
        "mutations": {
            "accepted_same_length_path_change": {
                "changed_occurrences": occurrences, "bytes_before": len(accepted),
                "bytes_after": len(mutated), "errors": accepted_errors,
                "rejected_by_receipt_hash": "ACCEPTED_SHA256_MISMATCH" in accepted_errors,
                "control_sound": accepted_sound,
            },
            "delivered_prefix_23_to_22_bytes": {
                "bytes_before": len(delivered), "bytes_after": len(truncated),
                "errors": prefix_errors,
                "rejected_by_receipt_length": "DELIVERED_BYTES_MISMATCH" in prefix_errors,
                "rejected_by_receipt_hash": "DELIVERED_SHA256_MISMATCH" in prefix_errors,
                "control_sound": prefix_sound,
            },
        },
    }


def main() -> int:
    if len(sys.argv) != 5:
        raise SystemExit("usage: audit.py INPUT_ROOT MANIFEST_PATH OUTPUT_ROOT AUDIT_SOURCE_COMMIT")
    input_root, manifest_path, output_root = map(Path, sys.argv[1:4])
    audit_source_commit = sys.argv[4]
    if len(audit_source_commit) != 40 or any(c not in "0123456789abcdef" for c in audit_source_commit):
        raise SystemExit("invalid audit source commit")
    manifest, files, preflight_errors = load_inputs(input_root, manifest_path)
    history_errors = validate_history(files) if not preflight_errors else []
    decision = adjudicate(files, preflight_errors, history_errors)
    result = {
        "schema": "agent-interface/issue-3816-audit-result-v1",
        "issue": 3816,
        "allocation": manifest.get("allocation"),
        **decision,
        "audit_source_commit": audit_source_commit,
        "frozen_pr_head": FROZEN_HEAD,
        "image": IMAGE,
        "platform": platform.machine(),
        "network": "none",
        "formal_experiment_invocations": 0,
        "audit_invocations": 1,
    }
    result["result_sha256"] = canonical_sha(result)
    if not output_root.is_dir() or any(output_root.iterdir()):
        raise SystemExit("STOP_OUTPUT_NOT_EMPTY_OR_MISSING")
    (output_root / "RESULT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["disposition"] == "PASS_AUDIT_BINDING_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
