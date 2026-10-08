"""Independent audit of the saved WSLc A02 records; no predecessor code runs."""

import copy
import errno
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
A02 = ROOT / "inputs" / "a02"
A02_FILES = {
    "AUDIT_ATTEMPT.json",
    "AUDITOR_CID.txt",
    "AUDITOR_CLEANUP.json",
    "CANDIDATE_CID.txt",
    "CANDIDATE_CLEANUP.json",
    "CANDIDATE_RESULT.json",
    "FREEZE.json",
    "MANIFEST.json",
    "PROTOCOL.json",
    "RAW.json",
    "README.md",
    "REPORT.md",
    "RUN_COMMAND.txt",
    "RUN_RECEIPT.json",
    "auditor.py",
    "fixture.txt",
    "probe.py",
}


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _read_json(files, name):
    try:
        return json.loads(files[name].decode("utf-8"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid A02 JSON input: {name}") from exc


def _json_after_warning(output):
    decoder = json.JSONDecoder()
    for offset, char in enumerate(output):
        if char != "{":
            continue
        try:
            value, consumed = decoder.raw_decode(output[offset:])
        except json.JSONDecodeError:
            continue
        if output[offset + consumed :].strip() == "":
            return value
    raise ValueError("candidate output has no final JSON record")


def load_saved_evidence(directory):
    directory = Path(directory)
    files = {path.name: path.read_bytes() for path in directory.iterdir() if path.is_file()}
    _need(set(files) == A02_FILES, "A02 copied file set differs from the frozen package")

    manifest = _read_json(files, "MANIFEST.json")
    digests = manifest.get("sha256")
    _need(isinstance(digests, dict), "A02 SHA-256 manifest is missing")
    _need(set(digests) == A02_FILES - {"MANIFEST.json"}, "A02 SHA-256 manifest inventory mismatch")
    for name, expected in digests.items():
        actual = hashlib.sha256(files[name]).hexdigest()
        _need(actual == expected, f"A02 evidence hash mismatch: {name}")

    return {
        "files": files,
        "manifest": manifest,
        "freeze": _read_json(files, "FREEZE.json"),
        "protocol": _read_json(files, "PROTOCOL.json"),
        "raw": _read_json(files, "RAW.json"),
        "candidate_result": _read_json(files, "CANDIDATE_RESULT.json"),
        "candidate_cid": files["CANDIDATE_CID.txt"].decode("utf-8").strip(),
        "auditor_cid": files["AUDITOR_CID.txt"].decode("utf-8").strip(),
        "candidate_cleanup": _read_json(files, "CANDIDATE_CLEANUP.json"),
        "auditor_cleanup": _read_json(files, "AUDITOR_CLEANUP.json"),
        "attempt": _read_json(files, "AUDIT_ATTEMPT.json"),
        "run": _read_json(files, "RUN_RECEIPT.json"),
    }


def _not_found_output(output, cid, role):
    _need(cid in output, f"{role} cleanup output is not bound to its exact CID")
    _need("[]" in output and ("見つかりません" in output or "not found" in output.lower()),
          f"{role} cleanup output is ambiguous")


def validate_candidate_cleanup(evidence):
    receipt = evidence["candidate_cleanup"]
    cid = evidence["candidate_cid"]
    expected_name = evidence["freeze"]["candidate_container_name"]
    _need(receipt.get("container_name") == expected_name, "candidate cleanup name mismatch")
    _need(receipt.get("container_id") == cid, "candidate cleanup CID mismatch")
    _need(receipt.get("run_requested_auto_remove") is True, "candidate cleanup lacks --rm receipt")
    _need(receipt.get("absence_verified") is True, "candidate cleanup does not prove absence")
    _need(receipt.get("global_container_list_calls") == 0, "candidate cleanup used global inventory")
    _need(receipt.get("targeted_inspect_exit_code") == 1, "candidate exact-CID inspection did not return not-found")
    _not_found_output(receipt.get("targeted_inspect_output", ""), cid, "candidate")


def validate_auditor_cleanup(evidence):
    receipt = evidence["auditor_cleanup"]
    cid = evidence["auditor_cid"]
    expected_name = evidence["freeze"]["auditor_container_name"]
    _need(receipt.get("container_name") == expected_name, "auditor cleanup name mismatch")
    _need(receipt.get("container_id") == cid, "auditor cleanup CID mismatch")
    _need(receipt.get("run_requested_auto_remove") is True, "auditor cleanup lacks --rm receipt")
    _need(receipt.get("global_container_list_calls") == 0, "auditor cleanup used global inventory")

    checks = receipt.get("targeted_inspect_checks")
    _need(isinstance(checks, list), "auditor cleanup targeted checks are missing")
    exact = [item for item in checks if item.get("attempt") == "exact CID from AUDITOR_CID.txt"]
    _need(len(exact) == 1, "auditor cleanup lacks one exact-CID inspection")
    _need(any(item.get("used_for_verification") is False for item in checks),
          "auditor cleanup does not distinguish the mistyped-ID attempt")
    exact = exact[0]
    _need(exact.get("exit_code") == 1, "auditor exact-CID inspection did not return not-found")
    _need(exact.get("absence_verified") is True, "auditor cleanup nested receipt does not prove absence")
    _not_found_output(exact.get("output", ""), cid, "auditor")


def validate_saved_records(evidence):
    manifest = evidence["manifest"]
    freeze = evidence["freeze"]
    protocol = evidence["protocol"]
    raw = evidence["raw"]
    run = evidence["run"]

    _need(manifest.get("decision") == "FAIL_AUDITOR_CONTRACT", "A02 first disposition changed")
    _need(manifest.get("audit_json") is None, "A02 manifest unexpectedly contains AUDIT.json")
    _need(freeze.get("schema") == "wslc-local-smoke-7924-a02-freeze-v1", "A02 freeze schema mismatch")
    _need(protocol.get("allocation") == freeze.get("allocation"), "A02 protocol allocation mismatch")
    _need(run.get("main_sha") == freeze.get("main_sha") == manifest.get("main_sha"),
          "A02 source-main identities disagree")

    sources = freeze.get("source_sha256")
    _need(isinstance(sources, dict), "A02 frozen source hash map missing")
    for name, digest in sources.items():
        _need(manifest["sha256"].get(name) == digest, f"A02 source identity mismatch: {name}")

    fixture_digest = hashlib.sha256(evidence["files"]["fixture.txt"]).hexdigest()
    _need(fixture_digest == sources.get("fixture.txt"), "fixture bytes differ from frozen source SHA-256")
    _need(raw == evidence["candidate_result"], "RAW.json differs from candidate result")
    _need(raw.get("fixture_sha256") == fixture_digest, "candidate fixture digest mismatch")
    _need(raw.get("expected_fixture_sha256") == fixture_digest, "candidate expected fixture digest mismatch")
    _need(raw.get("read_only_write_errno") == errno.EROFS, "read-only source did not report EROFS")
    _need(raw.get("status") == "PASS_PORTABILITY_SCOPED", "candidate result status mismatch")
    _need(_json_after_warning(run["candidate"]["combined_output"]) == raw,
          "saved candidate output differs from RAW.json")

    for record in (raw, run.get("scope", {})):
        for field in ("model_calls", "gui_calls", "external_network_calls", "game_calls", "os_input_calls"):
            if field in record:
                _need(record[field] == 0, f"nonzero out-of-scope call count: {field}")
    runtime = run.get("runtime", {})
    _need(runtime.get("docker_calls") == 0, "A02 records a Docker call")
    _need(runtime.get("global_container_list_calls") == 0, "A02 records global container inventory")
    _need(runtime.get("image_pull_policy") == "never", "A02 image pull policy changed")
    _need(freeze.get("invocations", {}).get("image_pulls") == 0, "A02 records an image pull")
    _need(freeze.get("preflight", {}).get("docker_used") is False, "A02 preflight records Docker use")

    _need(evidence["candidate_cid"] == run["candidate"].get("cid"), "candidate CID file/run receipt mismatch")
    _need(evidence["auditor_cid"] == run["auditor"].get("cid"), "auditor CID file/run receipt mismatch")
    _need(run["candidate"].get("exact_cid_absent") is True, "candidate run lacks exact-CID absence receipt")
    _need(run["auditor"].get("exact_cid_absent") is True, "auditor run lacks exact-CID absence receipt")
    validate_candidate_cleanup(evidence)
    validate_auditor_cleanup(evidence)

    attempt = evidence["attempt"]
    _need(attempt.get("status") == "FAIL_AUDITOR_CONTRACT", "A02 auditor failure status changed")
    _need(attempt.get("auditor_invocations") == 1 and attempt.get("exit_code") == 1,
          "A02 auditor invocation count/exit changed")
    _need(attempt.get("exception") == "KeyError: 'sha256'", "A02 original exception changed")
    _need(attempt.get("audit_json_created") is False, "A02 failure unexpectedly produced AUDIT.json")
    _need(attempt.get("retry_or_frozen_code_edit") is False, "A02 retry/frozen-edit boundary changed")
    _need("freeze[\"sha256\"]" in evidence["files"]["auditor.py"].decode("utf-8"),
          "A02 frozen source lacks the reported defect")
    _need("source_sha256" in freeze and "sha256" not in freeze,
          "A02 freeze no longer reproduces the recorded key mismatch")
    _need(run["candidate"].get("invocations") == 1 and run["auditor"].get("invocations") == 1,
          "A02 run counts changed")
    _need(run.get("decision", "").startswith("FAIL_AUDITOR_CONTRACT"), "A02 run decision changed")

    return {
        "a02_decision": "FAIL_AUDITOR_CONTRACT",
        "candidate_decision": "PASS_PORTABILITY_SCOPED",
        "input_files_checked": len(manifest["sha256"]),
        "candidate_stdout_matches_raw": True,
        "candidate_cleanup_shape": "top_level_absence_verified",
        "auditor_cleanup_shape": "targeted_inspect_checks[1].absence_verified",
    }


def audit_saved_evidence(directory):
    evidence = load_saved_evidence(directory)
    report = validate_saved_records(evidence)
    controls = (
        ("fixture_digest", "fixture", lambda item: _set_raw(item, "fixture_sha256", "0" * 64)),
        ("ero_fs_errno", "EROFS", lambda item: _set_raw(item, "read_only_write_errno", 13)),
        ("external_call_count", "out-of-scope", lambda item: item["run"]["scope"].__setitem__("external_network_calls", 1)),
        ("auditor_cleanup_present", "auditor cleanup", _set_auditor_present),
    )
    rejected = {}
    for name, expected_reason, mutate in controls:
        changed = copy.deepcopy(evidence)
        mutate(changed)
        try:
            validate_saved_records(changed)
        except ValueError as exc:
            message = str(exc)
            _need(expected_reason.lower() in message.lower(), f"mutation {name} rejected by wrong gate: {message}")
            rejected[name] = message
        else:
            raise ValueError(f"hostile mutation was accepted: {name}")

    report["mutation_controls_rejected"] = len(rejected)
    report["mutation_rejections"] = rejected
    report["status"] = "PASS_AUDIT_ONLY_SCOPED"
    return report


def _set_raw(evidence, field, value):
    evidence["raw"][field] = value
    evidence["candidate_result"][field] = value


def _set_auditor_present(evidence):
    exact = evidence["auditor_cleanup"]["targeted_inspect_checks"][1]
    exact["absence_verified"] = False


def verify_a04_freeze(directory):
    directory = Path(directory)
    try:
        freeze = json.loads((directory / "FREEZE.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("A04 freeze record is missing or invalid") from exc

    _need(freeze.get("schema") == "wslc-local-smoke-7924-a04-freeze-v1", "A04 freeze schema mismatch")
    _need(freeze.get("allocation") == "wslc-local-smoke-7924-a04-20261008", "A04 allocation mismatch")
    _need(freeze.get("issue") == 8455, "A04 issue identity mismatch")
    input_hashes = freeze.get("a02_input_sha256")
    blob_oids = freeze.get("a02_git_blob_oids")
    _need(isinstance(input_hashes, dict) and set(input_hashes) == A02_FILES, "A04 frozen A02 file set mismatch")
    _need(isinstance(blob_oids, dict) and set(blob_oids) == A02_FILES, "A04 Git blob inventory mismatch")
    input_directory = directory / "inputs" / "a02"
    files = {path.name: path for path in input_directory.iterdir() if path.is_file()}
    _need(set(files) == A02_FILES, "A04 copied A02 file set mismatch")
    for name, path in files.items():
        payload = path.read_bytes()
        _need(hashlib.sha256(payload).hexdigest() == input_hashes[name],
              f"A04 frozen A02 input hash mismatch: {name}")
        oid = blob_oids[name]
        _need(isinstance(oid, str) and len(oid) == 40 and all(c in "0123456789abcdef" for c in oid),
              f"A04 invalid Git blob OID: {name}")
        actual_oid = hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload).hexdigest()
        _need(actual_oid == oid, f"A04 Git blob identity mismatch: {name}")

    source_hashes = freeze.get("a04_source_sha256")
    expected_sources = {"README.md", "auditor.py", "PROTOCOL.json", "test_audit.py"}
    _need(isinstance(source_hashes, dict) and set(source_hashes) == expected_sources,
          "A04 source freeze inventory mismatch")
    for name, expected in source_hashes.items():
        actual = hashlib.sha256((directory / name).read_bytes()).hexdigest()
        _need(actual == expected, f"A04 frozen source hash mismatch: {name}")
    return {"a02_inputs_checked": len(files), "a04_sources_checked": len(source_hashes)}


def main():
    freeze = verify_a04_freeze(ROOT)
    result = audit_saved_evidence(A02)
    result["freeze"] = freeze
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
