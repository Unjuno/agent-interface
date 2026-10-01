import argparse
import base64
import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path("/study")
EXPECTED_KEYS = {
    "audit_freeze", "audit_plan", "audit_source", "audit_result",
    "formal_freeze", "formal_raw", "accepted", "delivered_prefix",
    "audit_v1_result", "audit_v2_01_failure",
}
EXPECTED_SOURCE_FILES = {
    "PLAN.md", "ENVIRONMENT.json", "source/run.py",
    "source/audit.py", "source/controls.py",
}
IMAGE = "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"
INTAKE = "522ff97664c12399e94e28462688afc905732373"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_read(root, rel):
    path = Path(rel)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("unsafe input path")
    return (root / path).read_bytes()


def load_inputs(root, manifest):
    found = {}
    errors = []
    table = manifest.get("inputs")
    if not isinstance(table, dict) or set(table) != EXPECTED_KEYS:
        return {}, ["manifest key set mismatch"], {}
    for key in sorted(EXPECTED_KEYS):
        entry = table[key]
        try:
            value = safe_read(root, entry["path"] + (".b64" if key == "delivered_prefix" else ""))
            if key == "delivered_prefix":
                value = base64.b64decode(value.strip(), validate=True)
        except Exception as exc:
            errors.append("input unreadable:" + key + ":" + type(exc).__name__)
            continue
        digest = sha(value)
        if digest != entry.get("sha256"):
            errors.append("INPUT_SHA256_MISMATCH:" + key)
        found[key] = value
    return found, errors, {
        key: {"path": table[key].get("path"), "sha256": sha(found[key])}
        for key in found
    }


def independent_delivery(accepted, delivered, raw):
    errors = []
    p = raw.get("producer") or {}
    d = raw.get("downstream") or {}
    c = d.get("consumer") or {}
    try:
        text = accepted.decode("utf-8")
        parsed = json.loads(text)
        if parsed.get("status") != "returned" or parsed.get("result", {}).get("scope") != "synthetic-only":
            errors.append("ACCEPTED_CONTENT_MISMATCH")
    except Exception:
        text = None
        errors.append("ACCEPTED_JSON_INVALID")
    if sha(accepted) != p.get("accepted_sha256"):
        errors.append("ACCEPTED_SHA256_MISMATCH")
    if text is not None and (p.get("reported_character_count") != len(text) or p.get("write_return_values") != [len(text)]):
        errors.append("PRODUCER_COUNT_MISMATCH")
    if len(delivered) != d.get("delivered_bytes"):
        errors.append("DELIVERED_BYTES_MISMATCH")
    if sha(delivered) != d.get("delivered_sha256"):
        errors.append("DELIVERED_SHA256_MISMATCH")
    if not accepted.startswith(delivered) or len(delivered) >= len(accepted):
        errors.append("DELIVERED_NOT_STRICT_PREFIX")
    try:
        json.loads(delivered)
        failure = None
    except Exception as exc:
        failure = type(exc).__name__
    if failure != c.get("error_type"):
        errors.append("CONSUMER_ERROR_TYPE_MISMATCH")
    return errors, failure


