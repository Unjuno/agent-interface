#!/usr/bin/env python3
"""Independent offline auditor for immutable WSLc A02 evidence."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OLD = ROOT / "predecessor_a02"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def validate_candidate(raw, fixture_sha):
    require(raw["schema"] == "wslc-local-smoke-7924-a02-v1", "candidate schema mismatch")
    require(raw["fixture_sha256"] == fixture_sha, "candidate fixture digest mismatch")
    require(raw["expected_fixture_sha256"] == fixture_sha, "candidate expected fixture mismatch")
    require(raw["status"] == "PASS_PORTABILITY_SCOPED", "candidate status mismatch")
    require(raw["read_only_write_errno"] == 30, "candidate did not receive EROFS")
    require(raw["external_network_calls"] == 0, "candidate external-call count mismatch")
    require(raw["gui_calls"] == 0 and raw["model_calls"] == 0, "unexpected GUI/model calls")
    require(raw["container_network_mode"] == "none (requested by frozen command)",
            "candidate network request record mismatch")


def validate_candidate_cleanup(cleanup, cid, frozen_name):
    require(cleanup["container_name"] == frozen_name, "candidate cleanup name mismatch")
    require(cleanup["container_id"] == cid, "candidate cleanup CID mismatch")
    require(cleanup["run_requested_auto_remove"] is True, "candidate auto-remove not requested")
    require(cleanup["targeted_inspect_exit_code"] == 1 and
            cleanup["absence_verified"] is True, "candidate scoped absence receipt mismatch")
    require(cleanup["global_container_list_calls"] == 0, "candidate used global container list")


def validate_auditor_cleanup(cleanup, cid, frozen_name):
    """A02 auditor cleanup stores absence only in its exact-CID second check."""
    require(cleanup["container_name"] == frozen_name, "auditor cleanup name mismatch")
    require(cleanup["container_id"] == cid, "auditor cleanup CID mismatch")
    require(cleanup["run_requested_auto_remove"] is True, "auditor auto-remove not requested")
    checks = cleanup["targeted_inspect_checks"]
    require(len(checks) == 2, "auditor cleanup inspect-check count mismatch")
    require(checks[0]["used_for_verification"] is False, "mistyped first check used as evidence")
    exact = checks[1]
    require(exact["attempt"] == "exact CID from AUDITOR_CID.txt", "auditor exact-CID check mismatch")
    require(exact["exit_code"] == 1 and exact["absence_verified"] is True,
            "auditor nested absence receipt mismatch")
    require(cleanup["global_container_list_calls"] == 0, "auditor used global container list")


def validate_a02(import_manifest):
    freeze = load(OLD / "FREEZE.json")
    manifest = load(OLD / "MANIFEST.json")
    receipt = load(OLD / "RUN_RECEIPT.json")
    attempt = load(OLD / "AUDIT_ATTEMPT.json")
    raw = load(OLD / "RAW.json")
    imported = import_manifest["files"]

    require(import_manifest["repository"] == "Unjuno/agent-interface" and
            import_manifest["source_branch"] == "research/wslc-local-smoke-7924-a02-20261008" and
            import_manifest["source_commit"] == "d13480e51a6116afdef2ac4797f0fedc3385cf56",
            "A02 source provenance mismatch")
    require(set(imported) == set(import_manifest["source_git_blobs"]),
            "A02 Git blob map file-set mismatch")
    require(set(imported) == {p.name for p in OLD.iterdir() if p.is_file()},
            "A02 imported package file set mismatch")
    for name, expected in imported.items():
        require(digest(OLD / name) == expected, f"A02 SHA-256 mismatch: {name}")
    require(set(manifest["sha256"]) == set(imported) - {"MANIFEST.json"},
            "A02 manifest file set mismatch")
    for name, expected in manifest["sha256"].items():
        require(imported[name] == expected, f"A02 source manifest mismatch: {name}")

    require(freeze["schema"] == "wslc-local-smoke-7924-a02-freeze-v1" and
            freeze["allocation"] == "wslc-local-smoke-7924-a02-20261008",
            "A02 freeze identity mismatch")
    for name, expected in freeze["source_sha256"].items():
        require(imported[name] == expected, f"A02 frozen source mismatch: {name}")

    candidate_cid = (OLD / "CANDIDATE_CID.txt").read_text(encoding="utf-8").strip()
    auditor_cid = (OLD / "AUDITOR_CID.txt").read_text(encoding="utf-8").strip()
    candidate_cleanup = load(OLD / "CANDIDATE_CLEANUP.json")
    auditor_cleanup = load(OLD / "AUDITOR_CLEANUP.json")
    require(freeze["candidate_container_name"] == candidate_cleanup["container_name"],
            "A02 frozen candidate name mismatch")
    require(freeze["auditor_container_name"] == auditor_cleanup["container_name"],
            "A02 frozen auditor name mismatch")

    result = load(OLD / "CANDIDATE_RESULT.json")
    require(raw == result, "A02 raw/result mismatch")
    validate_candidate(raw, digest(OLD / "fixture.txt"))
    candidate_line_found = False
    for line in receipt["candidate"]["combined_output"].splitlines():
        try:
            if json.loads(line) == raw:
                candidate_line_found = True
                break
        except json.JSONDecodeError:
            pass
    require(candidate_line_found, "A02 candidate result absent from retained combined output")

    require(receipt["candidate"]["invocations"] == 1 and
            receipt["candidate"]["exit_code"] == 0 and
            receipt["candidate"]["status"] == "PASS_PORTABILITY_SCOPED" and
            receipt["candidate"]["cid"] == candidate_cid and
            receipt["candidate"]["exact_cid_absent"] is True,
            "A02 candidate run receipt mismatch")
    validate_candidate_cleanup(candidate_cleanup, candidate_cid, freeze["candidate_container_name"])
    require(receipt["auditor"]["invocations"] == 1 and
            receipt["auditor"]["exit_code"] == 1 and
            receipt["auditor"]["status"] == "FAIL_AUDITOR_CONTRACT" and
            receipt["auditor"]["exception"] == "KeyError: 'sha256'" and
            receipt["auditor"]["cid"] == auditor_cid and
            receipt["auditor"]["exact_cid_absent"] is True,
            "A02 auditor run receipt mismatch")
    validate_auditor_cleanup(auditor_cleanup, auditor_cid, freeze["auditor_container_name"])
    require(attempt["status"] == "FAIL_AUDITOR_CONTRACT" and
            attempt["audit_json_created"] is False and
            attempt["retry_or_frozen_code_edit"] is False,
            "A02 auditor attempt mismatch")
    require(manifest["decision"] == "FAIL_AUDITOR_CONTRACT" and
            manifest["audit_json"] is None and not (OLD / "AUDIT.json").exists(),
            "A02 overall outcome/audit absence mismatch")
    return raw, candidate_cid, auditor_cid


def validate_frozen_a04():
    freeze = load(ROOT / "FREEZE.json")
    require(freeze["schema"] == "wslc-local-smoke-7924-a04-freeze-v1" and
            freeze["allocation"] == "wslc-local-smoke-7924-a04-20261008" and
            freeze["issue"] == 8455 and
            freeze["source_main_sha"] == "4864ee82c11a729c26ffdcbafc4d95c9d99e1f65",
            "A04 freeze identity mismatch")
    require(freeze["branch"] == "research/wslc-local-smoke-7924-a04-current-main-20261008",
            "A04 frozen branch mismatch")
    for name, expected in freeze["source_sha256"].items():
        require(digest(ROOT / name) == expected, f"A04 frozen input hash mismatch: {name}")

    receipt = load(ROOT / "PREFLIGHT_RECEIPT.json")
    cleanup = load(ROOT / "PREFLIGHT_CLEANUP.json")
    cid = (ROOT / "PREFLIGHT_CID.txt").read_text(encoding="utf-8").strip()
    require(receipt["status"] == "PASS_PREFLIGHT_RECEIPT_SHAPES" and
            receipt["formal_audit"] is False and receipt["exit_code"] == 0 and
            receipt["invocation"] == 1 and receipt["cid"] == cid and
            receipt["container_name"] == freeze["preflight_container_name"],
            "A04 preflight receipt mismatch")
    require(cleanup["container_id"] == cid and
            cleanup["container_name"] == freeze["preflight_container_name"] and
            cleanup["run_requested_auto_remove"] is True and
            cleanup["targeted_inspect_exit_code"] == 1 and
            cleanup["absence_verified"] is True and
            cleanup["docker_calls"] == cleanup["global_container_list_calls"] == 0,
            "A04 preflight cleanup receipt mismatch")
    require(receipt["result"] == {
        "schema": "wslc-local-smoke-7924-a04-preflight-v1",
        "status": "PASS_PREFLIGHT_RECEIPT_SHAPES",
        "candidate_absence_field": "top-level",
        "auditor_absence_field": "targeted_inspect_checks[1]",
        "a02_candidate_or_auditor_reruns": 0,
        "formal_audit": False,
    }, "A04 preflight output record mismatch")
    require(json.loads(receipt["stdout"].strip()) == receipt["result"],
            "A04 preflight stdout/result mismatch")
    return freeze


def main():
    freeze = validate_frozen_a04()
    import_manifest = load(ROOT / "A02_IMPORT_MANIFEST.json")
    raw, candidate_cid, _ = validate_a02(import_manifest)
    fixture_sha = digest(OLD / "fixture.txt")

    mutations = []
    altered = copy.deepcopy(raw)
    altered["fixture_sha256"] = "0" * 64
    mutations.append(("fixture_digest", lambda: validate_candidate(altered, fixture_sha)))
    altered = copy.deepcopy(raw)
    altered["read_only_write_errno"] = 13
    mutations.append(("write_errno", lambda: validate_candidate(altered, fixture_sha)))
    altered = copy.deepcopy(raw)
    altered["external_network_calls"] = 1
    mutations.append(("external_calls", lambda: validate_candidate(altered, fixture_sha)))
    cleanup = load(OLD / "CANDIDATE_CLEANUP.json")
    altered = copy.deepcopy(cleanup)
    altered["absence_verified"] = False
    freeze = load(OLD / "FREEZE.json")
    mutations.append(("cleanup_present", lambda: validate_candidate_cleanup(
        altered, candidate_cid, freeze["candidate_container_name"])))

    mutation_results = []
    for name, check in mutations:
        try:
            check()
        except (KeyError, TypeError, ValueError):
            mutation_results.append({"mutation": name, "rejected": True})
        else:
            raise ValueError(f"hostile mutation accepted: {name}")

    print(json.dumps({
        "schema": "wslc-local-smoke-7924-a04-audit-v1",
        "status": "PASS_AUDIT_ONLY_SCOPED",
        "a02_overall_decision": "FAIL_AUDITOR_CONTRACT",
        "a02_candidate_result": raw["status"],
        "a02_candidate_or_auditor_reruns": 0,
        "a02_imported_files_verified": len(import_manifest["files"]),
        "a02_git_blob_ids_recorded": len(import_manifest["source_git_blobs"]),
        "a04_frozen_inputs_verified": len(freeze["source_sha256"]),
        "preflight_shape_smoke_verified": True,
        "candidate_cleanup_schema": "top-level absence_verified",
        "auditor_cleanup_schema": "targeted_inspect_checks[1].absence_verified",
        "mutations_rejected": mutation_results,
        "docker_calls": 0,
        "global_container_list_calls": 0,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
