"""Run the frozen memoryview allocation comparison with a durable journal."""

import argparse
import json
import os
import platform
import ssl
import subprocess
import sys
import time
from pathlib import Path

from common import corpus_bytes, sha256_bytes, sha256_path


SOURCE_FILES = (
    "baseline_reader.py",
    "candidate_reader.py",
    "common.py",
    "worker.py",
    "contract_worker.py",
    "run.py",
    "supervise.py",
    "audit.py",
    "controls.py",
    "test_supervisor.py",
    "stop_audit.py",
)


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def append_journal(path, event):
    with Path(path).open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def read_journal(path):
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def environment(image_id):
    return {
        "image_id": image_id,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version,
        "python_version": platform.python_version(),
        "openssl": ssl.OPENSSL_VERSION,
        "cpu_count": os.cpu_count(),
    }


def verify_freeze(root, image_id):
    freeze_path = root.parent / "FREEZE.json"
    env_path = root.parent / "ENVIRONMENT.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if sha256_path(env_path) != freeze["environment_sha256"]:
        raise ValueError("environment_sha256_mismatch")
    if image_id != freeze["container_image_id"]:
        raise ValueError("container_image_id_mismatch")
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "AMD64"):
        raise ValueError("platform_mismatch")
    if platform.python_version() != "3.13.5":
        raise ValueError("python_version_mismatch")
    actual = {name: sha256_path(root / name) for name in SOURCE_FILES}
    for name, expected in freeze["source_sha256"].items():
        if actual.get(name) != expected:
            raise ValueError("source_sha256_mismatch:" + name)
    if set(actual) != set(freeze["source_sha256"]):
        raise ValueError("source_manifest_membership_mismatch")
    return freeze, sha256_path(freeze_path), actual


def run_worker(root, out, journal_path, worker_id, spec, timeout, inject_delay):
    command = spec["argv"]
    if inject_delay and spec["kind"] == "resource" and spec["order_index"] == 0:
        command = [sys.executable, "-B", "-c", "import time; time.sleep(" + str(inject_delay) + ")"]

    prefix = "worker-" + worker_id
    stdout_path = out / (prefix + ".stdout")
    stderr_path = out / (prefix + ".stderr")
    started_ns = time.time_ns()
    append_journal(
        journal_path,
        {
            "event": "worker_intent",
            "worker_id": worker_id,
            "kind": spec["kind"],
            "identity": spec["identity"],
            "argv": command,
            "started_ns": started_ns,
        },
    )

    with stdout_path.open("wb") as stdout_stream, stderr_path.open("wb") as stderr_stream:
        process = subprocess.Popen(command, cwd=root, stdout=stdout_stream, stderr=stderr_stream)
        append_journal(
            journal_path,
            {
                "event": "worker_start",
                "worker_id": worker_id,
                "kind": spec["kind"],
                "identity": spec["identity"],
                "pid": process.pid,
                "argv": command,
                "stdout_path": stdout_path.name,
                "stderr_path": stderr_path.name,
                "started_ns": started_ns,
            },
        )
        status = "complete"
        try:
            exit_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            status = "worker_timeout"
            process.kill()
            exit_code = process.wait()

    stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
    stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
    ended_ns = time.time_ns()
    record = {
        "worker_id": worker_id,
        "kind": spec["kind"],
        **spec["identity"],
        "argv": command,
        "pid": process.pid,
        "exit": exit_code,
        "status": status,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_sha256": sha256_path(stdout_path),
        "stderr_sha256": sha256_path(stderr_path),
        "started_ns": started_ns,
        "ended_ns": ended_ns,
        "duration_ns": ended_ns - started_ns,
    }
    append_journal(journal_path, {"event": "worker_complete", **record})
    return record


