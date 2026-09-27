import argparse
import base64
import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path("/study")
INPUT_ROOT = Path("/inputs")
SOURCE_ROOT = ROOT / "source"
EXPECTED_KEYS = {
    "audit_freeze", "audit_plan", "audit_source", "audit_result",
    "formal_freeze", "formal_raw", "accepted", "delivered_prefix",
    "audit_v1_result", "audit_v2_01_failure",
}
PINNED_IMAGE = "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9"
INTAKE = "522ff97664c12399e94e28462688afc905732373"
ALLOCATION = "issue3809-fullpath-byte-audit-localamd64-20260927"
EXPECTED_SOURCE_FILES = {
    "PLAN.md", "ENVIRONMENT.json", "source/run.py",
    "source/audit.py", "source/controls.py",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_bytes())


def source_errors(freeze):
    errors = []
    table = freeze.get("source_sha256")
    if not isinstance(table, dict) or set(table) != EXPECTED_SOURCE_FILES:
        return ["SOURCE_MANIFEST_SET_MISMATCH"]
    for rel, expected in table.items():
        path = ROOT / rel
        try:
            actual = sha(path.read_bytes())
        except OSError:
            errors.append("SOURCE_MISSING:" + rel)
            continue
        if actual != expected:
            errors.append("SOURCE_SHA256_MISMATCH:" + rel)
    try:
        sidecar = (ROOT / "FREEZE.sha256").read_text(encoding="ascii").strip().split()[0]
        if sidecar != sha((ROOT / "FREEZE.json").read_bytes()):
            errors.append("FREEZE_SHA256_MISMATCH")
    except (OSError, IndexError, UnicodeDecodeError):
        errors.append("FREEZE_SIDECAR_INVALID")
    return errors


def input_bytes(key, entry):
    rel = entry["path"]
    path = Path(rel)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("INPUT_PATH_INVALID:" + key)
    local = INPUT_ROOT / (str(path) + ".b64" if key == "delivered_prefix" else path)
    raw = local.read_bytes()
    if key == "delivered_prefix":
        raw = base64.b64decode(raw.strip(), validate=True)
    return raw


