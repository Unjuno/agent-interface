"""One-shot parent runner for Issue #5795's frozen process-crash schedule."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile

import protocol


TIMEOUT_SECONDS = 5
IDENTITY_FIELDS = {"fingerprint": "fp-01", "target": "target-01", "label": "submit"}
READ_BUFFERS: dict[int, bytearray] = {}


def read_event(proc: subprocess.Popen[bytes]) -> dict[str, object]:
    if proc.stdout is None:
        raise RuntimeError("STOP_MISSING_CHILD_STDOUT")
    buffer = READ_BUFFERS.setdefault(proc.pid, bytearray())
    while b"\n" not in buffer:
        ready, _, _ = select.select([proc.stdout], [], [], TIMEOUT_SECONDS)
        if not ready:
            raise TimeoutError("STOP_CHILD_BARRIER_TIMEOUT")
        chunk = os.read(proc.stdout.fileno(), 4096)
        if not chunk:
            raise RuntimeError("STOP_CHILD_EXIT_BEFORE_BARRIER")
        buffer.extend(chunk)
    line, _, rest = buffer.partition(b"\n")
    buffer[:] = rest
    value = json.loads(line.decode("utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("event"), str):
        raise RuntimeError("STOP_CHILD_EVENT_SCHEMA")
    return value


def child_command(action: str, policy: str, root: Path, ident: str, **extra: object) -> list[str]:
    command = [
        sys.executable,
        "-B",
        str(Path(__file__).with_name("worker.py")),
        action,
        "--policy",
        policy,
        "--root",
        str(root),
        "--identity",
        ident,
    ]
    for key, value in extra.items():
        flag = "--action" if key == "mutation" else "--" + key.replace("_", "-")
        if isinstance(value, bool):
            if value:
                command.append(flag)
            continue
        command.extend([flag, str(value)])
    return command


def launch(command: list[str]) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        bufsize=0,
    )


def continue_child(proc: subprocess.Popen[bytes]) -> None:
    if proc.stdin is None:
        raise RuntimeError("STOP_MISSING_CHILD_STDIN")
    proc.stdin.write(b"CONTINUE\n")
    proc.stdin.flush()


def persist(policy: str, root: Path, ident: str, cut_at: str | None) -> dict[str, object]:
    proc = launch(child_command("persist", policy, root, ident, **IDENTITY_FIELDS))
    trace: list[dict[str, object]] = []
    while True:
        event = read_event(proc)
        trace.append(event)
        name = str(event["event"])
        if name == cut_at:
            os.kill(proc.pid, signal.SIGKILL)
            try:
                proc.wait(timeout=TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired as exc:
                proc.kill()
                proc.wait()
                raise TimeoutError("STOP_CHILD_KILL_WAIT") from exc
            stdout_tail, stderr_tail = proc.communicate(timeout=TIMEOUT_SECONDS)
            buffered = bytes(READ_BUFFERS.pop(proc.pid, bytearray()))
            tail = buffered + stdout_tail
            if tail.strip():
                for line in tail.splitlines():
                    trace.append(json.loads(line))
            return {
                "events": trace,
                "returncode": proc.returncode,
                "acknowledged": False,
                "cut_at": cut_at,
                "stderr": stderr_tail.decode("utf-8", "replace"),
            }
        if event.get("barrier") is True:
            continue_child(proc)
            continue
        if name == "ACKNOWLEDGED":
            remainder, errors = proc.communicate(timeout=TIMEOUT_SECONDS)
            buffered = bytes(READ_BUFFERS.pop(proc.pid, bytearray()))
            remainder = buffered + remainder
            if remainder.strip():
                for line in remainder.splitlines():
                    trace.append(json.loads(line))
            if proc.returncode != 0:
                raise RuntimeError(f"STOP_ACK_CHILD_EXIT:{proc.returncode}:{errors!r}")
            return {
                "events": trace,
                "returncode": proc.returncode,
                "acknowledged": True,
                "cut_at": None,
                "stderr": errors.decode("utf-8", "replace"),
            }


def probe(
    policy: str,
    root: Path,
    ident: str,
    *,
    fields: dict[str, str] | None = None,
    generation: int = 1,
    fresh: bool = False,
    now: int = 100,
) -> dict[str, object]:
    kwargs = dict(fields or IDENTITY_FIELDS)
    command = child_command(
        "probe",
        policy,
        root,
        ident,
        **kwargs,
        evidence_generation=generation,
        fresh_evidence=fresh,
        now=now,
    )
    proc = subprocess.run(command, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
    if proc.returncode != 0:
        raise RuntimeError(f"STOP_PROBE_EXIT:{proc.returncode}:{proc.stderr}")
    result = json.loads(proc.stdout)
    if result.get("event") != "PROBE":
        raise RuntimeError("STOP_PROBE_SCHEMA")
    return result


def mutate(root: Path, ident: str, action: str, generation: int, *, now: int = 100, ttl: int = 50) -> dict[str, object]:
    proc = subprocess.run(
        child_command(action="mutate", policy="C", root=root, ident=ident, mutation=action,
                      generation=generation, now=now, ttl=ttl, **IDENTITY_FIELDS),
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
    )
    if proc.returncode:
        raise RuntimeError(f"STOP_MUTATION_EXIT:{proc.returncode}:{proc.stderr}")
    return json.loads(proc.stdout)


def garbage_collect(root: Path, ident: str, *, now: int) -> dict[str, object]:
    proc = subprocess.run(
        child_command("gc", "C", root, ident, now=now, **IDENTITY_FIELDS),
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
    )
    if proc.returncode:
        raise RuntimeError(f"STOP_GC_EXIT:{proc.returncode}:{proc.stderr}")
    return json.loads(proc.stdout)


def inspect_state(root: Path, ident: str) -> dict[str, object]:
    proc = subprocess.run(
        child_command("inspect", "C", root, ident, **IDENTITY_FIELDS),
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
    )
    if proc.returncode:
        raise RuntimeError(f"STOP_INSPECT_EXIT:{proc.returncode}:{proc.stderr}")
    return json.loads(proc.stdout)


def run_row(spec: dict[str, str], scratch: Path) -> dict[str, object]:
    case = spec["case"]
    policy = spec["policy"]
    root = scratch / f"{case}-{policy}"
    root.mkdir()
    fields = dict(IDENTITY_FIELDS)
    ident = protocol.identity(fields["fingerprint"], fields["target"], fields["label"])
    cut = {
        "pre_write": "READY_BEFORE_WRITE",
        "partial_split_write": "CANDIDATE_WRITTEN",
        "pre_commit": "PRE_COMMIT",
        "post_commit_pre_ack": "POST_COMMIT_PRE_ACK",
    }.get(case)
    persist_result: dict[str, object] | None = None

    if case == "malformed_record":
        (root / "state.sqlite3").write_bytes(b"not-a-sqlite-database\n")
    else:
        persist_result = persist(policy, root, ident, cut)

    row: dict[str, object] = {
        "case": case,
        "policy": policy,
        "identity_sha256": ident,
        "fields": fields,
        "generation": 1,
        "persist": persist_result,
        "probes": [],
        "ack_state": (
            "ACKNOWLEDGED" if persist_result and persist_result["acknowledged"]
            else "UNKNOWN" if case == "post_commit_pre_ack"
            else "NOT_ACKNOWLEDGED"
        ),
    }

    if case == "new_generation_same_fingerprint":
        row["probes"] = [probe(policy, root, ident, generation=2, fresh=True)]
    elif case == "changed_target_same_label":
        changed = {**fields, "target": "target-02"}
        changed_id = protocol.identity(changed["fingerprint"], changed["target"], changed["label"])
        row["probe_identity_sha256"] = changed_id
        row["probes"] = [probe(policy, root, changed_id, fields=changed, fresh=False)]
    elif case == "reactivation":
        row["mutation"] = mutate(root, ident, "reactivate", 2)
        row["probes"] = [probe(policy, root, ident, generation=2, fresh=True)]
    elif case == "expiry_gc_tombstone":
        issued_at, ttl, before_expiry, at_expiry = 100, 50, 149, 150
        row["ttl"] = {"issued_at": issued_at, "duration": ttl,
                      "expires_at": issued_at + ttl, "pre_probe_at": before_expiry,
                      "gc_at": at_expiry, "post_probe_at": at_expiry}
        row["pre_expiry_probe"] = probe(policy, root, ident, generation=1, fresh=False, now=before_expiry)
        row["expired_pre_gc_probe"] = probe(policy, root, ident, generation=1, fresh=False, now=at_expiry)
        row["pre_expiry_gc"] = garbage_collect(root, ident, now=before_expiry)
        row["pre_expiry_state"] = inspect_state(root, ident)
        row["gc"] = garbage_collect(root, ident, now=at_expiry)
        row["post_expiry_probe"] = probe(policy, root, ident, generation=1, fresh=False, now=at_expiry)
        row["probes"] = [row["pre_expiry_probe"], row["expired_pre_gc_probe"], row["post_expiry_probe"]]
    elif case == "repeated_restart":
        row["probes"] = [probe(policy, root, ident), probe(policy, root, ident)]
    else:
        row["probes"] = [probe(policy, root, ident, generation=1, fresh=False)]

    row["observed"] = [p["disposition"] for p in row["probes"]]
    return row


def source_sha256() -> dict[str, str]:
    here = Path(__file__).parent
    names = ("protocol.py", "worker.py", "runner.py", "audit.py")
    return {name: hashlib.sha256((here / name).read_bytes()).hexdigest() for name in names}


def verify_formal_provenance() -> dict[str, object]:
    """Verify frozen local source and runtime identity before any candidate row."""
    here = Path(__file__).parent
    try:
        frozen = json.loads((here / "FREEZE.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"STOP_FREEZE_MANIFEST:{exc}") from exc
    manifest_digest = hashlib.sha256(
        json.dumps(frozen, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if os.environ.get("OBSTAC_FREEZE_SHA256") != manifest_digest:
        raise SystemExit("STOP_FREEZE_DIGEST_MISMATCH")
    if frozen.get("source_sha256") != source_sha256():
        raise SystemExit("STOP_SOURCE_HASH_MISMATCH")
    if frozen.get("schedule_sha256") != protocol.schedule_sha256():
        raise SystemExit("STOP_SCHEDULE_HASH_MISMATCH")
    expected = {
        "run_kind": os.environ.get("OBSTAC_RUN_KIND"),
        "docker_context": os.environ.get("OBSTAC_DOCKER_CONTEXT"),
        "docker_host": os.environ.get("OBSTAC_DOCKER_HOST"),
        "platform": os.environ.get("OBSTAC_PLATFORM"),
        "source_commit": os.environ.get("OBSTAC_SOURCE_COMMIT"),
        "image_id": os.environ.get("OBSTAC_IMAGE_ID"),
    }
    if any(value is None or value == "" for value in expected.values()):
        raise SystemExit("STOP_OBSTAC_PROVENANCE_MISSING")
    frozen_runtime = frozen.get("runtime")
    if not isinstance(frozen_runtime, dict) or any(
        frozen_runtime.get(name) != value for name, value in expected.items()
    ):
        raise SystemExit("STOP_RUNTIME_IDENTITY_MISMATCH")
    if expected["run_kind"] != "formal":
        raise SystemExit("STOP_OBSTAC_RUN_KIND")
    audit_hash = hashlib.sha256((here / "audit.py").read_bytes()).hexdigest()
    if frozen.get("audit_sha256") != audit_hash:
        raise SystemExit("STOP_AUDIT_HASH_MISMATCH")
    if os.environ.get("OBSTAC_AUDIT_SHA256") != audit_hash:
        raise SystemExit("STOP_AUDIT_ENV_HASH_MISMATCH")
    if frozen.get("image_ref") != "python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9":
        raise SystemExit("STOP_IMAGE_REFERENCE_NOT_PINNED")
    return {"manifest_sha256": manifest_digest, **expected}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--construction", action="store_true")
    args = parser.parse_args()
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise SystemExit("STOP_NONEMPTY_OUTPUT")
    if args.construction:
        print(json.dumps({"mode": "construction", "output_empty": True, "formal_rows": 0}))
        return 0

    runtime_provenance = verify_formal_provenance()

    raw_path = output / "raw.jsonl"
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="suppression-5789-") as temp:
        scratch = Path(temp)
        with raw_path.open("x", encoding="utf-8") as raw:
            for index, spec in enumerate(protocol.CASES):
                try:
                    row = run_row(spec, scratch)
                    raw.write(json.dumps(row, sort_keys=True) + "\n")
                    raw.flush()
                except Exception as exc:  # retain partial rows and the first stop
                    failures.append(f"row[{index}] {spec}: {type(exc).__name__}: {exc}")
                    break
    result = {
        "mode": "formal",
        "allocation": "issue-5795-t0-20261001-01",
        "schedule_sha256": protocol.schedule_sha256(),
        "source_sha256": source_sha256(),
        "runtime_provenance": runtime_provenance,
        "rows_written": sum(1 for _ in raw_path.open(encoding="utf-8")),
        "failures": failures,
        "formal_runner_exit": 0 if not failures else 2,
    }
    (output / "runner_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return int(result["formal_runner_exit"])


if __name__ == "__main__":
    raise SystemExit(main())