def make_specs(root, corpus, phase, inject_delay):
    if phase == "construction":
        cursors = [0, 32, 64]
        repetitions = 1
    else:
        cursors = [0, 2048, 4064, 4096]
        repetitions = 3

    specs = []
    for cursor in cursors:
        for repetition in range(repetitions):
            arms = ["BASELINE", "MEMORYVIEW"] if repetition % 2 == 0 else ["MEMORYVIEW", "BASELINE"]
            for arm in arms:
                identity = {"cursor_records": cursor, "rep": repetition, "arm": arm}
                argv = [
                    sys.executable,
                    "-B",
                    str(root / "worker.py"),
                    "--arm",
                    arm,
                    "--corpus",
                    str(corpus),
                    "--cursor-records",
                    str(cursor),
                    "--max-records",
                    "32",
                ]
                specs.append({"kind": "resource", "identity": identity, "argv": argv})

    for arm in ("BASELINE", "MEMORYVIEW"):
        specs.append(
            {
                "kind": "contract",
                "identity": {"arm": arm},
                "argv": [sys.executable, "-B", str(root / "contract_worker.py"), "--arm", arm],
            }
        )
    if inject_delay and phase != "construction":
        raise ValueError("timeout_injection_forbidden_in_formal")
    return specs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("construction", "formal"), required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--image-id", required=True)
    parser.add_argument("--worker-timeout-seconds", type=float, default=8.0)
    parser.add_argument("--inject-worker-delay-seconds", type=float, default=0.0)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    out = Path(args.out)
    if out.exists():
        raise SystemExit("OUTPUT_EXISTS")
    freeze, freeze_sha, source_hashes = verify_freeze(root, args.image_id)
    out.mkdir(parents=True)
    started_ns = time.time_ns()
    records = 64 if args.phase == "construction" else 4096
    corpus = out / "corpus.jsonl"
    data = corpus_bytes(records)
    corpus.write_bytes(data)
    run_meta = {
        "schema": "reader-memoryview-run-meta-v2",
        "phase": args.phase,
        "records": records,
        "corpus_bytes": len(data),
        "corpus_sha256": sha256_bytes(data),
        "started_ns": started_ns,
        "runner_pid": os.getpid(),
        "freeze_sha256": freeze_sha,
        "source_sha256": source_hashes,
        "environment": environment(args.image_id),
        "worker_timeout_seconds": args.worker_timeout_seconds,
        "scheduled_resource_workers": 6 if args.phase == "construction" else 24,
        "scheduled_contract_workers": 2,
    }
    write_json(out / "RUN.json", run_meta)
    journal_path = out / "PROGRESS.jsonl"
    append_journal(journal_path, {"event": "run_start", **run_meta})

    specs = make_specs(root, corpus, args.phase, args.inject_worker_delay_seconds)
    resources = []
    contracts = []
    stop_reason = None
    for order_index, spec in enumerate(specs):
        spec["order_index"] = order_index
        worker_id = "{:03d}".format(order_index + 1)
        record = run_worker(
            root,
            out,
            journal_path,
            worker_id,
            spec,
            args.worker_timeout_seconds,
            args.inject_worker_delay_seconds,
        )
        (resources if spec["kind"] == "resource" else contracts).append(record)
        if record["status"] != "complete":
            stop_reason = "STOP_WORKER_TIMEOUT"
            break
        if record["exit"] != 0:
            stop_reason = "STOP_WORKER_NONZERO_EXIT"
            break

    ended_ns = time.time_ns()
    append_journal(
        journal_path,
        {"event": "run_complete", "ended_ns": ended_ns, "stop_reason": stop_reason},
    )
    journal_events = read_journal(journal_path)
    raw = {
        "schema": "reader-memoryview-run-v2",
        **run_meta,
        "ended_ns": ended_ns,
        "resource": resources,
        "contracts": contracts,
        "journal": journal_events,
        "journal_sha256": sha256_path(journal_path),
        "stop_reason": stop_reason,
    }
    write_json(out / "RAW.json", raw)
    result = {
        "phase": args.phase,
        "resource_rows": len(resources),
        "contracts": len(contracts),
        "stop_reason": stop_reason,
        "raw_sha256": sha256_path(out / "RAW.json"),
    }
    print(json.dumps(result, sort_keys=True))
    if stop_reason:
        return 3
    expected_resources = 6 if args.phase == "construction" else 24
    return 0 if len(resources) == expected_resources and len(contracts) == 2 else 2


if __name__ == "__main__":
    raise SystemExit(main())