def preflight(freeze):
    errors = []
    if freeze.get("schema") != "issue3809-fullpath-byte-audit-localamd64-freeze-v1":
        errors.append("FREEZE_SCHEMA_MISMATCH")
    if freeze.get("issue") != 4649 or freeze.get("allocation") != ALLOCATION:
        errors.append("ALLOCATION_IDENTITY_MISMATCH")
    if freeze.get("intake_main") != INTAKE:
        errors.append("INTAKE_MAIN_MISMATCH")
    if freeze.get("image_id") != PINNED_IMAGE:
        errors.append("IMAGE_ID_MISMATCH")
    if freeze.get("execution_platform") != "linux/amd64" or platform.machine() != "x86_64":
        errors.append("EXECUTION_PLATFORM_MISMATCH")
    if not sys.version.startswith("3.12.14 "):
        errors.append("PYTHON_VERSION_MISMATCH")
    errors.extend(source_errors(freeze))
    try:
        manifest_b64 = (INPUT_ROOT / "MANIFEST.json.b64").read_bytes()
        manifest_bytes = base64.b64decode(manifest_b64.strip(), validate=True)
        manifest = json.loads(manifest_bytes)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return errors + ["MANIFEST_INVALID"], {}, {}, None
    if sha(manifest_bytes) != freeze.get("manifest_sha256"):
        errors.append("MANIFEST_SHA256_MISMATCH")
    if freeze.get("manifest_git_blob") != "d5127266279299ada9ecb30af14a942370a3cc21":
        errors.append("MANIFEST_BLOB_MISMATCH")
    if manifest.get("schema") != "agent-interface/issue-3809-audit-input-manifest-v1":
        errors.append("MANIFEST_SCHEMA_MISMATCH")
    if manifest.get("issue") != 3809 or manifest.get("allocation") != "issue3711-downstream-truncation-audit-v3-02":
        errors.append("MANIFEST_ALLOCATION_MISMATCH")
    table = manifest.get("inputs")
    expected = freeze.get("input_sha256")
    if not isinstance(table, dict) or set(table) != EXPECTED_KEYS or not isinstance(expected, dict) or set(expected) != EXPECTED_KEYS:
        return errors + ["INPUT_MANIFEST_SET_MISMATCH"], {}, {}, manifest
    files = {}
    actual_table = {}
    for key in sorted(EXPECTED_KEYS):
        entry = table[key]
        if not isinstance(entry, dict) or expected.get(key) != entry.get("sha256"):
            errors.append("INPUT_EXPECTED_HASH_MISMATCH:" + key)
            continue
        try:
            data = input_bytes(key, entry)
        except (OSError, KeyError, ValueError, base64.binascii.Error):
            errors.append("INPUT_UNREADABLE:" + key)
            continue
        digest = sha(data)
        actual_table[key] = {"path": entry.get("path"), "sha256": digest}
        files[key] = data
        if digest != entry.get("sha256"):
            errors.append("INPUT_SHA256_MISMATCH:" + key)
    if set(files) != EXPECTED_KEYS:
        errors.append("INPUT_SET_INCOMPLETE")
    if errors:
        return errors, files, actual_table, manifest
    try:
        af = json.loads(files["audit_freeze"])
        ff = json.loads(files["formal_freeze"])
        raw = json.loads(files["formal_raw"])
        prior = json.loads(files["audit_result"])
        audit1 = json.loads(files["audit_v1_result"])
        audit201 = json.loads(files["audit_v2_01_failure"])
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ["HISTORY_JSON_INVALID"], files, actual_table, manifest
    roles = manifest["inputs"]
    audit_plan_path = roles["audit_plan"]["path"]
    audit_source_path = roles["audit_source"]["path"]
    audit_hashes = af.get("sha256", {})
    if audit_hashes.get(audit_plan_path) != roles["audit_plan"]["sha256"]:
        errors.append("AUDIT_PLAN_FULL_PATH_ROLE_MISMATCH")
    if audit_hashes.get(audit_source_path) != roles["audit_source"]["sha256"]:
        errors.append("AUDIT_SOURCE_FULL_PATH_ROLE_MISMATCH")
    if "PLAN.md" in audit_hashes or "audit.py" in audit_hashes:
        errors.append("AUDIT_FREEZE_ROLE_AMBIGUOUS")
    if af.get("formal_raw_sha256") != sha(files["formal_raw"]):
        errors.append("AUDIT_FREEZE_RAW_BINDING_MISMATCH")
    if af.get("formal_freeze_sha256") != sha(files["formal_freeze"]):
        errors.append("FORMAL_FREEZE_BINDING_MISMATCH")
    if af.get("audit_v1_sha256") != sha(files["audit_v1_result"]):
        errors.append("AUDIT_V1_BINDING_MISMATCH")
    if af.get("audit_v2_01_failure_sha256") != sha(files["audit_v2_01_failure"]):
        errors.append("AUDIT_V2_01_BINDING_MISMATCH")
    if af.get("image_digest") != PINNED_IMAGE or af.get("platform") != "linux/arm64":
        errors.append("HISTORICAL_AUDIT_FREEZE_IDENTITY_MISMATCH")
    if ff.get("image_digest") != PINNED_IMAGE or ff.get("platform") != "linux/arm64":
        errors.append("HISTORICAL_FORMAL_FREEZE_IDENTITY_MISMATCH")
    if raw.get("image_digest") != PINNED_IMAGE or raw.get("engine_platform") != "linux/arm64":
        errors.append("HISTORICAL_RAW_IDENTITY_MISMATCH")
    if raw.get("freeze_sha256") != sha(files["formal_freeze"]):
        errors.append("RAW_FREEZE_BINDING_MISMATCH")
    if prior.get("disposition") != "PASS_V2_ARTIFACT_BINDING" or prior.get("errors") != []:
        errors.append("PRIOR_RESULT_DISPOSITION_MISMATCH")
    if audit1.get("disposition") != "PASS_SCOPED_DOWNSTREAM_REJECTION_AND_READ_ONLY_RECOVERY" or audit1.get("errors") != []:
        errors.append("AUDIT_V1_DISPOSITION_MISMATCH")
    if audit201.get("disposition") != "FAIL_AUDIT_V2" or audit201.get("errors") != ["ALLOCATION_OR_BASE_MISMATCH"]:
        errors.append("AUDIT_V2_01_FAILURE_MISMATCH")
    provenance = {
        "audit_plan_freeze_key": audit_plan_path,
        "audit_plan_expected_sha256": audit_hashes.get(audit_plan_path),
        "audit_source_freeze_key": audit_source_path,
        "audit_source_expected_sha256": audit_hashes.get(audit_source_path),
        "audit_freeze_keys_are_full_paths": (
            audit_plan_path in audit_hashes and audit_source_path in audit_hashes
            and "PLAN.md" not in audit_hashes and "audit.py" not in audit_hashes
        ),
        "historical_formal_platform": ff.get("platform"),
        "historical_raw_platform": raw.get("engine_platform"),
    }
    return errors, files, actual_table, (manifest, provenance)


def delivery(accepted, delivered, raw):
    errors = []
    producer = raw.get("producer", {})
    downstream = raw.get("downstream", {})
    consumer = downstream.get("consumer", {})
    try:
        text = accepted.decode("utf-8")
        doc = json.loads(text)
        if doc.get("status") != "returned" or doc.get("result", {}).get("scope") != "synthetic-only":
            errors.append("ACCEPTED_CONTENT_MISMATCH")
    except (UnicodeDecodeError, json.JSONDecodeError):
        text = None
        errors.append("ACCEPTED_JSON_INVALID")
    if sha(accepted) != producer.get("accepted_sha256"):
        errors.append("ACCEPTED_SHA256_MISMATCH")
    if text is not None:
        if producer.get("reported_character_count") != len(text):
            errors.append("ACCEPTED_CHARACTER_COUNT_MISMATCH")
        if producer.get("write_return_values") != [len(text)]:
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


