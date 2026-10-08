"""One synthetic current-main CLI allocation for Issue #3814; no external calls."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def write_json(path: Path, value: object) -> bytes:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    path.write_bytes(data)
    return data

def snapshot(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): sha(path.read_bytes())
            for path in sorted(root.rglob("*")) if path.is_file()}

def cli_command(args: list[str], *, env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[bytes]:
    """Run the real CLI main with only its dispatch function replaced by a fixture."""
    launcher = r'''
import json, os, sys
from pathlib import Path
from runtime.cli_v1 import __main__ as cli
counter = Path(os.environ["ISSUE3814_DISPATCH_COUNTER"])
def synthetic_dispatch(**kwargs):
    count = int(counter.read_text()) if counter.exists() else 0
    counter.write_text(str(count + 1), encoding="ascii")
    return {"schema": "agent-interface/runtime-dispatch-result-v1", "status": "returned",
            "result": {"status": "completed", "execution": {"observations": []}}}
cli.dispatch = synthetic_dispatch
sys.argv = ["agent-interface", *json.loads(os.environ["ISSUE3814_CLI_ARGS"])]
raise SystemExit(cli.main())
'''
    child_env = dict(env)
    child_env["ISSUE3814_CLI_ARGS"] = json.dumps(args)
    return subprocess.run([sys.executable, "-c", launcher], cwd=cwd, env=child_env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30)

def run(output: Path, source: Path, *, preflight: dict | None = None) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise RuntimeError("OUTPUT_NOT_EMPTY")
    work = output / "work"
    work.mkdir()
    input_dir = work / "input"
    input_dir.mkdir()
    program, targets = input_dir / "program.json", input_dir / "targets.json"
    write_json(program, {"ops": []})
    write_json(targets, {"fixture": 1})
    run_dir = work / "attempt-formal-01"
    counter = output / "dispatch-count.txt"
    env = dict(os.environ)
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(source),
               ISSUE3814_DISPATCH_COUNTER=str(counter))

    dispatch_args = ["dispatch", "--program", str(program), "--targets", str(targets),
                     "--current-observation-seq", "7", "--current-binding-revision", "3",
                     "--run-directory", str(run_dir)]
    producer = cli_command(dispatch_args, env=env, cwd=source)
    (output / "producer.stdout.bin").write_bytes(producer.stdout)
    (output / "producer.stderr.bin").write_bytes(producer.stderr)
    (output / "producer.returncode.txt").write_text(str(producer.returncode), encoding="ascii")
    if producer.returncode != 0 or not producer.stdout.endswith(b"\n"):
        raise RuntimeError("PRODUCER_DID_NOT_COMPLETE_FRAMED_JSONL")

    # Relay accepted every producer byte; the caller receives only the strict prefix without LF.
    delivered = producer.stdout[:-1]
    (output / "relay-accepted.bin").write_bytes(producer.stdout)
    (output / "caller-delivered.bin").write_bytes(delivered)
    parsed_full, parsed_prefix = json.loads(producer.stdout), json.loads(delivered)
    parser_only_completed = (parsed_prefix.get("status") == "returned"
                             and parsed_prefix.get("result", {}).get("status") == "completed")
    framing_guard_rejects = not delivered.endswith(b"\n")

    retained_before = snapshot(run_dir)
    report_bytes = (run_dir / "report.json").read_bytes()
    report_sha = sha(report_bytes)
    def read_cli(args):
        return subprocess.run([sys.executable, "-m", "runtime.cli_v1", *args], cwd=source,
                              env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              check=False, timeout=30)
    attempt_status = read_cli(["attempt-status", "--run-directory", str(run_dir)])
    receipt = read_cli(["receipt", "--report", str(run_dir / "report.json"), "--raw"])
    review = read_cli(["review", "--report", str(run_dir / "report.json"), "--run-directory", str(run_dir)])
    (output / "attempt-status.stdout.bin").write_bytes(attempt_status.stdout)
    (output / "receipt-raw.stdout.bin").write_bytes(receipt.stdout)
    (output / "review.stdout.bin").write_bytes(review.stdout)

    # Complete-delivery control uses the exact same producer bytes.
    complete_control = json.loads(producer.stdout)
    complete_control_pass = producer.stdout.endswith(b"\n") and complete_control == parsed_full

    # Request-only control: inspection must report unknown and must not authorize replay.
    request_only = work / "attempt-request-only"
    request_only.mkdir()
    write_json(request_only / "request.json", {
        "schema": "agent-interface/cli-attempt-v1", "operation": "dispatch",
        "arguments": {"fixture": True}, "note": "synthetic request-only control"})
    request_status = read_cli(["attempt-status", "--run-directory", str(request_only)])
    (output / "request-only-status.stdout.bin").write_bytes(request_status.stdout)

    # Existing-directory control must refuse before calling the synthetic facade.
    preexisting = work / "attempt-preexisting"
    preexisting.mkdir()
    sentinel = preexisting / "sentinel.txt"
    sentinel.write_bytes(b"immutable-preexisting-bytes\n")
    sentinel_before = sha(sentinel.read_bytes())
    preexisting_args = ["dispatch", "--program", str(program), "--targets", str(targets),
                        "--current-observation-seq", "7", "--current-binding-revision", "3",
                        "--run-directory", str(preexisting)]
    preexisting_result = cli_command(preexisting_args, env=env, cwd=source)
    (output / "preexisting.stdout.bin").write_bytes(preexisting_result.stdout)
    (output / "preexisting.stderr.bin").write_bytes(preexisting_result.stderr)

    retained_after = snapshot(run_dir)
    status_row, receipt_row, review_row = (json.loads(attempt_status.stdout),
                                           json.loads(receipt.stdout), json.loads(review.stdout))
    result = {
        "allocation": "issue-3814-jsonl-framing-formal-01",
        "base_commit": os.environ.get("ISSUE3814_BASE_COMMIT"),
        "preflight": preflight or {},
        "container": {"image_ref": os.environ.get("ISSUE3814_IMAGE_REF"),
                      "image_id": os.environ.get("ISSUE3814_IMAGE_ID"),
                      "platform": os.environ.get("ISSUE3814_PLATFORM"),
                      "docker_server": os.environ.get("ISSUE3814_DOCKER_SERVER")},
        "producer": {"returncode": producer.returncode, "stdout_bytes": len(producer.stdout),
                     "delivered_bytes": len(delivered), "stdout_sha256": sha(producer.stdout),
                     "delivered_sha256": sha(delivered), "ends_lf": producer.stdout.endswith(b"\n"),
                     "delivered_is_exact_prefix_without_lf": delivered == producer.stdout[:-1]},
        "parser_only": {"valid_json": True, "reports_completed": parser_only_completed},
        "framing_guard": {"rejects_missing_lf": framing_guard_rejects},
        "recovery": {
            "attempt_status_returncode": attempt_status.returncode,
            "attempt_status": status_row.get("status"), "replay_allowed": status_row.get("replay_allowed"),
            "attempt_report_value_matches": status_row.get("files", {}).get("report.json", {}).get("value") == json.loads(report_bytes),
            "receipt_returncode": receipt.returncode,
            "receipt_raw_matches_report": json.loads(receipt.stdout) == json.loads(report_bytes),
            "review_returncode": review.returncode,
            "review_source_sha256": review_row.get("receipt", {}).get("source", {}).get("sha256"),
            "retained_report_sha256": report_sha,
            "attempt_files_unchanged": retained_before == retained_after,
            "report_bytes_unchanged": sha((run_dir / "report.json").read_bytes()) == report_sha,
        },
        "controls": {
            "complete_delivery_pass": complete_control_pass,
            "request_only_returncode": request_status.returncode,
            "request_only_status": json.loads(request_status.stdout).get("status"),
            "request_only_report_missing": json.loads(request_status.stdout).get("files", {}).get("report.json", {}).get("state") == "missing",
            "preexisting_returncode": preexisting_result.returncode,
            "preexisting_facade_calls_unchanged": int(counter.read_text()) == 1,
            "preexisting_sentinel_unchanged": sha(sentinel.read_bytes()) == sentinel_before,
        },
        "dispatch_facade_calls": int(counter.read_text()),
        "attempt_file_sha256_before": retained_before,
        "attempt_file_sha256_after": retained_after,
        "report_bytes_sha256": report_sha, "report_bytes": len(report_bytes),
        "scope": "synthetic CLI dispatch and in-memory downstream final-LF truncation only",
    }
    (output / "RESULT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if result["dispatch_facade_calls"] != 1:
        raise RuntimeError("DISPATCH_COUNT_NOT_ONE")
    manifest = []
    for path in sorted(p for p in output.rglob("*") if p.is_file() and p.name != "SHA256SUMS"):
        manifest.append(f"{sha(path.read_bytes())}  {path.relative_to(output).as_posix()}")
    (output / "SHA256SUMS").write_text("\n".join(manifest) + "\n", encoding="ascii")
    return result

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: runner.py OUTPUT_DIR SOURCE_ROOT")
    print(json.dumps(run(Path(sys.argv[1]), Path(sys.argv[2])), sort_keys=True))
