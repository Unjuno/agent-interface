"""Bound one run and materialize partial evidence from its fsynced journal."""

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from common import sha256_path


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def read_journal(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def terminate_group(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=2.0)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()
    except ProcessLookupError:
        process.wait()


def write_partial(out, reason, return_code, started_ns, image_id, stdout_path, stderr_path):
    out.mkdir(parents=True, exist_ok=True)
    journal_path = out / "PROGRESS.jsonl"
    events = read_journal(journal_path)
    meta_path = out / "RUN.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    completed = [event for event in events if event.get("event") == "worker_complete"]
    starts = [event for event in events if event.get("event") == "worker_start"]
    intents = [event for event in events if event.get("event") == "worker_intent"]
    resources = [{k: v for k, v in event.items() if k != "event"} for event in completed if event.get("kind") == "resource"]
    contracts = [{k: v for k, v in event.items() if k != "event"} for event in completed if event.get("kind") == "contract"]
    partial = {
        "schema": "reader-memoryview-partial-v2",
        **meta,
        "stop_reason": reason,
        "supervisor_return_code": return_code,
        "supervisor_started_ns": started_ns,
        "supervisor_stopped_ns": time.time_ns(),
        "resource": resources,
        "contracts": contracts,
        "worker_intents": intents,
        "worker_starts": starts,
        "journal": events,
        "journal_sha256": sha256_path(journal_path) if journal_path.exists() else None,
        "image_id": image_id,
        "supervisor_stdout_sha256": sha256_path(stdout_path) if stdout_path.exists() else None,
        "supervisor_stderr_sha256": sha256_path(stderr_path) if stderr_path.exists() else None,
    }
    write_json(out / "RAW_PARTIAL.json", partial)
    stop = {
        "schema": "reader-memoryview-stop-v1",
        "reason": reason,
        "completed_resource_workers": len(resources),
        "completed_contract_workers": len(contracts),
        "started_workers": len(starts),
        "intended_workers": len(intents),
        "corpus_sha256": meta.get("corpus_sha256"),
        "freeze_sha256": meta.get("freeze_sha256"),
        "source_sha256": meta.get("source_sha256"),
        "partial_sha256": sha256_path(out / "RAW_PARTIAL.json"),
        "journal_sha256": partial["journal_sha256"],
        "image_id": image_id,
    }
    write_json(out / "STOP.json", stop)
    return stop


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("construction", "formal"), required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--image-id", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    parser.add_argument("--worker-timeout-seconds", type=float, default=8.0)
    parser.add_argument("--inject-worker-delay-seconds", type=float, default=0.0)
    args = parser.parse_args()

    if args.inject_worker_delay_seconds and args.phase != "construction":
        raise SystemExit("timeout_injection_forbidden_in_formal")
    out = Path(args.out).resolve()
    if out.exists():
        raise SystemExit("OUTPUT_EXISTS")
    out.parent.mkdir(parents=True, exist_ok=True)
    stdout_path = out.parent / (out.name + ".supervisor.stdout")
    stderr_path = out.parent / (out.name + ".supervisor.stderr")
    root = Path(__file__).resolve().parent
    command = [
        sys.executable,
        "-B",
        str(root / "run.py"),
        "--phase",
        args.phase,
        "--out",
        str(out),
        "--image-id",
        args.image_id,
        "--worker-timeout-seconds",
        str(args.worker_timeout_seconds),
    ]
    if args.inject_worker_delay_seconds:
        command.extend(("--inject-worker-delay-seconds", str(args.inject_worker_delay_seconds)))

    started_ns = time.time_ns()
    timed_out = False
    with stdout_path.open("wb") as stdout_stream, stderr_path.open("wb") as stderr_stream:
        process = subprocess.Popen(
            command,
            cwd=root,
            stdout=stdout_stream,
            stderr=stderr_stream,
            start_new_session=True,
        )
        try:
            return_code = process.wait(timeout=args.timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            terminate_group(process)
            return_code = 124

    if timed_out:
        write_partial(out, "STOP_SUPERVISOR_TIMEOUT", return_code, started_ns, args.image_id, stdout_path, stderr_path)
        print(json.dumps({"status": "STOP_SUPERVISOR_TIMEOUT", "return_code": 124, "out": str(out)}, sort_keys=True))
        return 124

    result = {
        "schema": "reader-memoryview-supervisor-v1",
        "phase": args.phase,
        "return_code": return_code,
        "started_ns": started_ns,
        "ended_ns": time.time_ns(),
        "timeout_seconds": args.timeout_seconds,
        "image_id": args.image_id,
        "command": command,
        "stdout_sha256": sha256_path(stdout_path),
        "stderr_sha256": sha256_path(stderr_path),
    }
    write_json(out.parent / (out.name + ".SUPERVISOR.json"), result)
    if return_code != 0:
        raw_path = out / "RAW.json"
        raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {}
        write_json(
            out / "STOP.json",
            {
                "schema": "reader-memoryview-stop-v1",
                "reason": raw.get("stop_reason") or "STOP_RUNNER_NONZERO_EXIT",
                "runner_return_code": return_code,
                "raw_sha256": sha256_path(raw_path) if raw_path.exists() else None,
                "journal_sha256": raw.get("journal_sha256"),
                "corpus_sha256": raw.get("corpus_sha256"),
                "image_id": args.image_id,
            },
        )
    print(json.dumps({"status": "completed" if return_code == 0 else "stopped", **result}, sort_keys=True))
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
