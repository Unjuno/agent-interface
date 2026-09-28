"""One-shot host-filesystem publication boundary experiment for Issue #5134."""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import queue
import subprocess
import sys
import tempfile
import time
import traceback

ALLOCATION = "needle-publication-host-boundary-5134-20260928-01"
ISSUE = 5134
BASE_MAIN = "16421aefa2ec357b79e3fd3dc307b32955bc6fab"
SEED_REL = "research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json"
SEED_SHA256 = "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a"
SEED_BLOB = "45b80150dac503f4eb6f3cb5d82f9afa2c587107"
GENERATIONS = tuple(range(3789, 3796))
READERS = 4
PHASES = tuple(f"phase_{i}" for i in range(1, 8))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_value(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def package_for(seed: dict, generation: int) -> bytes:
    value = copy.deepcopy(seed)
    value["generation"] = generation
    value["provenance"] = dict(value["provenance"])
    value["provenance"]["allocation"] = ALLOCATION
    value["provenance"]["predecessor_issue"] = ISSUE
    value.pop("payload_sha256", None)
    value["payload_sha256"] = sha(canonical(value))
    return canonical(value)


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _reader_atomic(active: str, gate, results, phase: str, index: int) -> None:
    fd = os.open(active, os.O_RDONLY)
    fd_open_ns = time.monotonic_ns()
    results.put({"kind": "ready", "phase": phase, "reader": index, "pid": os.getpid(), "fd_open_ns": fd_open_ns})
    if not gate.wait(30):
        os.close(fd)
        results.put({"kind": "error", "phase": phase, "reader": index, "error": "atomic gate timeout"})
        return
    fd_read_start_ns = time.monotonic_ns()
    held = os.pread(fd, 1_000_000, 0)
    fd_read_end_ns = time.monotonic_ns()
    fresh_fd = os.open(active, os.O_RDONLY)
    fresh_open_ns = time.monotonic_ns()
    fresh = os.read(fresh_fd, 1_000_000)
    fresh_read_end_ns = time.monotonic_ns()
    os.close(fresh_fd)
    os.close(fd)
    results.put({"kind": "atomic", "phase": phase, "reader": index, "pid": os.getpid(),
                 "fd_open_ns": fd_open_ns, "fd_read_start_ns": fd_read_start_ns,
                 "fd_read_end_ns": fd_read_end_ns, "fresh_open_ns": fresh_open_ns,
                 "fresh_read_end_ns": fresh_read_end_ns, "held_b64": b64(held),
                 "held_sha256": sha(held), "fresh_b64": b64(fresh), "fresh_sha256": sha(fresh)})


def _reader_unsafe(active: str, gate, results, phase: str, index: int) -> None:
    fd = os.open(active, os.O_RDONLY)
    fd_open_ns = time.monotonic_ns()
    results.put({"kind": "ready", "phase": phase, "reader": index, "pid": os.getpid(), "fd_open_ns": fd_open_ns})
    if not gate.wait(30):
        os.close(fd)
        results.put({"kind": "error", "phase": phase, "reader": index, "error": "unsafe gate timeout"})
        return
    read_start_ns = time.monotonic_ns()
    size = os.fstat(fd).st_size
    held = os.pread(fd, 1_000_000, 0)[:size]
    read_end_ns = time.monotonic_ns()
    fresh_fd = os.open(active, os.O_RDONLY)
    fresh_open_ns = time.monotonic_ns()
    fresh_size = os.fstat(fresh_fd).st_size
    fresh = os.read(fresh_fd, 1_000_000)[:fresh_size]
    fresh_read_end_ns = time.monotonic_ns()
    os.close(fresh_fd)
    os.close(fd)
    results.put({"kind": "unsafe", "phase": phase, "reader": index, "pid": os.getpid(),
                 "fd_open_ns": fd_open_ns, "read_start_ns": read_start_ns, "read_end_ns": read_end_ns,
                 "fresh_open_ns": fresh_open_ns, "fresh_read_end_ns": fresh_read_end_ns,
                 "held_b64": b64(held), "held_sha256": sha(held),
                 "fresh_b64": b64(fresh), "fresh_sha256": sha(fresh)})


def collect(results, count: int, expected_kind: str, timeout_s: float = 30.0) -> list[dict]:
    deadline = time.monotonic() + timeout_s
    found = []
    while len(found) < count:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"timed out collecting {expected_kind}: {len(found)}/{count}")
        try:
            item = results.get(timeout=remaining)
        except queue.Empty as exc:
            raise TimeoutError(f"timed out collecting {expected_kind}: {len(found)}/{count}") from exc
        if item.get("kind") == "error":
            raise RuntimeError(f"reader error: {item}")
        if item.get("kind") != expected_kind:
            raise RuntimeError(f"unexpected reader message: {item.get('kind')}")
        found.append(item)
    return found


