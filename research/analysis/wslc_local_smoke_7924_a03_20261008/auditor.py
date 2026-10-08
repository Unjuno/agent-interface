#!/usr/bin/env python3
"""Offline independent audit of immutable WSLc A02 evidence."""
import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OLD = ROOT / "predecessor_a02"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def validate_candidate(raw, fixture_hash):
    require(raw["fixture_sha256"] == raw["expected_fixture_sha256"] == fixture_hash,
            "fixture digest mismatch")
    require(raw["status"] == "PASS_PORTABILITY_SCOPED", "candidate status mismatch")
    require(raw["read_only_write_errno"] == 30, "read-only write was not EROFS")
    require(raw["external_network_calls"] == 0, "candidate reports external calls")
    require(raw["gui_calls"] == raw["model_calls"] == 0, "unexpected GUI/model calls")
    require(raw["container_network_mode"] == "none (requested by frozen command)",
            "network mode record mismatch")


def validate_cleanup(cleanup, cid_value, role):
    require(cleanup["container_id"] == cid_value, f"{role} exact CID mismatch")
    require(cleanup["run_requested_auto_remove"] is True and
            cleanup["absence_verified"] is True and
            cleanup["global_container_list_calls"] == 0,
            f"{role} scoped cleanup receipt mismatch")


def validate_record(record, imported):
    """Raise on any inconsistency; returns only after validating saved bytes."""
    freeze = read_json(OLD / "FREEZE.json")
    manifest = read_json(OLD / "MANIFEST.json")
    receipt = read_json(OLD / "RUN_RECEIPT.json")
    attempt = read_json(OLD / "AUDIT_ATTEMPT.json")
    raw = read_json(OLD / "RAW.json")

    require(set(imported) == set(p.name for p in OLD.iterdir() if p.is_file()),
            "A02 imported file set differs")
    for name, digest in imported.items():
        require(sha256(OLD / name) == digest, f"A02 import digest mismatch: {name}")
    require(set(manifest["sha256"]) == set(imported) - {"MANIFEST.json"},
            "A02 manifest file set differs")
    for name, digest in manifest["sha256"].items():
        require(imported[name] == digest, f"A02 manifest/import mismatch: {name}")

    require(freeze["schema"] == "wslc-local-smoke-7924-a02-freeze-v1",
            "A02 freeze schema mismatch")
    require(freeze["allocation"] == "wslc-local-smoke-7924-a02-20261008",
            "A02 allocation mismatch")
    for name, digest in freeze["source_sha256"].items():
        require(imported[name] == digest, f"A02 frozen source mismatch: {name}")
    require(freeze["candidate_container_name"] == record["candidate_cleanup"]["container_name"],
            "candidate name differs from freeze")
    require(freeze["auditor_container_name"] == record["auditor_cleanup"]["container_name"],
            "auditor name differs from freeze")

    result = read_json(OLD / "CANDIDATE_RESULT.json")
    require(result == raw, "candidate result and raw differ")
    require(record["candidate_result"] == raw, "audited candidate result differs")
    fixture_hash = sha256(OLD / "fixture.txt")
    validate_candidate(raw, fixture_hash)

    candidate_line = None
    for line in receipt["candidate"]["combined_output"].splitlines():
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if parsed == raw:
            candidate_line = line
            break
    require(candidate_line is not None, "candidate result absent from saved output")
    require(receipt["candidate"]["exit_code"] == 0 and
            receipt["candidate"]["status"] == "PASS_PORTABILITY_SCOPED" and
            receipt["candidate"]["invocations"] == 1,
            "candidate run receipt mismatch")
    require(receipt["auditor"]["exit_code"] == 1 and
            receipt["auditor"]["status"] == "FAIL_AUDITOR_CONTRACT" and
            receipt["auditor"]["invocations"] == 1 and
            receipt["auditor"]["exception"] == "KeyError: 'sha256'",
            "original auditor failure receipt mismatch")
    require(attempt["status"] == "FAIL_AUDITOR_CONTRACT" and
            attempt["audit_json_created"] is False and
            attempt["retry_or_frozen_code_edit"] is False,
            "saved auditor attempt mismatch")
    require(record["audit_absent"] is True, "A02 unexpectedly has an audit artifact")

    for role, cid_field, cleanup_field in (
            ("candidate", "candidate_cid", "candidate_cleanup"),
            ("auditor", "auditor_cid", "auditor_cleanup")):
        cid = (OLD / ("CANDIDATE_CID.txt" if role == "candidate" else "AUDITOR_CID.txt"))
        cid_value = cid.read_text(encoding="utf-8").strip()
        receipt_role = receipt[role]
        cleanup = record[cleanup_field]
        require(cid_value == receipt_role["cid"], f"{role} run receipt CID mismatch")
        validate_cleanup(cleanup, cid_value, role)
        require(receipt_role["auto_remove_requested"] is True and
                receipt_role["exact_cid_absent"] is True,
                f"{role} run cleanup receipt mismatch")
    require(record["candidate_cleanup"]["targeted_inspect_exit_code"] == 1,
            "candidate targeted inspect result mismatch")
    audit_checks = record["auditor_cleanup"]["targeted_inspect_checks"]
    require(len(audit_checks) == 2 and
            audit_checks[1]["attempt"] == "exact CID from AUDITOR_CID.txt" and
            audit_checks[1]["exit_code"] == 1 and
            audit_checks[1]["absence_verified"] is True,
            "auditor exact-CID cleanup check mismatch")
    require(record["candidate_cid"] == receipt["candidate"]["cid"] and
            record["auditor_cid"] == receipt["auditor"]["cid"],
            "A02 CID record differs")
    return True


