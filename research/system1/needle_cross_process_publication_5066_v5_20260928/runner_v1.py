"""Single orchestration for Issue #5082 process-overlap experiment (not yet frozen)."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import queue
import tempfile
import time
import traceback

REPLACEMENTS = 4096
READERS = 4
MAX_SECONDS = 90


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def package_bytes(seed: dict, generation: int) -> bytes:
    package = json.loads(json.dumps(seed))
    package["generation"] = generation
    package["provenance"]["seed"] = generation
    return (json.dumps(package, sort_keys=True, separators=(",", ":")) + "\n").encode()


def append_jsonl(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()


def _reader(reader_index: int, active: str, ready, start, finished,
            out_file: str, deadline_ns: int, seed_hash: str, seed_len: int) -> None:
    path = Path(active)
    out = Path(out_file)
    pid = os.getpid()
    ready.put({"reader_index": reader_index, "pid": pid, "ready_ns": time.monotonic_ns()})
    if not start.wait(timeout=20):
        append_jsonl(out, {"kind": "reader_error", "reader_index": reader_index,
                           "pid": pid, "error": "start_gate_timeout"})
        return
    index = 0
    while not finished.is_set() and time.monotonic_ns() < deadline_ns:
        begin = time.monotonic_ns()
        try:
            with path.open("rb") as stream:
                data = stream.read()
            end = time.monotonic_ns()
            try:
                obj = json.loads(data)
                generation = obj.get("generation")
                valid = (generation == 3788 and digest(data) == seed_hash and len(data) == seed_len)
                if generation != 3788:
                    valid = isinstance(generation, int) and data == package_bytes(obj, generation)
            except Exception:
                generation, valid = None, False
            append_jsonl(out, {"kind": "read", "reader_index": reader_index,
                               "reader_pid": pid, "read_index": index,
                               "open_start_ns": begin, "open_end_ns": end,
                               "bytes": len(data), "sha256": digest(data),
                               "data_b64": base64.b64encode(data).decode("ascii"),
                               "generation": generation, "valid": valid})
        except Exception as exc:
            end = time.monotonic_ns()
            append_jsonl(out, {"kind": "read", "reader_index": reader_index,
                               "reader_pid": pid, "read_index": index,
                               "open_start_ns": begin, "open_end_ns": end,
                               "error": type(exc).__name__})
        index += 1
    append_jsonl(out, {"kind": "reader_exit", "reader_index": reader_index,
                       "reader_pid": pid, "read_count": index,
                       "exit_ns": time.monotonic_ns()})


def _publisher(active: str, seed: dict, start, finished, out_file: str,
               ready_count: int) -> None:
    path, out = Path(active), Path(out_file)
    if ready_count != READERS:
        append_jsonl(out, {"kind": "publisher_error", "error": "reader_ready_count",
                           "ready_count": ready_count})
        finished.set()
        return
    start.set()
    try:
        for index in range(REPLACEMENTS):
            generation = 3789 + index
            payload = package_bytes(seed, generation)
            fd, temp_name = tempfile.mkstemp(prefix=".candidate-", dir=path.parent)
            tmp = Path(temp_name)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(payload)
                    stream.flush()
                call_start = time.monotonic_ns()
                os.replace(tmp, path)
                call_end = time.monotonic_ns()
            finally:
                if tmp.exists():
                    tmp.unlink()
            append_jsonl(out, {"kind": "replace", "replace_index": index,
                               "generation": generation, "sha256": digest(payload),
                               "start_ns": call_start, "end_ns": call_end})
    except BaseException as exc:
        append_jsonl(out, {"kind": "publisher_error", "error": type(exc).__name__,
                           "detail": str(exc), "traceback": traceback.format_exc()})
    finally:
        finished.set()


def _diagnostic_reader(reader_index: int, active: str, midpoint, observed,
                       out_file: str) -> None:
    pid = os.getpid()
    out = Path(out_file)
    if not midpoint.wait(timeout=20):
        append_jsonl(out, {"kind": "diagnostic_error", "reader_index": reader_index,
                           "reader_pid": pid, "error": "midpoint_timeout"})
        observed.put({"reader_index": reader_index, "pid": pid, "ok": False})
        return
    start_ns = time.monotonic_ns()
    data = Path(active).read_bytes()
    end_ns = time.monotonic_ns()
    try:
        obj = json.loads(data)
        valid = data == package_bytes(obj, obj["generation"])
    except Exception:
        valid = False
    append_jsonl(out, {"kind": "diagnostic_read", "reader_index": reader_index,
                       "reader_pid": pid, "open_start_ns": start_ns,
                       "open_end_ns": end_ns, "bytes": len(data),
                       "sha256": digest(data), "valid": valid,
                       "partial_b64": base64.b64encode(data).decode("ascii")})
    observed.put({"reader_index": reader_index, "pid": pid, "ok": not valid,
                  "sha256": digest(data), "bytes": len(data)})


def run_diagnostic(seed_bytes: bytes, seed: dict, out: Path) -> bool:
    root = out / "diagnostic"
    root.mkdir()
    active = root / "active.json"
    active.write_bytes(seed_bytes)
    candidate = package_bytes(seed, 3789)
    ctx = mp.get_context("spawn")
    midpoint, observed = ctx.Event(), ctx.Queue()
    readers = [ctx.Process(target=_diagnostic_reader,
                           args=(i, str(active), midpoint, observed,
                                 str(root / f"reader-{i}.jsonl")))
               for i in range(READERS)]
    for proc in readers:
        proc.start()
    try:
        with active.open("wb") as stream:
            stream.write(candidate[:len(candidate) // 2])
            stream.flush()
            os.fsync(stream.fileno())
            midpoint.set()
            observations = [observed.get(timeout=20) for _ in readers]
            stream.write(candidate[len(candidate) // 2:])
            stream.flush()
            os.fsync(stream.fileno())
        for proc in readers:
            proc.join(timeout=5)
        (root / "observations.json").write_text(
            json.dumps(observations, sort_keys=True) + "\n", encoding="utf-8")
        return (len(observations) == READERS and all(x.get("ok") for x in observations)
                and active.read_bytes() == candidate)
    finally:
        for proc in readers:
            if proc.is_alive():
                proc.terminate()
                proc.join()


def run_atomic(seed_path: Path, out: Path) -> int:
    if not out.is_dir() or any(out.iterdir()):
        raise RuntimeError("raw output must be a pre-created empty directory")
    seed_bytes = seed_path.read_bytes()
    seed = json.loads(seed_bytes)
    seed_hash = digest(seed_bytes)
    root = out / "atomic"
    root.mkdir()
    active = root / "active.json"
    active.write_bytes(seed_bytes)
    ctx = mp.get_context("spawn")
    ready, start, finished = ctx.Queue(), ctx.Event(), ctx.Event()
    deadline_ns = time.monotonic_ns() + MAX_SECONDS * 1_000_000_000
    readers = [ctx.Process(target=_reader,
                           args=(i, str(active), ready, start, finished,
                                 str(root / f"reader-{i}.jsonl"), deadline_ns,
                                 seed_hash, len(seed_bytes)))
               for i in range(READERS)]
    for process in readers:
        process.start()
    announced = []
    until = time.monotonic() + 20
    while len(announced) < READERS and time.monotonic() < until:
        try:
            announced.append(ready.get(timeout=0.1))
        except queue.Empty:
            if any(not proc.is_alive() for proc in readers):
                break
    if len(announced) == READERS:
        _publisher(str(active), seed, start, finished, root / "publisher.jsonl", len(announced))
    else:
        finished.set()
        append_jsonl(root / "publisher.jsonl", {"kind": "publisher_error",
                                                  "error": "reader_readiness_incomplete",
                                                  "ready": announced})
    for process in readers:
        process.join(timeout=MAX_SECONDS + 5)
        if process.is_alive():
            process.terminate()
            process.join()
    exits = [{"reader_index": i, "pid": proc.pid, "exitcode": proc.exitcode}
             for i, proc in enumerate(readers)]
    (root / "process_exits.json").write_text(json.dumps(exits, sort_keys=True) + "\n")
    atomic_ok = len(announced) == READERS and all(x["exitcode"] == 0 for x in exits)
    diag_ok = run_diagnostic(seed_bytes, seed, out)
    (out / "construction_disposition.json").write_text(
        json.dumps({"atomic_processes_exit_zero": atomic_ok,
                    "diagnostic_partial_observed_by_all": diag_ok}, sort_keys=True) + "\n",
        encoding="utf-8")
    return 0 if atomic_ok and diag_ok else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    return run_atomic(args.seed, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