def start_readers(ctx, target, active: Path, phase: str):
    gate = ctx.Event()
    results = ctx.Queue()
    workers = [ctx.Process(target=target, args=(str(active), gate, results, phase, i)) for i in range(READERS)]
    for worker in workers:
        worker.start()
    ready = collect(results, READERS, "ready")
    return gate, results, workers, ready


def finish_workers(workers) -> list[int | None]:
    for worker in workers:
        worker.join(30)
    for worker in workers:
        if worker.is_alive():
            worker.terminate()
            worker.join(5)
    return [worker.exitcode for worker in workers]


def run_atomic(ctx, scratch: Path, seed_raw: bytes, seed: dict, packages: dict[int, bytes]) -> list[dict]:
    root = scratch / "atomic"
    root.mkdir()
    active = root / "ACTIVE.json"
    active.write_bytes(seed_raw)
    rows = []
    previous = seed_raw
    for phase, generation in zip(PHASES, GENERATIONS, strict=True):
        staged = root / f"{phase}.candidate"
        staged.write_bytes(packages[generation])
        gate, results, workers, ready = start_readers(ctx, _reader_atomic, active, phase)
        replace_start_ns = time.monotonic_ns()
        os.replace(staged, active)
        replace_return_ns = time.monotonic_ns()
        gate.set()
        phase_rows = collect(results, READERS, "atomic")
        exit_codes = finish_workers(workers)
        if exit_codes != [0] * READERS:
            raise RuntimeError(f"atomic child exit codes: {exit_codes}")
        opened = {row["reader"]: row for row in ready}
        for row in phase_rows:
            row.update({"generation": generation, "replace_start_ns": replace_start_ns,
                        "replace_return_ns": replace_return_ns, "child_exit_codes": exit_codes})
            row["fd_open_ns"] = opened[row["reader"]]["fd_open_ns"]
        rows.extend(phase_rows)
        previous = packages[generation]
    return rows


def write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        count = os.write(fd, view)
        view = view[count:]


