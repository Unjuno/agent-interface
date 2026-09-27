"""One-shot cross-process publication probe; formal entrypoint only in container."""
from __future__ import annotations

import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import sys
import threading
import time

from protocol import IMAGE_ID, NEW, OLD, SEED_SHA256, SNAPSHOTS_PER_BATCH, canonical_bytes, successor, valid

EXP = Path("/src/research/system1/needle_cross_process_publication_orbstack_bind_5066_v1_20260928")
SEED = Path("/src/research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json")
OUT = Path("/out")
READERS = 4


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def observe(path: str, phase: str, request: str, batch: int) -> dict:
    rows = []
    for _ in range(SNAPSHOTS_PER_BATCH):
        start = time.monotonic_ns()
        try:
            raw = Path(path).read_bytes()
            end = time.monotonic_ns()
            try:
                obj = json.loads(raw)
                parsed = True
                is_valid = valid(obj)
                gen = obj.get("generation")
                embedded = obj.get("payload_sha256")
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError, AttributeError):
                parsed, is_valid, gen, embedded = False, False, None, None
            rows.append({"start_ns": start, "end_ns": end, "bytes": len(raw), "raw_sha256": sha(raw),
                         "parse_ok": parsed, "valid": is_valid, "generation": gen, "embedded_digest": embedded})
        except OSError as exc:
            end = time.monotonic_ns()
            rows.append({"start_ns": start, "end_ns": end, "read_error": type(exc).__name__})
    return {"phase": phase, "request": request, "batch": batch, "pid": os.getpid(), "rows": rows}


def reader(index: int, path: str, commands, responses):
    while True:
        item = commands.get()
        if item is None:
            return
        phase, request, batch = item
        try:
            result = observe(path, phase, request, batch)
            result["reader"] = index
        except BaseException as exc:
            result = {"phase": phase, "request": request, "batch": batch, "pid": os.getpid(),
                     "reader": index, "error": type(exc).__name__ + ":" + str(exc)}
        responses.put(result)


def launch(active: Path):
    workers = []
    for i in range(READERS):
        q, r = mp.Queue(), mp.Queue()
        p = mp.Process(target=reader, args=(i, str(active), q, r))
        p.start()
        workers.append((p, q, r))
    pids = [p.pid for p, _, _ in workers]
    if len(set(pids)) != READERS or os.getpid() in pids:
        raise RuntimeError("reader process identity failure")
    return workers


def request(workers, phase: str, request_id: str, batch: int) -> list[dict]:
    for p, q, _ in workers:
        if not p.is_alive():
            raise RuntimeError("reader exited before scheduled read")
        q.put((phase, request_id, batch))
    result = []
    for index, (_, _, r) in enumerate(workers):
        row = r.get(timeout=30)
        if row.get("request") != request_id or row.get("reader") != index:
            raise RuntimeError("reader response schedule mismatch")
        result.append(row)
    return result


def finish(workers):
    for _, q, _ in workers:
        q.put(None)
    for p, _, _ in workers:
        p.join(10)
        if p.is_alive():
            p.terminate(); p.join()
    exits = [p.exitcode for p, _, _ in workers]
    if exits != [0] * READERS:
        raise RuntimeError(f"reader exits not clean: {exits}")
    return exits


def concurrent_window(active: Path, workers, phase: str, request_id: str, batch: int, publish_count: int,
                      candidate: bytes | None) -> tuple[list[dict], list[dict]]:
    intervals = []
    failures = []
    started = threading.Event()
    def publisher():
        try:
            started.set()
            if candidate is not None:
                for n in range(publish_count):
                    tmp = active.parent / f"candidate-{phase}-{n}.tmp"
                    tmp.write_bytes(candidate)
                    a = time.monotonic_ns()
                    os.replace(tmp, active)
                    b = time.monotonic_ns()
                    intervals.append([a, b])
                    time.sleep(0.001)
        except BaseException as exc:
            failures.append(type(exc).__name__ + ":" + str(exc))
    start = time.monotonic_ns()
    thread = threading.Thread(target=publisher)
    thread.start()
    if not started.wait(5): raise RuntimeError("publisher did not start")
    read_rows = request(workers, phase, request_id, batch)
    thread.join(30)
    end = time.monotonic_ns()
    if thread.is_alive() or failures: raise RuntimeError(f"publisher window failed: {failures}")
    for row in read_rows: row["window_start_ns"], row["window_end_ns"] = start, end
    return read_rows, intervals


