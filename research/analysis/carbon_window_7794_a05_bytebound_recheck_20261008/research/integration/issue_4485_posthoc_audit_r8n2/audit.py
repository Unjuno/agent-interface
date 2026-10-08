#!/usr/bin/env python3
"""Independent, stdlib-only reconstruction of #4485 retained raw bytes."""
import hashlib
import json
from pathlib import Path

SPEC = json.loads(Path("/audit/FREEZE.json").read_text())
STUDY = Path("/study")
REPO = Path("/repo")
RAW = STUDY / SPEC["source"]["path"] / SPEC["formal_raw"]["path"]
errors = []
rows = []


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        errors.append(message)


def git_blob(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


original_freeze_path = STUDY / SPEC["source"]["path"] / "FREEZE.json"
original_auditor_path = STUDY / SPEC["source"]["path"] / "audit.py"
original_report_path = RAW / "AUDIT.json"
require(digest(original_freeze_path) == SPEC["source"]["original_freeze_sha256"], "original freeze digest mismatch")
require(digest(original_auditor_path) == SPEC["source"]["original_auditor_sha256"], "original auditor digest mismatch")
require(digest(original_report_path) == SPEC["source"]["original_audit_report_sha256"], "original audit report digest mismatch")

old_freeze = load(original_freeze_path)
require(old_freeze["allocation"] == "issue3924-orbstac-broker-contract-v2-20260926-01", "wrong source allocation")
require(old_freeze["timeout_case"]["fake_sleep_s"] == SPEC["formal_raw"]["timeout_fake_sleep_s"], "frozen timeout sleep differs from audit freeze")

source_paths = {
    "broker": REPO / "runtime/host_model_ipc_broker_v1.py",
    "test": REPO / "runtime/test_host_model_ipc_broker_v1.py",
    "fake": STUDY / SPEC["source"]["path"] / "fake_codex.py",
}
source_expected = {
    "broker": (SPEC["source"]["broker_sha256"], old_freeze["source"]["broker_git_blob"]),
    "test": (SPEC["source"]["test_sha256"], old_freeze["source"]["existing_test_git_blob"]),
    "fake": (SPEC["source"]["fake_sha256"], None),
}
for label, path in source_paths.items():
    expected_sha, expected_blob = source_expected[label]
    require(path.is_file(), f"missing {label} source")
    if path.is_file():
        require(digest(path) == expected_sha, f"{label} SHA-256 mismatch")
        if expected_blob is not None:
            require(git_blob(path) == expected_blob, f"{label} Git blob mismatch")

container = load(RAW / "container.json")
require(container["allocation"] == old_freeze["allocation"], "container allocation mismatch")
require(container["image_id"] == SPEC["container"]["image_id"], "container image mismatch")
require(container["platform"] == "linux", "container platform mismatch")
require(container["uname"][-1] == "aarch64", "container architecture mismatch")
require(container["real_codex_found"] is False, "real Codex unexpectedly present")
require(container["broker_sha256"] == SPEC["source"]["broker_sha256"], "container broker source mismatch")
require(container["test_sha256"] == SPEC["source"]["test_sha256"], "container test source mismatch")
require(container["fake_sha256"] == SPEC["source"]["fake_sha256"], "container fake source mismatch")

# Recompute the original report's immutable input manifest without invoking it.
prior_audit = load(original_report_path)
actual_manifest = {
    path.relative_to(RAW).as_posix(): digest(path)
    for path in sorted(RAW.rglob("*"))
    if path.is_file() and path != original_report_path
}
require(prior_audit["allocation"] == old_freeze["allocation"], "original audit allocation mismatch")
require(prior_audit["files_hashed"] == SPEC["formal_raw"]["manifest_file_count"], "original manifest count mismatch")
require(len(actual_manifest) == SPEC["formal_raw"]["manifest_file_count"], "recomputed raw file count mismatch")
require(prior_audit["sha256"] == actual_manifest, "original audit raw manifest does not match retained bytes")
require(prior_audit["decision"] == "STOP_AUDIT_PROVENANCE", "original audit disposition changed")
require(prior_audit["contract_errors"] == [], "original audit contract error list unexpected")
require(prior_audit["provenance_errors"] == ["timeout: expected recorded sleeping fake invocation"], "original audit provenance error changed")

case_names = SPEC["formal_raw"]["case_names"]
for case in case_names:
    folder = RAW / case
    process_path = folder / "process.json"
    require(process_path.is_file(), f"{case}: missing process record")
    if not process_path.is_file():
        continue
    process = load(process_path)
    requests = sorted(folder.glob("*.request.json"))
    responses = sorted(folder.glob("*.response.jsonl"))
    receipts = sorted(folder.glob("*.broker.json"))
    invocations = sorted(folder.glob("invocation-*.json"))
    request_ids = [load(path)["request_id"] for path in requests]
    row = {"case": case, "process_returncode": process["returncode"], "request_ids": request_ids}

    if case == "one-shot-idle":
        require(process["returncode"] == SPEC["formal_raw"]["idle_harness_exit"] and process["killed_by_harness"] is True, "one-shot-idle: harness-bound process record mismatch")
        require(not requests and not responses and not receipts and not invocations, "one-shot-idle: unexpected request/response/receipt/invocation")
    elif case == "malformed":
        require(request_ids == ["malformed"], "malformed: request ID mismatch")
        require(process["returncode"] == 1 and process["killed_by_harness"] is False, "malformed: process outcome mismatch")
        require("KeyError" in process["stderr"], "malformed: expected exception absent")
        require(not responses and not receipts and not invocations, "malformed: unexpected response/receipt/invocation")
    elif case == "two-queued":
        require(request_ids == ["queued-a", "queued-b"], "two-queued: request set mismatch")
        require(len(receipts) == len(responses) == len(invocations) == 1, "two-queued: expected exactly one receipt/response/invocation")
        require(receipts[0].name == "queued-a.broker.json" and responses[0].name == "queued-a.response.jsonl", "two-queued: first queued item mismatch")
        receipt = load(receipts[0])
        invocation = load(invocations[0])
        require(receipt["request_id"] == "queued-a" and receipt["returncode"] == 0, "two-queued: receipt mismatch")
        require(invocation["configured_exit"] == 0 and invocation["stdin"] == "fake\n", "two-queued: invocation mismatch")
        require(process["returncode"] == 1 and process["killed_by_harness"] is False, "two-queued: process outcome mismatch")
        row["served_request"] = receipt["request_id"]
        row["queued_b_has_no_receipt"] = True
    else:
        require(request_ids == [case], f"{case}: request ID mismatch")
        require(len(receipts) == len(responses) == 1, f"{case}: expected one receipt and response")
        if len(receipts) == 1 and len(responses) == 1:
            receipt = load(receipts[0])
            require(receipt["request_id"] == case, f"{case}: receipt ID mismatch")
            require(receipt["boundary"] == "host-local-codex-exe" and receipt["authority_granted"] is False, f"{case}: boundary/authority mismatch")
            row["receipt_returncode"] = receipt.get("returncode")
            row["stop_reason"] = receipt.get("stop_reason")
            if case == "exit0":
                require(receipt.get("returncode") == 0 and process["returncode"] == 1, "exit0: retained child/broker return codes differ from expected observation")
                require(responses[0].read_bytes() == b'{"ok":true}', "exit0: response bytes mismatch")
                require(len(invocations) == 1, "exit0: invocation count mismatch")
                if len(invocations) == 1:
                    invocation = load(invocations[0])
                    require(invocation["configured_exit"] == 0 and invocation["stdin"] == "fake\n", "exit0: fake invocation mismatch")
                row["child_broker_exit_discrepancy_observed"] = True
            elif case == "exit23":
                require(receipt.get("returncode") == 23 and process["returncode"] == 23, "exit23: return-code mismatch")
                require(len(invocations) == 1 and load(invocations[0])["configured_exit"] == 23, "exit23: fake invocation mismatch")
            elif case == "timeout":
                require(receipt.get("returncode") is None and receipt.get("stop_reason") == "HOST_BROKER_SUBPROCESS_TIMEOUT", "timeout: typed receipt mismatch")
                require(process["returncode"] == 1, "timeout: broker process return code mismatch")
                require(len(invocations) == 1, "timeout: invocation count mismatch")
                if len(invocations) == 1:
                    invocation = load(invocations[0])
                    require(invocation.get("sleep_s") == old_freeze["timeout_case"]["fake_sleep_s"], "timeout: retained fake sleep differs from original preregistration")
                    row["fake_sleep_s"] = invocation.get("sleep_s")
            elif case == "unavailable":
                require(receipt.get("returncode") is None and receipt.get("stop_reason") == "HOST_BROKER_EXECUTABLE_UNAVAILABLE", "unavailable: typed receipt mismatch")
                require(process["returncode"] == 1 and not invocations, "unavailable: unexpected process/invocation outcome")
    rows.append(row)

# Confirm the precise frozen auditor mismatch without importing or running it.
auditor_text = original_auditor_path.read_text()
require('get("sleep_s") != 0.3' in auditor_text, "frozen auditor mismatch expression not found at pinned source")
timeout_invocation = load(RAW / "timeout/invocation-01.json")
require(timeout_invocation["sleep_s"] == old_freeze["timeout_case"]["fake_sleep_s"] == 2.0, "timeout source/raw comparison mismatch")

decision = "PASS_POSTHOC_RAW_AUDIT" if not errors else "FAIL_POSTHOC_RAW_RECONSTRUCTION"
posthoc_source_hashes = {
    label: {
        "sha256": digest(path),
        "git_blob": git_blob(path) if label in {"broker", "test"} else None,
    }
    for label, path in source_paths.items()
    if path.is_file()
}
report = {
    "schema": "issue4485_posthoc_raw_audit_report_r8n2",
    "allocation": SPEC["allocation"],
    "decision": decision,
    "original_issue_4485_decision": SPEC["original_decision_immutable"],
    "original_decision_changed": False,
    "auditor_invoked": False,
    "broker_invoked": False,
    "fake_invoked": False,
    "model_calls": 0,
    "raw_manifest_files_recomputed": len(actual_manifest),
    "raw_file_sha256": actual_manifest,
    "raw_manifest_sha256": hashlib.sha256(json.dumps(actual_manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    "source_hashes": posthoc_source_hashes,
    "posthoc_auditor_sha256": digest(Path("/audit/audit.py")),
    "posthoc_freeze_sha256": digest(Path("/audit/FREEZE.json")),
    "source_and_provenance_errors": errors,
    "rows": rows,
    "scope": "Posthoc byte-level reconstruction only; not a retroactive formal decision or product claim.",
}
out = Path("/evidence/AUDIT.json")
out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
print(f"OBSTAC_POSTHOC_AUDIT {decision} cases={len(rows)} raw_files={len(actual_manifest)} errors={len(errors)} original_decision_unchanged=true")
if errors:
    raise SystemExit(2)