def main():
    import_manifest = read_json(ROOT / "A02_IMPORT_MANIFEST.json")
    imported = import_manifest["files"]
    require(import_manifest["repository"] == "Unjuno/agent-interface" and
            import_manifest["source_branch"] == "research/wslc-local-smoke-7924-a02-20261008" and
            import_manifest["source_commit"] == "d13480e51a6116afdef2ac4797f0fedc3385cf56" and
            set(import_manifest["source_git_blobs"]) == set(imported),
            "A02 import provenance map mismatch")
    record = {
        "candidate_result": read_json(OLD / "CANDIDATE_RESULT.json"),
        "candidate_cid": (OLD / "CANDIDATE_CID.txt").read_text(encoding="utf-8").strip(),
        "auditor_cid": (OLD / "AUDITOR_CID.txt").read_text(encoding="utf-8").strip(),
        "candidate_cleanup": read_json(OLD / "CANDIDATE_CLEANUP.json"),
        "auditor_cleanup": read_json(OLD / "AUDITOR_CLEANUP.json"),
        "audit_absent": not (OLD / "AUDIT.json").exists(),
    }
    validate_record(record, imported)

    mutations = []
    baseline_candidate = copy.deepcopy(record["candidate_result"])
    fixture_hash = sha256(OLD / "fixture.txt")
    mutations_to_check = []
    bad_digest = copy.deepcopy(baseline_candidate)
    bad_digest["fixture_sha256"] = bad_digest["expected_fixture_sha256"] = "digest"
    mutations_to_check.append(("fixture digest", lambda: validate_candidate(bad_digest, fixture_hash)))
    bad_errno = copy.deepcopy(baseline_candidate)
    bad_errno["read_only_write_errno"] = 13
    mutations_to_check.append(("write errno", lambda: validate_candidate(bad_errno, fixture_hash)))
    bad_network = copy.deepcopy(baseline_candidate)
    bad_network["external_network_calls"] = 1
    mutations_to_check.append(("external calls", lambda: validate_candidate(bad_network, fixture_hash)))
    bad_cleanup = copy.deepcopy(record["candidate_cleanup"])
    bad_cleanup["absence_verified"] = False
    mutations_to_check.append(("cleanup present", lambda: validate_cleanup(
        bad_cleanup, record["candidate_cid"], "candidate")))
    for label, check in mutations_to_check:
        rejected = False
        try:
            check()
        except (AssertionError, KeyError, TypeError, ValueError):
            rejected = True
        require(rejected, f"mutation was not rejected: {label}")
        mutations.append({"mutation": label, "rejected": True})

    print(json.dumps({
        "schema": "wslc-local-smoke-7924-a03-audit-v1",
        "status": "PASS_AUDIT_ONLY_SCOPED",
        "a02_overall_decision": "FAIL_AUDITOR_CONTRACT",
        "a02_candidate_result": "PASS_PORTABILITY_SCOPED",
        "a02_candidate_or_auditor_reruns": 0,
        "a02_imported_files_verified": len(imported),
        "saved_run_receipt_verified": True,
        "scoped_cleanup_receipts_verified": 2,
        "mutations_rejected": mutations,
        "docker_calls": 0,
        "global_container_list_calls": 0,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