def arm_atomic(root: Path, old_raw: bytes, old: dict, new: dict) -> dict:
    folder = root / "atomic"; folder.mkdir()
    active = folder / "ACTIVE.json"; active.write_bytes(old_raw)
    workers = launch(active); all_rows, replacements, post_rows = [], [], []
    candidate = canonical_bytes(new)
    try:
        cp = folder / "candidate.tmp"; cp.write_bytes(candidate)
        if not valid(json.loads(cp.read_bytes())): raise RuntimeError("candidate validation failed")
        for phase_no in range(1, 8):
            phase = f"publish_{phase_no}"
            rows, intervals = concurrent_window(active, workers, phase, f"atomic-{phase_no}", phase_no, 64, candidate)
            all_rows += rows; replacements += [{"phase": phase, "start_ns": a, "end_ns": b} for a, b in intervals]
            post_rows += request(workers, phase + "_post", f"atomic-post-{phase_no}", phase_no)
            for row in post_rows[-READERS:]: row["expected_post_raw_sha256"] = sha(candidate)
        before = sha(active.read_bytes())
        bad = dict(new); bad["payload_sha256"] = "0" * 64
        invalid_accepted = valid(bad)
        stale_disposition = "YIELD_STALE_GENERATION" if old["generation"] != new["generation"] else "ELIGIBLE_PROPOSAL_ONLY"
        stale_unchanged = sha(active.read_bytes()) == before and not invalid_accepted and stale_disposition == "YIELD_STALE_GENERATION"
        if not stale_unchanged: raise RuntimeError("invalid/stale proposal mutated ACTIVE")
        return {"pid": os.getpid(), "reader_pids": [p.pid for p, _, _ in workers], "exit_codes": finish(workers),
                "rows": all_rows, "post_rows": post_rows, "replacement_intervals": replacements,
                "invalid_accepted": invalid_accepted, "stale_disposition": stale_disposition,
                "active_before_rejection_sha256": before, "active_after_rejection_sha256": sha(active.read_bytes()),
                "active_unchanged_rejections": stale_unchanged}
    finally:
        if any(p.is_alive() for p, _, _ in workers): finish(workers)


def arm_unsafe(root: Path, old_raw: bytes, new: dict) -> dict:
    folder = root / "unsafe"; folder.mkdir()
    active = folder / "ACTIVE.json"; active.write_bytes(old_raw)
    workers = launch(active); rows, writes = [], []
    candidate = canonical_bytes(new)
    try:
        phases = tuple(f"write_{i}" for i in range(1, 8))
        for n, phase in enumerate(phases):
            def rewrite(partial_barrier=None):
                with active.open("wb") as f:
                    f.write(candidate[:len(candidate)//2]); f.flush(); os.fsync(f.fileno())
                    if partial_barrier is not None:
                        ready, release = partial_barrier
                        ready.set()
                        if not release.wait(30): raise RuntimeError("partial writer barrier timed out")
                    else:
                        time.sleep(0.02)
                    f.write(candidate[len(candidate)//2:]); f.flush(); os.fsync(f.fileno())
            start = time.monotonic_ns()
            partial_barrier = (threading.Event(), threading.Event()) if n == 0 else None
            thread = threading.Thread(target=rewrite, args=(partial_barrier,)); thread.start()
            if partial_barrier is not None and not partial_barrier[0].wait(10): raise RuntimeError("partial-write barrier missing")
            rows += request(workers, phase, f"unsafe-{n+1}", n+1)
            if partial_barrier is not None: partial_barrier[1].set()
            thread.join(30)
            if thread.is_alive(): raise RuntimeError("unsafe writer timed out")
            writes.append({"phase": phase, "start_ns": start, "end_ns": time.monotonic_ns()})
        return {"pid": os.getpid(), "reader_pids": [p.pid for p, _, _ in workers], "exit_codes": finish(workers),
                "rows": rows, "write_intervals": writes}
    finally:
        if any(p.is_alive() for p, _, _ in workers): finish(workers)


def main():
    if any(OUT.iterdir()): raise RuntimeError("output mount is not empty")
    if os.environ.get("OBSTAC_IMAGE_ID") != IMAGE_ID: raise RuntimeError("image identity env mismatch")
    if os.environ.get("OBSTAC_CONSTRUCTION") != "0": raise RuntimeError("construction invocation mismatch")
    old_raw = SEED.read_bytes()
    if sha(old_raw) != SEED_SHA256: raise RuntimeError("seed digest mismatch")
    old = json.loads(old_raw)
    if old.get("generation") != OLD or not valid(old): raise RuntimeError("seed schema/digest gate failed")
    new = successor(old)
    root = OUT / "work"; root.mkdir()
    atomic = arm_atomic(root, old_raw, old, new)
    unsafe = arm_unsafe(root, old_raw, new)
    raw = {"allocation": "needle-publication-orbstack-bind-5066-20260928-01", "issue": 5073,
           "formal_invocations": 1, "python": sys.version, "platform": platform.platform(),
           "image_id": os.environ["OBSTAC_IMAGE_ID"], "source_commit": os.environ["OBSTAC_SOURCE_COMMIT"],
           "freeze_sha256": os.environ["OBSTAC_FREEZE_SHA256"], "construction": os.environ["OBSTAC_CONSTRUCTION"],
           "input_git_blob": "45b80150dac503f4eb6f3cb5d82f9afa2c587107", "input_sha256": sha(old_raw),
           "input_bytes": len(old_raw), "old_raw_sha256": sha(old_raw), "old_digest": old["payload_sha256"],
           "candidate_raw_sha256": sha(canonical_bytes(new)), "candidate_bytes": len(canonical_bytes(new)),
           "candidate_digest": new["payload_sha256"], "dispatch_count": 0, "authority_granted": False,
           "atomic": atomic, "unsafe": unsafe}
    (OUT / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"formal": "RAW_CAPTURED", "atomic_rows": len(atomic["rows"]),
                      "post_rows": len(atomic["post_rows"]), "unsafe_rows": len(unsafe["rows"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
