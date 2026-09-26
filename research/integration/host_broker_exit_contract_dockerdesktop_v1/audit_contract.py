from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def audit(evidence: Path, output: Path, study: Path, workspace: Path) -> dict:
    errors: list[str] = []
    freeze_path = study / "FREEZE.json"
    if not freeze_path.is_file():
        return {"status": "AUDIT_FAIL", "errors": ["FREEZE.json missing"]}
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    for rel, expected in freeze.get("sha256", {}).items():
        path = (study / rel.split("study/", 1)[-1]) if rel.startswith("study/") else workspace / rel
        if not path.is_file() or digest(path.read_bytes()) != expected:
            errors.append(f"frozen source digest mismatch: {rel}")
    for rel, expected in freeze.get("source_git_blobs", {}).items():
        path = workspace / rel
        if not path.is_file() or git_blob_id(path.read_bytes()) != expected:
            errors.append(f"source Git blob identity mismatch: {rel}")
    formal_root = study / freeze.get("formal_result_path", "")
    run_meta_path = formal_root / "formal_run.json"
    inspect_path = formal_root / "formal-container-inspect.json"
    if not run_meta_path.is_file() or not inspect_path.is_file():
        errors.append("Docker Desktop formal run metadata/inspection missing")
    else:
        run_meta = json.loads(run_meta_path.read_text(encoding="utf-8"))
        raw_inspect = json.loads(inspect_path.read_text(encoding="utf-8"))
        inspect = raw_inspect[0] if isinstance(raw_inspect, list) else raw_inspect
        host = inspect.get("HostConfig", {})
        mounts = {m.get("Destination"): m for m in inspect.get("Mounts", [])}
        expected_engine = freeze.get("engine", {})
        expected_image = freeze.get("image", {})
        if run_meta.get("context") != "desktop-linux": errors.append("Docker context mismatch")
        if run_meta.get("branch") != freeze.get("branch") or run_meta.get("base_main_commit") != freeze.get("base_main_commit"):
            errors.append("formal branch/base identity mismatch")
        if not isinstance(run_meta.get("freeze_commit"), str) or len(run_meta["freeze_commit"]) != 40:
            errors.append("formal freeze commit identity missing")
        if run_meta.get("engine") != {"version": expected_engine.get("version"), "os": "linux", "architecture": "x86_64"}:
            errors.append("Docker Desktop engine metadata mismatch")
        if run_meta.get("image", {}).get("id") != expected_image.get("id"):
            errors.append("Docker Desktop image metadata mismatch")
        if run_meta.get("docker_exit_code") != 0 or run_meta.get("inspect_exit_code") != 0 or run_meta.get("container_exit_code") != 0:
            errors.append("formal container did not exit cleanly")
        if run_meta.get("removed_after_capture") is not True or run_meta.get("remove_exit_code") != 0:
            errors.append("formal container cleanup after evidence capture failed")
        required_command = ["--pull=never", "--platform", "linux/amd64", "--network", "none",
                            "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges"]
        command = run_meta.get("command", [])
        if not all(token in command for token in required_command):
            errors.append("formal Docker command does not match frozen isolation policy")
        if run_meta.get("container_image_id") != expected_image.get("id") or inspect.get("Image") != expected_image.get("id"):
            errors.append("formal container image identity mismatch")
        if inspect.get("State", {}).get("ExitCode") != 0 or inspect.get("Config", {}).get("Image") != "python:3.12-slim":
            errors.append("formal container state/image tag mismatch")
        if not str(inspect.get("Path", "")).endswith("python") or inspect.get("Args") != ["/study/test_contract.py"]:
            errors.append("formal container entrypoint/command mismatch")
        if host.get("NetworkMode") != "none" or host.get("ReadonlyRootfs") is not True:
            errors.append("formal container network/rootfs policy mismatch")
        if "ALL" not in host.get("CapDrop", []) or not any(
                option.split(":", 1)[0] == "no-new-privileges" for option in host.get("SecurityOpt", [])):
            errors.append("formal container privilege policy mismatch")
        if host.get("PidsLimit") != 64 or host.get("Memory") != 268435456 or host.get("NanoCpus") != 1000000000:
            errors.append("formal container resource bounds mismatch")
        tmpfs = host.get("Tmpfs", {}).get("/tmp", "")
        if not all(flag in tmpfs for flag in ("rw", "exec", "nosuid", "nodev", "size=32m")):
            errors.append("formal container tmpfs policy mismatch")
        if mounts.get("/study", {}).get("RW") is not False or mounts.get("/source/runtime", {}).get("RW") is not False:
            errors.append("formal source mount is not read-only")
        if mounts.get("/evidence", {}).get("RW") is not True:
            errors.append("formal evidence mount is not writable as declared")
        transcript = formal_root / run_meta.get("transcript_file", "")
        if not transcript.is_file() or not transcript.read_text(encoding="utf-8").strip():
            errors.append("formal Docker stdout transcript missing/empty")
    inventory_path = evidence / "raw_inventory.json"
    if not inventory_path.is_file():
        return {"status": "AUDIT_FAIL", "errors": ["raw_inventory.json missing"]}
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    actual_files = {p.relative_to(evidence).as_posix() for p in evidence.rglob("*") if p.is_file()
                    and p.name not in {"raw_inventory.json", "formal_summary.json", "audit.json"}}
    if set(inventory) != actual_files:
        errors.append("raw evidence inventory path set mismatch")
    for name, expected in inventory.items():
        path = evidence / name
        if not path.is_file() or digest(path.read_bytes()) != expected:
            errors.append(f"raw evidence digest mismatch: {name}")
    summary = json.loads((evidence / "formal_summary.json").read_text(encoding="utf-8"))
    expected_cases = ["exit-zero", "exit-23", "timeout", "unavailable", "malformed", "no-request",
                      "one-shot-two-requests"]
    if summary.get("case_order") != expected_cases:
        errors.append("case order mismatch")
    if summary.get("broker_source_sha256") != freeze.get("sha256", {}).get("runtime/host_model_ipc_broker_v1.py"):
        errors.append("formal broker source is not the frozen source")
    if summary.get("fake_source_sha256") != freeze.get("sha256", {}).get("study/fake_codex.py"):
        errors.append("formal fake program is not the frozen fake source")
    if summary.get("container", {}).get("machine") not in {"x86_64", "AMD64"}:
        errors.append("formal container architecture is not x86_64")
    cases = {}
    for name in expected_cases:
        path = evidence / "cases" / name / "raw.json"
        if not path.is_file():
            errors.append(f"missing case: {name}")
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("case") != name:
            errors.append(f"case identity mismatch: {name}")
            continue
        receipt = record.get("broker_receipt")
        proc = record.get("process", {}).get("returncode")
        config = record.get("execution_config", {})
        if record.get("fake_source_sha256") != freeze.get("sha256", {}).get("study/fake_codex.py"):
            errors.append(f"fake program digest mismatch in {name}")
        if name not in {"malformed", "no-request"}:
            request_rows = record.get("requests", [])
            if not request_rows or any(digest(bytes.fromhex(row["bytes_hex"])) != row["sha256"] for row in request_rows):
                errors.append(f"request bytes/hash invalid in {name}")
        if name == "malformed":
            rows = record.get("requests", [])
            if len(rows) != 1 or digest(bytes.fromhex(rows[0]["bytes_hex"])) != rows[0]["sha256"] or bytes.fromhex(rows[0]["bytes_hex"]) != b"{not-json\n":
                errors.append("malformed request bytes mismatch")
        elif name != "no-request":
            expected_ids = {"exit-zero": ["req-zero"], "exit-23": ["req-23"],
                            "timeout": ["req-timeout"], "unavailable": ["req-missing"],
                            "one-shot-two-requests": ["req-A", "req-B"]}[name]
            decoded = [json.loads(bytes.fromhex(row["bytes_hex"])) for row in record.get("requests", [])]
            if [row.get("request_id") for row in decoded] != expected_ids or any(
                    row.get("prompt") != "deterministic fake-only probe"
                    or row.get("schema") != "/repo/runtime/fake-schema.json"
                    or row.get("working") != "/repo" for row in decoded):
                errors.append(f"request contents mismatch in {name}")
        if name in {"exit-zero", "exit-23", "timeout", "one-shot-two-requests"}:
            child = record.get("child")
            if not child or child.get("stdin") != "deterministic fake-only probe\n":
                errors.append(f"fake child input missing/mismatched in {name}")
            else:
                expected_argv = ["exec", "--ignore-user-config", "--ignore-rules", "--ephemeral",
                                 "--sandbox", "read-only", "--skip-git-repo-check", "--json", "--model",
                                 "gpt-5.6-luna", "-c", 'model_reasoning_effort="low"', "-c",
                                 "project_doc_max_bytes=0", "--output-schema", "/source/runtime/fake-schema.json",
                                 "-C", "/source", "-"]
                if child.get("argv") != expected_argv:
                    errors.append(f"broker argv mismatch in {name}")
            if child and config.get("executable_sha256") != freeze.get("sha256", {}).get("study/fake_codex.py"):
                errors.append(f"executed file is not the frozen fake in {name}")
            if name != "timeout" and record.get("broker_stderr_text") != "fake-stderr\n":
                errors.append(f"fake child stderr mismatch in {name}")
        if name == "timeout" and (record.get("child_stdout_bytes_hex") != "" or "timed out after" not in record.get("broker_stderr_text", "")):
            errors.append("timeout output/receipt mismatch")
        if name in {"exit-zero", "exit-23", "one-shot-two-requests"}:
            if record.get("child_stdout_bytes_hex") != '{"fake":true}\n'.encode().hex():
                errors.append(f"fake child stdout mismatch in {name}")
        if name in {"timeout", "unavailable"} and (record.get("response_bytes_hex") != "" or record.get("observed", {}).get("response_count") != 1):
            errors.append(f"typed failure response bytes/count mismatch in {name}")
        if name in {"exit-zero", "exit-23", "one-shot-two-requests"} and record.get("observed", {}).get("response_count") != 1:
            errors.append(f"successful fake response count mismatch in {name}")
        if receipt:
            raw_receipt = record.get("broker_receipt_bytes_hex")
            if not raw_receipt or json.loads(bytes.fromhex(raw_receipt)) != receipt:
                errors.append(f"broker receipt bytes mismatch in {name}")
        if name in {"exit-zero", "exit-23", "timeout", "unavailable", "one-shot-two-requests"}:
            expected_id = {"exit-zero": "req-zero", "exit-23": "req-23", "timeout": "req-timeout",
                           "unavailable": "req-missing", "one-shot-two-requests": "req-A"}[name]
            if not receipt or receipt.get("request_id") != expected_id:
                errors.append(f"request/receipt identity mismatch in {name}")
        if name == "exit-zero" and (config.get("fake_exit") != 0 or config.get("broker_timeout_s") != 2.0):
            errors.append("exit-zero config mismatch")
        if name == "exit-23" and config.get("fake_exit") != 23:
            errors.append("exit-23 config mismatch")
        if name == "timeout" and (config.get("fake_sleep_s") != 1.0 or config.get("broker_timeout_s") != 0.1):
            errors.append("timeout config mismatch")
        if name == "unavailable" and config.get("executable") != "/tmp/no-such-fake-codex":
            errors.append("unavailable executable mismatch")
        if name == "unavailable" and config.get("executable_sha256") is not None:
            errors.append("unavailable executable unexpectedly has a file digest")
        expected_fake_config = {"exit-zero": (0, 0.0), "exit-23": (23, 0.0),
                                "timeout": (0, 1.0), "one-shot-two-requests": (0, 0.0)}
        if name in expected_fake_config:
            expected_exit, expected_sleep = expected_fake_config[name]
            if not record.get("child") or record["child"].get("configured_exit") != expected_exit or record["child"].get("configured_sleep_s") != expected_sleep:
                errors.append(f"fake executable configuration mismatch in {name}")
        if name == "no-request" and config.get("idle_observation_s") != 0.2:
            errors.append("no-request observation duration mismatch")
        if name == "exit-zero":
            verdict = "FAIL_ZERO_EXIT_PROPAGATION" if receipt and receipt.get("returncode") == 0 and proc != 0 else "UNEXPECTED"
            if verdict != "FAIL_ZERO_EXIT_PROPAGATION": errors.append("exit-zero behavior differs from frozen prediction")
        elif name == "exit-23":
            verdict = "PASS_NONZERO_PROPAGATION" if receipt and receipt.get("returncode") == 23 and proc == 23 else "FAIL"
            if verdict != "PASS_NONZERO_PROPAGATION": errors.append("exit-23 mismatch")
        elif name == "timeout":
            verdict = "PASS_TYPED_TIMEOUT" if receipt and receipt.get("error_class") == "TimeoutExpired" and receipt.get("stop_reason") == "HOST_BROKER_SUBPROCESS_TIMEOUT" and proc != 0 else "FAIL"
            if verdict != "PASS_TYPED_TIMEOUT": errors.append("timeout classification mismatch")
        elif name == "unavailable":
            verdict = "PASS_TYPED_UNAVAILABLE" if receipt and receipt.get("error_class") == "FileNotFoundError" and receipt.get("stop_reason") == "HOST_BROKER_EXECUTABLE_UNAVAILABLE" and proc != 0 else "FAIL"
            if verdict != "PASS_TYPED_UNAVAILABLE": errors.append("unavailable classification mismatch")
        elif name == "malformed":
            verdict = "PASS_MALFORMED_FAIL_CLOSED" if proc != 0 and receipt is None and record["observed"]["response_count"] == 0 and "JSONDecodeError" in record["process"]["stderr"] else "FAIL"
            if verdict != "PASS_MALFORMED_FAIL_CLOSED": errors.append("malformed request mismatch")
        elif name == "no-request":
            verdict = "PASS_BOUNDED_NO_REQUEST_IDLE" if record["process"].get("alive_at_deadline") and record["ipc_files"] == [] and record["execution_config"].get("idle_observation_s") == 0.2 else "FAIL"
            if verdict != "PASS_BOUNDED_NO_REQUEST_IDLE": errors.append("no-request idle mismatch")
        else:
            verdict = "PASS_ONE_SHOT_CARDINALITY" if receipt and receipt.get("request_id") == "req-A" and record["observed"] == {"receipt_count": 1, "response_count": 1} and "02.request.json" in record["ipc_files"] else "FAIL"
            if verdict != "PASS_ONE_SHOT_CARDINALITY": errors.append("one-shot cardinality mismatch")
        cases[name] = {"verdict": verdict, "process_returncode": proc,
                       "receipt_returncode": receipt.get("returncode") if receipt else None,
                       "raw_sha256": digest(path.read_bytes())}
    if summary.get("tests_run") != 7 or summary.get("failures") != 0 or summary.get("errors") != 0:
        errors.append("formal characterization test summary mismatch")
    if summary.get("hypothesis_disposition") != "FAIL_ZERO_EXIT_PROPAGATION":
        errors.append("formal summary does not preserve predicted failure")
    result = {"status": "AUDIT_PASS_REPRODUCED_CONTRACT_FAIL" if not errors else "AUDIT_FAIL",
              "errors": errors, "cases": cases, "raw_file_count": len(inventory),
              "raw_inventory_sha256": digest(inventory_path.read_bytes()),
              "formal_summary_sha256": digest((evidence / "formal_summary.json").read_bytes())}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, default=Path("/evidence"))
    parser.add_argument("--output", type=Path, default=Path("/audit-out/audit.json"))
    parser.add_argument("--study", type=Path, default=Path("/study"))
    parser.add_argument("--workspace", type=Path, default=Path("/source"))
    args = parser.parse_args()
    result = audit(args.evidence, args.output, args.study, args.workspace)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "AUDIT_PASS_REPRODUCED_CONTRACT_FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