def run_unsafe(ctx, scratch: Path, seed_raw: bytes, packages: dict[int, bytes]) -> list[dict]:
    root = scratch / "unsafe"
    root.mkdir()
    active = root / "ACTIVE.json"
    active.write_bytes(seed_raw)
    rows = []
    previous = seed_raw
    for phase, generation in zip(PHASES, GENERATIONS, strict=True):
        expected = packages[generation]
        split = max(1, len(expected) // 3)
        gate, results, workers, ready = start_readers(ctx, _reader_unsafe, active, phase)
        write_start_ns = time.monotonic_ns()
        fd = os.open(active, os.O_WRONLY)
        os.ftruncate(fd, 0)
        truncate_ns = time.monotonic_ns()
        write_all(fd, expected[:split])
        partial_complete_ns = time.monotonic_ns()
        gate.set()
        phase_rows = collect(results, READERS, "unsafe")
        complete_write_start_ns = time.monotonic_ns()
        write_all(fd, expected[split:])
        os.close(fd)
        write_end_ns = time.monotonic_ns()
        final = active.read_bytes()
        if final != expected:
            raise RuntimeError(f"unsafe completed bytes differ for {phase}")
        exit_codes = finish_workers(workers)
        if exit_codes != [0] * READERS:
            raise RuntimeError(f"unsafe child exit codes: {exit_codes}")
        opened = {row["reader"]: row for row in ready}
        for row in phase_rows:
            row.update({"generation": generation, "write_start_ns": write_start_ns,
                        "truncate_ns": truncate_ns, "partial_complete_ns": partial_complete_ns,
                        "complete_write_start_ns": complete_write_start_ns, "write_end_ns": write_end_ns,
                        "partial_b64": b64(expected[:split]), "partial_sha256": sha(expected[:split]),
                        "completed_b64": b64(final), "completed_sha256": sha(final),
                        "child_exit_codes": exit_codes})
            row["fd_open_ns"] = opened[row["reader"]]["fd_open_ns"]
        rows.extend(phase_rows)
        previous = expected
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    output = args.output.resolve()
    if platform.system() != "Darwin":
        raise RuntimeError("STOP: this host boundary allocation requires macOS")
    if output.exists() or output == repo or repo in output.parents:
        raise RuntimeError("STOP: output must be a fresh path outside the source checkout")
    head = git_value(repo, "rev-parse", "HEAD")
    tree = git_value(repo, "rev-parse", "HEAD^{tree}")
    main_sha = git_value(repo, "rev-parse", "origin/main")
    if main_sha != BASE_MAIN:
        raise RuntimeError(f"STOP: origin/main changed from frozen main {BASE_MAIN} to {main_sha}")
    if head != BASE_MAIN:
        raise RuntimeError(f"STOP: source HEAD {head} does not equal frozen main {BASE_MAIN}")
    source_dir = Path(__file__).resolve().parent
    freeze = json.loads((source_dir / "FREEZE.json").read_text())
    for rel, expected in freeze["source_sha256"].items():
        if sha((source_dir / rel).read_bytes()) != expected:
            raise RuntimeError(f"STOP: frozen source hash mismatch: {rel}")
    seed_path = repo / SEED_REL
    seed_raw = seed_path.read_bytes()
    if sha(seed_raw) != SEED_SHA256 or blob_id(seed_raw) != SEED_BLOB:
        raise RuntimeError("STOP: seed identity mismatch")
    if output.exists():
        raise RuntimeError("STOP: output path collision")
    output.mkdir(parents=True)
    receipt = {"allocation": ALLOCATION, "issue": ISSUE, "source_commit": head, "source_tree": tree,
               "frozen_main": BASE_MAIN, "seed_path": SEED_REL, "seed_sha256": sha(seed_raw),
               "seed_git_blob": blob_id(seed_raw), "source_sha256": freeze["source_sha256"],
               "host": {"system": platform.system(), "release": platform.release(),
                        "machine": platform.machine(), "python": sys.version,
                        "filesystem_device": os.stat(repo).st_dev},
               "docker_invocations": 0, "container_id": None,
               "command": ["python3", f"{source_dir.name}/host_boundary.py", "--repo", "<checkout>",
                           "--output", "<fresh-output-outside-checkout>"]}
    (output / "run_receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
    scratch = Path(tempfile.mkdtemp(prefix="needle-pub-host-boundary-", dir="/tmp"))
    seed = json.loads(seed_raw)
    packages = {generation: package_for(seed, generation) for generation in GENERATIONS}
    raw = {"schema": "needle-publication-host-boundary-raw-v1", "allocation": ALLOCATION,
           "issue": ISSUE, "source_commit": head, "source_tree": tree, "frozen_main": BASE_MAIN,
           "seed_sha256": sha(seed_raw), "seed_git_blob": blob_id(seed_raw),
           "source_sha256": freeze["source_sha256"],
           "seed_bytes": len(seed_raw), "docker_invocations": 0, "container_id": None,
           "scratch_path_class": "/tmp", "phases": list(PHASES), "generations": list(GENERATIONS),
           "readers_per_phase": READERS, "candidate_sha256": {str(g): sha(b) for g, b in packages.items()},
           "atomic_rows": [], "unsafe_rows": [], "status": "RUNNING"}
    (output / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n")
    try:
        ctx = mp.get_context("spawn")
        raw["atomic_rows"] = run_atomic(ctx, scratch, seed_raw, seed, packages)
        (output / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n")
        raw["unsafe_rows"] = run_unsafe(ctx, scratch, seed_raw, packages)
        raw["status"] = "CAPTURED"
        (output / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n")
        return 0
    except BaseException as exc:
        raw["status"] = "STOP_EXECUTION_ERROR"
        raw["error_type"] = type(exc).__name__
        raw["error"] = str(exc)
        (output / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n")
        (output / "traceback.txt").write_text(traceback.format_exc())
        raise


if __name__ == "__main__":
    raise SystemExit(main())