def formal(freeze):
    pre_errors, files, input_table, extra = preflight(freeze)
    if pre_errors:
        return {
            "disposition": "STOP_SOURCE_OR_FREEZE_MISMATCH",
            "errors": pre_errors,
            "baseline": None,
            "mutations": {},
            "input_sha256": input_table,
        }
    manifest, provenance = extra
    raw = json.loads(files["formal_raw"])
    accepted = files["accepted"]
    delivered = files["delivered_prefix"]
    baseline_errors = delivery(accepted, delivered, raw)
    path_token = b"/out/attempt"
    occurrences = accepted.count(path_token)
    mutated = accepted.replace(path_token, b"/bad/attempt", 1)
    accepted_mutation_errors = delivery(mutated, delivered, raw)
    truncated = delivered[:-1]
    prefix_mutation_errors = delivery(accepted, truncated, raw)
    accepted_sound = (
        occurrences == 1 and len(mutated) == len(accepted)
        and "ACCEPTED_JSON_INVALID" not in accepted_mutation_errors
        and "ACCEPTED_CONTENT_MISMATCH" not in accepted_mutation_errors
        and "ACCEPTED_SHA256_MISMATCH" in accepted_mutation_errors
    )
    prefix_sound = (
        len(delivered) == 23 and len(truncated) == 22
        and accepted.startswith(truncated) and len(truncated) < len(accepted)
        and "DELIVERED_BYTES_MISMATCH" in prefix_mutation_errors
        and "DELIVERED_SHA256_MISMATCH" in prefix_mutation_errors
        and "DELIVERED_NOT_STRICT_PREFIX" not in prefix_mutation_errors
    )
    errors = list(baseline_errors)
    if not accepted_sound:
        errors.append("ACCEPTED_MUTATION_GATE_FAIL")
    if not prefix_sound:
        errors.append("PREFIX_MUTATION_GATE_FAIL")
    return {
        "disposition": "PASS_FULLPATH_BYTE_AUDIT_LOCAL_AMD64_SCOPED" if not errors else "FAIL_BYTE_DELIVERY_AUDIT",
        "errors": errors,
        "input_sha256": input_table,
        "provenance": provenance,
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
                "changed_occurrences": occurrences,
                "bytes_before": len(accepted),
                "bytes_after": len(mutated),
                "errors": accepted_mutation_errors,
                "valid_json": "ACCEPTED_JSON_INVALID" not in accepted_mutation_errors,
                "rejected_by_receipt_hash": "ACCEPTED_SHA256_MISMATCH" in accepted_mutation_errors,
            },
            "delivered_prefix_23_to_22_bytes": {
                "bytes_before": len(delivered),
                "bytes_after": len(truncated),
                "errors": prefix_mutation_errors,
                "rejected_by_receipt_length": "DELIVERED_BYTES_MISMATCH" in prefix_mutation_errors,
                "rejected_by_receipt_hash": "DELIVERED_SHA256_MISMATCH" in prefix_mutation_errors,
                "invalid_json": "TRUNCATED_PREFIX_ACCEPTED" not in prefix_mutation_errors,
            },
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("preflight", "formal"), required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise SystemExit("OUTPUT_NOT_EMPTY")
    try:
        freeze = read_json(ROOT / "FREEZE.json")
        if args.phase == "preflight":
            errors, files, table, extra = preflight(freeze)
            result = {
                "schema": "issue3809-localamd64-preflight-v1",
                "phase": "preflight",
                "decision": "PASS_PREFLIGHT" if not errors else "STOP_SOURCE_OR_FREEZE_MISMATCH",
                "errors": errors,
                "input_count": len(table),
                "source_sha256": freeze.get("source_sha256"),
            }
        else:
            result = {
                "schema": "issue3809-localamd64-formal-v1",
                "phase": "formal",
                "issue": 4649,
                "allocation": ALLOCATION,
                "intake_main": INTAKE,
                "image_id": PINNED_IMAGE,
                "execution_platform": "linux/amd64",
                "python": sys.version,
                "source_sha256": freeze.get("source_sha256"),
                "freeze_sha256": sha((ROOT / "FREEZE.json").read_bytes()),
                "manifest_sha256": freeze.get("manifest_sha256"),
                **formal(freeze),
            }
        with (output / ("PREFLIGHT.json" if args.phase == "preflight" else "FORMAL.json")).open("x", encoding="utf-8") as f:
            json.dump(result, f, sort_keys=True, indent=2)
            f.write("\n")
            f.flush()
        print(json.dumps({"phase": args.phase, "decision": result.get("decision", result.get("disposition")), "errors": result.get("errors")}, sort_keys=True))
        return 0
    except Exception as error:
        result = {
            "schema": "issue3809-localamd64-runner-exception-v1",
            "phase": args.phase,
            "decision": "STOP_RUNNER_EXCEPTION",
            "exception_type": type(error).__name__,
            "exception": str(error),
        }
        target = output / ("PREFLIGHT.json" if args.phase == "preflight" else "FORMAL.json")
        if not target.exists():
            with target.open("x", encoding="utf-8") as f:
                json.dump(result, f, sort_keys=True, indent=2)
                f.write("\n")
                f.flush()
        print(json.dumps(result, sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
