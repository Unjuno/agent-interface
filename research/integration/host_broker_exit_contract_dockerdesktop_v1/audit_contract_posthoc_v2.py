from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


CASES = ["exit-zero", "exit-23", "timeout", "unavailable", "malformed",
         "no-request", "one-shot-two-requests"]
FAKE_SHA = "f730498c1158b55c0af45036e350090eecad7042d79c4e35be625d87e20e78eb"
ARGV = ["exec", "--ignore-user-config", "--ignore-rules", "--ephemeral", "--sandbox",
        "read-only", "--skip-git-repo-check", "--json", "--model", "gpt-5.6-luna",
        "-c", 'model_reasoning_effort="low"', "-c", "project_doc_max_bytes=0",
        "--output-schema", "/source/runtime/fake-schema.json", "-C", "/source", "-"]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def audit(study: Path, workspace: Path, output: Path, manifest_path: Path) -> dict:
    errors: list[str] = []
    holds: list[str] = []
    manifest = read_json(manifest_path)
    freeze_path = study / "FREEZE.json"
    freeze = read_json(freeze_path)
    formal = study / freeze["formal_result_path"]
    evidence = formal / "raw"

    for rel, expected in manifest["pinned_sha256"].items():
        path = study / rel
        if not path.is_file() or sha(path.read_bytes()) != expected:
            errors.append(f"posthoc pinned hash mismatch: {rel}")
    for rel, expected in freeze["sha256"].items():
        path = (study / rel.removeprefix("study/")) if rel.startswith("study/") else workspace / rel
        if not path.is_file() or sha(path.read_bytes()) != expected:
            errors.append(f"frozen source hash mismatch: {rel}")
    for rel, expected in freeze["source_git_blobs"].items():
        path = workspace / rel
        if not path.is_file() or blob(path.read_bytes()) != expected:
            errors.append(f"frozen Git blob mismatch: {rel}")

    inventory_path = evidence / "raw_inventory.json"
    summary_path = evidence / "formal_summary.json"
    inventory = read_json(inventory_path)
    actual = {p.relative_to(evidence).as_posix() for p in evidence.rglob("*")
              if p.is_file() and p.name not in {"raw_inventory.json", "formal_summary.json", "audit.json"}}
    if set(inventory) != actual:
        errors.append("raw inventory path set mismatch")
    for rel, expected in inventory.items():
        path = evidence / rel
        if not path.is_file() or sha(path.read_bytes()) != expected:
            errors.append(f"raw inventory digest mismatch: {rel}")

    summary = read_json(summary_path)
    if summary.get("case_order") != CASES or summary.get("tests_run") != 7:
        errors.append("formal case order/count mismatch")
    if summary.get("failures") != 0 or summary.get("errors") != 0:
        errors.append("characterization suite reported a test failure/error")
    if summary.get("hypothesis_disposition") != "FAIL_ZERO_EXIT_PROPAGATION":
        errors.append("formal predicted failure missing")
    expected_sources = freeze["sha256"]
    if summary.get("broker_source_sha256") != expected_sources.get("runtime/host_model_ipc_broker_v1.py"):
        errors.append("formal broker source digest mismatch")
    if summary.get("fake_source_sha256") != expected_sources.get("study/fake_codex.py"):
        errors.append("formal fake source digest mismatch")
    if summary.get("container", {}).get("machine") not in {"x86_64", "AMD64"}:
        errors.append("formal container architecture mismatch")

    verdicts: dict[str, dict] = {}
    expected_ids = {"exit-zero": ["req-zero"], "exit-23": ["req-23"],
                    "timeout": ["req-timeout"], "unavailable": ["req-missing"],
                    "malformed": ["malformed"], "no-request": [],
                    "one-shot-two-requests": ["req-A", "req-B"]}
    for name in CASES:
        path = evidence / "cases" / name / "raw.json"
        if not path.is_file():
            errors.append(f"case record missing: {name}")
            continue
        record = read_json(path)
        if record.get("case") != name or record.get("fake_source_sha256") != FAKE_SHA:
            errors.append(f"case/source identity mismatch: {name}")
        rows = record.get("requests", [])
        ids = []
        for row in rows:
            request_bytes = bytes.fromhex(row["bytes_hex"])
            if sha(request_bytes) != row.get("sha256"):
                errors.append(f"request byte hash mismatch: {name}")
            try:
                ids.append(json.loads(request_bytes).get("request_id"))
            except json.JSONDecodeError:
                ids.append("malformed")
        if ids != expected_ids[name]:
            errors.append(f"request order/identity mismatch: {name}")
        if name == "malformed":
            if len(rows) != 1 or bytes.fromhex(rows[0]["bytes_hex"]) != b"{not-json\n":
                errors.append("malformed request bytes mismatch")
        elif name != "no-request":
            decoded = [json.loads(bytes.fromhex(row["bytes_hex"])) for row in rows]
            if any(row.get("prompt") != "deterministic fake-only probe"
                   or row.get("schema") != "/repo/runtime/fake-schema.json"
                   or row.get("working") != "/repo" for row in decoded):
                errors.append(f"request field mismatch: {name}")
        receipt = record.get("broker_receipt")
        receipt_hex = record.get("broker_receipt_bytes_hex")
        if receipt is not None:
            if not receipt_hex or json.loads(bytes.fromhex(receipt_hex)) != receipt:
                errors.append(f"receipt bytes do not match decoded receipt: {name}")
            if receipt.get("boundary") != "host-local-codex-exe" or receipt.get("authority_granted") is not False:
                errors.append(f"receipt boundary/authority mismatch: {name}")
            expected_receipt_id = {"exit-zero": "req-zero", "exit-23": "req-23",
                                   "timeout": "req-timeout", "unavailable": "req-missing",
                                   "one-shot-two-requests": "req-A"}.get(name)
            if expected_receipt_id and receipt.get("request_id") != expected_receipt_id:
                errors.append(f"receipt request ID mismatch: {name}")
        if name in {"exit-zero", "exit-23", "timeout", "one-shot-two-requests"}:
            child = record.get("child")
            if not child or child.get("argv") != ARGV or child.get("stdin") != "deterministic fake-only probe\n":
                errors.append(f"fake argv/stdin provenance mismatch: {name}")
            config = record.get("execution_config", {})
            if config.get("executable_sha256") != FAKE_SHA:
                errors.append(f"executed fake digest mismatch: {name}")

        rc = record.get("process", {}).get("returncode")
        if name == "exit-zero":
            good = bool(receipt and receipt.get("returncode") == 0 and rc == 1
                        and record["observed"] == {"receipt_count": 1, "response_count": 1}
                        and record.get("child_stdout_bytes_hex") == b'{"fake":true}\n'.hex())
            verdict = "FAIL_ZERO_EXIT_PROPAGATION"
            if record.get("child", {}).get("configured_exit") != 0:
                errors.append("exit-zero fake configuration mismatch")
        elif name == "exit-23":
            good = bool(receipt and receipt.get("returncode") == 23 and rc == 23
                        and record["observed"] == {"receipt_count": 1, "response_count": 1})
            verdict = "PASS_NONZERO_PROPAGATION"
            if record.get("child", {}).get("configured_exit") != 23:
                errors.append("exit-23 fake configuration mismatch")
        elif name == "timeout":
            good = bool(receipt and receipt.get("error_class") == "TimeoutExpired"
                        and receipt.get("stop_reason") == "HOST_BROKER_SUBPROCESS_TIMEOUT"
                        and rc != 0 and record.get("response_bytes_hex") == "")
            verdict = "PASS_TYPED_TIMEOUT"
            if (record.get("execution_config", {}).get("fake_sleep_s") != 1.0
                    or record.get("execution_config", {}).get("broker_timeout_s") != 0.1):
                errors.append("timeout duration/configuration mismatch")
        elif name == "unavailable":
            good = bool(receipt and receipt.get("error_class") == "FileNotFoundError"
                        and receipt.get("stop_reason") == "HOST_BROKER_EXECUTABLE_UNAVAILABLE"
                        and rc != 0 and record.get("response_bytes_hex") == "")
            verdict = "PASS_TYPED_UNAVAILABLE"
            if (record.get("execution_config", {}).get("executable") != "/tmp/no-such-fake-codex"
                    or record.get("execution_config", {}).get("executable_sha256") is not None):
                errors.append("unavailable executable configuration mismatch")
        elif name == "malformed":
            good = bool(receipt is None and rc != 0 and record["observed"] ==
                        {"receipt_count": 0, "response_count": 0}
                        and "JSONDecodeError" in record["process"].get("stderr", ""))
            verdict = "PASS_MALFORMED_FAIL_CLOSED"
        elif name == "no-request":
            good = bool(record["process"].get("alive_at_deadline") is True and rc != 0
                        and record.get("ipc_files") == [] and record["observed"] ==
                        {"receipt_count": 0, "response_count": 0})
            verdict = "PASS_BOUNDED_NO_REQUEST_IDLE"
        else:
            good = bool(receipt and receipt.get("request_id") == "req-A"
                        and record.get("ipc_files") and "02.request.json" in record["ipc_files"]
                        and record["observed"] == {"receipt_count": 1, "response_count": 1}
                        and rc == 1)
            verdict = "PASS_ONE_SHOT_CARDINALITY"
            if record.get("child", {}).get("configured_exit") != 0:
                errors.append("one-shot fake configuration mismatch")
        if not good:
            errors.append(f"scenario assertion mismatch: {name}")
        verdicts[name] = {"verdict": verdict, "process_returncode": rc,
                          "receipt_returncode": receipt.get("returncode") if receipt else None,
                          "raw_sha256": sha(path.read_bytes())}

    run = read_json(formal / "formal_run.json")
    inspect_raw = read_json(formal / "formal-container-inspect.json")
    inspect = inspect_raw[0] if isinstance(inspect_raw, list) else inspect_raw
    state = inspect.get("State", {})
    host = inspect.get("HostConfig", {})
    mounts = {m.get("Destination"): m for m in inspect.get("Mounts", [])}
    expected_image = freeze["image"]["id"]
    if run.get("image", {}).get("id") != expected_image or inspect.get("Image") != expected_image:
        errors.append("formal container image identity mismatch")
    if run.get("container_image_id") != expected_image or inspect.get("Config", {}).get("Image") != "python:3.12-slim":
        errors.append("formal run/container image mismatch")
    if run.get("container_exit_code") != 0 or state.get("ExitCode") != 0 or state.get("OOMKilled"):
        errors.append("formal container completion/oom inspection mismatch")
    if run.get("branch") != freeze.get("branch") or run.get("base_main_commit") != freeze.get("base_main_commit"):
        errors.append("formal branch/base identity mismatch")
    if not isinstance(run.get("freeze_commit"), str) or len(run["freeze_commit"]) != 40:
        errors.append("formal frozen commit identity missing")
    if inspect.get("Path", "").endswith("python") is False or inspect.get("Args") != ["/study/test_contract.py"]:
        errors.append("formal container command mismatch")
    if host.get("NetworkMode") != "none" or host.get("ReadonlyRootfs") is not True:
        errors.append("formal isolation mode mismatch")
    if "ALL" not in host.get("CapDrop", []) or not any(
            option.split(":", 1)[0] == "no-new-privileges" for option in host.get("SecurityOpt", [])):
        errors.append("formal privilege policy mismatch")
    if host.get("PidsLimit") != 64 or host.get("Memory") != 268435456 or host.get("NanoCpus") != 1000000000:
        errors.append("formal resource bounds mismatch")
    if not all(flag in host.get("Tmpfs", {}).get("/tmp", "")
               for flag in ("rw", "exec", "nosuid", "nodev", "size=32m")):
        errors.append("formal tmpfs policy mismatch")
    if mounts.get("/study", {}).get("RW") is not False or mounts.get("/source/runtime", {}).get("RW") is not False:
        errors.append("formal source mount writeability mismatch")
    if mounts.get("/evidence", {}).get("RW") is not True:
        errors.append("formal evidence mount writeability mismatch")
    command = run.get("command", [])
    mount_specs = [command[index + 1] for index, token in enumerate(command[:-1]) if token == "--mount"]
    for destination, mount in mounts.items():
        matches = [spec for spec in mount_specs if f"target={destination}" in spec]
        if len(matches) != 1 or f"source={mount.get('Source')}" not in matches[0]:
            errors.append(f"formal command/inspect mount identity mismatch: {destination}")
        elif mount.get("RW") is False and "readonly" not in matches[0]:
            errors.append(f"formal read-only mount flag missing: {destination}")
    required_flags = ["--pull=never", "--platform", "linux/amd64", "--network", "none",
                      "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges"]
    if not all(flag in command for flag in required_flags):
        errors.append("formal docker command isolation flags mismatch")
    if run.get("docker_exit_code") is not None or run.get("docker_exit_code_observed") is not False:
        errors.append("expected explicit unobserved Docker CLI exit is not recorded")
    if run.get("wrapper_exit_code") != 1 or run.get("collection_classification") != "STOP_POWERSHELL_NATIVE_STDERR_INTERCEPTION":
        errors.append("runner collection STOP is missing/mismatched")
    if run.get("removed_after_capture") is not True or run.get("remove_exit_code") != 0:
        errors.append("formal exited container cleanup receipt mismatch")

    original_audit = read_json(formal / "audit" / "audit.json")
    if original_audit.get("status") != "AUDIT_FAIL" or original_audit.get("errors") != ["formal container did not exit cleanly"]:
        errors.append("frozen audit-01 disposition differs from its recorded single receipt finding")
    if set(original_audit.get("cases", {})) != set(CASES):
        errors.append("frozen audit-01 did not classify all seven cases")
    expected_audit01 = {"exit-zero": "FAIL_ZERO_EXIT_PROPAGATION",
                        "exit-23": "PASS_NONZERO_PROPAGATION", "timeout": "PASS_TYPED_TIMEOUT",
                        "unavailable": "PASS_TYPED_UNAVAILABLE", "malformed": "PASS_MALFORMED_FAIL_CLOSED",
                        "no-request": "PASS_BOUNDED_NO_REQUEST_IDLE",
                        "one-shot-two-requests": "PASS_ONE_SHOT_CARDINALITY"}
    for name, expected in expected_audit01.items():
        if original_audit.get("cases", {}).get(name, {}).get("verdict") != expected:
            errors.append(f"frozen audit-01 verdict mismatch: {name}")

    holds.append("Docker CLI exit receipt is unobserved; wrapper exit 1. No exit code is inferred.")
    status = ("AUDIT_PASS_RAW_CASES_HOLD_HOST_DOCKER_EXIT_UNOBSERVED"
              if not errors else "AUDIT_FAIL")
    result = {"status": status, "errors": errors, "holds": holds,
              "case_verdicts": verdicts, "tests_run": summary.get("tests_run"),
              "formal_failures": summary.get("failures"), "formal_errors": summary.get("errors"),
              "formal_hypothesis_disposition": summary.get("hypothesis_disposition"),
              "raw_file_count": len(inventory),
              "raw_inventory_sha256": sha(inventory_path.read_bytes()),
              "formal_summary_sha256": sha(summary_path.read_bytes()),
              "audit01_sha256": sha((formal / "audit" / "audit.json").read_bytes())}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--study", type=Path, default=Path("/study"))
    parser.add_argument("--workspace", type=Path, default=Path("/source"))
    parser.add_argument("--output", type=Path, default=Path("/audit-out/posthoc_audit_v2.json"))
    parser.add_argument("--manifest", type=Path, default=Path("/study/POSTHOC_AUDIT_V2_FREEZE.json"))
    args = parser.parse_args()
    result = audit(args.study, args.workspace, args.output, args.manifest)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "AUDIT_PASS_RAW_CASES_HOLD_HOST_DOCKER_EXIT_UNOBSERVED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