def audit(input_root, freeze_path, result_path):
    checks = []
    errors = []
    try:
        freeze_bytes = Path(freeze_path).read_bytes()
        freeze = json.loads(freeze_bytes)
        side = (ROOT / "FREEZE.sha256").read_text(encoding="ascii").split()[0]
        checks.append("freeze_sidecar")
        if sha(freeze_bytes) != side:
            errors.append("freeze sidecar mismatch")
    except Exception:
        return {"decision": "FAIL", "checks": checks, "errors": ["freeze unavailable"]}
    try:
        result = json.loads(Path(result_path).read_bytes())
        manifest_encoded = (Path(input_root) / "MANIFEST.json.b64").read_bytes()
        manifest_bytes = base64.b64decode(manifest_encoded.strip(), validate=True)
        manifest = json.loads(manifest_bytes)
    except Exception:
        return {"decision": "FAIL", "checks": checks, "errors": ["result or manifest unavailable"]}
    checks.append("manifest_bytes")
    if sha(manifest_bytes) != freeze.get("manifest_sha256"):
        errors.append("manifest digest mismatch")
    if manifest.get("schema") != "agent-interface/issue-3809-audit-input-manifest-v1":
        errors.append("manifest schema mismatch")
    if freeze.get("intake_main") != INTAKE or freeze.get("image_id") != IMAGE:
        errors.append("freeze identity mismatch")
    if result.get("issue") != 4649 or result.get("allocation") != freeze.get("allocation"):
        errors.append("result identity mismatch")
    if result.get("intake_main") != INTAKE or result.get("image_id") != IMAGE:
        errors.append("result source/image mismatch")
    if result.get("source_sha256") != freeze.get("source_sha256"):
        errors.append("result source digest ledger mismatch")
    if result.get("freeze_sha256") != sha(freeze_bytes):
        errors.append("result freeze digest mismatch")
    if result.get("manifest_sha256") != sha(manifest_bytes):
        errors.append("result manifest digest mismatch")
    if result.get("execution_platform") != "linux/amd64" or platform.machine() != "x86_64":
        errors.append("execution platform mismatch")
    if not sys.version.startswith("3.12.14 "):
        errors.append("auditor Python mismatch")
    checks.append("execution_identity")

    expected_sources = freeze.get("source_sha256")
    if not isinstance(expected_sources, dict) or set(expected_sources) != EXPECTED_SOURCE_FILES:
        errors.append("source key set mismatch")
    else:
        for rel, expected in expected_sources.items():
            try:
                actual = sha((ROOT / rel).read_bytes())
            except OSError:
                errors.append("source missing:" + rel)
                continue
            if actual != expected:
                errors.append("source digest mismatch:" + rel)
    checks.append("source_hashes")

    files, input_errors, table = load_inputs(Path(input_root), manifest)
    errors.extend(input_errors)
    checks.append("input_hashes")
    if set(files) != EXPECTED_KEYS:
        errors.append("input set incomplete")
    else:
        raw = json.loads(files["formal_raw"])
        audit_freeze = json.loads(files["audit_freeze"])
        formal_freeze = json.loads(files["formal_freeze"])
        prior = json.loads(files["audit_result"])
        v1 = json.loads(files["audit_v1_result"])
        v201 = json.loads(files["audit_v2_01_failure"])
        declared = freeze.get("input_sha256")
        actual_hashes = {key: value.get("sha256") for key, value in table.items()}
        if actual_hashes != declared:
            errors.append("result input ledger mismatch")
        audit_roles = manifest["inputs"]
        plan_path = audit_roles["audit_plan"]["path"]
        source_path = audit_roles["audit_source"]["path"]
        history_ok = (
            audit_freeze.get("sha256", {}).get(plan_path) == audit_roles["audit_plan"]["sha256"]
            and audit_freeze.get("sha256", {}).get(source_path) == audit_roles["audit_source"]["sha256"]
            and "PLAN.md" not in audit_freeze.get("sha256", {})
            and "audit.py" not in audit_freeze.get("sha256", {})
            and audit_freeze.get("formal_raw_sha256") == sha(files["formal_raw"])
            and audit_freeze.get("formal_freeze_sha256") == sha(files["formal_freeze"])
            and audit_freeze.get("audit_v1_sha256") == sha(files["audit_v1_result"])
            and audit_freeze.get("audit_v2_01_failure_sha256") == sha(files["audit_v2_01_failure"])
            and formal_freeze.get("image_digest") == IMAGE
            and formal_freeze.get("platform") == "linux/arm64"
            and raw.get("engine_platform") == "linux/arm64"
            and raw.get("image_digest") == IMAGE
            and raw.get("freeze_sha256") == sha(files["formal_freeze"])
            and prior.get("disposition") == "PASS_V2_ARTIFACT_BINDING"
            and prior.get("errors") == []
            and v1.get("disposition") == "PASS_SCOPED_DOWNSTREAM_REJECTION_AND_READ_ONLY_RECOVERY"
            and v1.get("errors") == []
            and v201.get("disposition") == "FAIL_AUDIT_V2"
            and v201.get("errors") == ["ALLOCATION_OR_BASE_MISMATCH"]
        )
        if not history_ok:
            errors.append("history/provenance role mismatch")
        checks.append("history_roles")

        baseline, parse_error = independent_delivery(files["accepted"], files["delivered_prefix"], raw)
        accepted = files["accepted"]
        delivered = files["delivered_prefix"]
        changed = accepted.replace(b"/out/attempt", b"/bad/attempt", 1)
        changed_errors, _ = independent_delivery(changed, delivered, raw)
        shortened = delivered[:-1]
        short_errors, short_parse_error = independent_delivery(accepted, shortened, raw)
        expected_mutations = {
            "accepted_same_length_path_change": {
                "changed_occurrences": accepted.count(b"/out/attempt"),
                "bytes_before": len(accepted),
                "bytes_after": len(changed),
                "errors": changed_errors,
                "valid_json": "ACCEPTED_JSON_INVALID" not in changed_errors,
                "rejected_by_receipt_hash": "ACCEPTED_SHA256_MISMATCH" in changed_errors,
            },
            "delivered_prefix_23_to_22_bytes": {
                "bytes_before": len(delivered),
                "bytes_after": len(shortened),
                "errors": short_errors,
                "rejected_by_receipt_length": "DELIVERED_BYTES_MISMATCH" in short_errors,
                "rejected_by_receipt_hash": "DELIVERED_SHA256_MISMATCH" in short_errors,
                "invalid_json": short_parse_error == "JSONDecodeError",
            },
        }
        base_record = result.get("baseline") or {}
        if baseline or base_record.get("errors") != baseline:
            errors.append("baseline reconstruction mismatch")
        if base_record.get("accepted_sha256") != sha(files["accepted"]) or base_record.get("delivered_sha256") != sha(files["delivered_prefix"]):
            errors.append("baseline digest fields mismatch")
        if result.get("mutations") != expected_mutations:
            errors.append("mutation reconstruction mismatch")
        prov = result.get("provenance") or {}
        if (
            prov.get("audit_plan_freeze_key") != plan_path
            or prov.get("audit_source_freeze_key") != source_path
            or prov.get("audit_freeze_keys_are_full_paths") is not True
            or prov.get("historical_formal_platform") != "linux/arm64"
            or prov.get("historical_raw_platform") != "linux/arm64"
        ):
            errors.append("reported path-role provenance mismatch")
        if result.get("disposition") != "PASS_FULLPATH_BYTE_AUDIT_LOCAL_AMD64_SCOPED":
            errors.append("runner disposition not PASS")
        checks.append("raw_reconstruction")
    return {
        "schema": "issue3809-independent-audit-v1",
        "decision": "PASS_INDEPENDENT" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
        "input_count": len(files) if "files" in locals() else 0,
        "baseline_parse_error": parse_error if "parse_error" in locals() else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--result", required=True)
    args = parser.parse_args()
    try:
        result = audit(args.input_root, args.freeze, args.result)
    except Exception as exc:
        result = {
            "schema": "issue3809-independent-audit-v1",
            "decision": "FAIL",
            "checks": [],
            "errors": ["AUDITOR_EXCEPTION:" + type(exc).__name__],
            "stderr_required_empty": True,
        }
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["decision"] == "PASS_INDEPENDENT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
