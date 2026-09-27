"""One-shot concurrent file-publication runner for Issue #5082."""
from __future__ import annotations

import json
import multiprocessing as mp
import os
from pathlib import Path
import sys
import time
import traceback

from model import INPUT_SHA256, OLD_GENERATION, git_blob_sha1, load_seed, package_for_sequence, parsed_package, sha256

PUBLICATIONS = 4096
READERS = 4
MAX_OBSERVATIONS_PER_READER = 50000
INPUT_GIT_BLOB = "45b80150dac503f4eb6f3cb5d82f9afa2c587107"


def _read_once(active: Path, phase) -> dict:
    phase_before = phase.value
    open_start = time.monotonic_ns()
    try:
        with active.open("rb") as stream:
            open_end = time.monotonic_ns()
            read_start = time.monotonic_ns()
            data = stream.read()
            read_end = time.monotonic_ns()
        package_ok, generation = parsed_package(data)
        return {
            "phase_before": phase_before,
            "open_start_ns": open_start,
            "open_end_ns": open_end,
            "read_start_ns": read_start,
            "read_end_ns": read_end,
            "bytes": len(data),
            "raw_sha256": sha256(data),
            "parse_ok": generation is not None,
            "generation": generation,
            "package_valid": package_ok,
            "pid": os.getpid(),
        }
    except Exception as error:
        ended = time.monotonic_ns()
        return {
            "phase_before": phase_before,
            "open_start_ns": open_start,
            "open_end_ns": ended,
            "read_start_ns": ended,
            "read_end_ns": ended,
            "bytes": 0,
            "raw_sha256": None,
            "parse_ok": False,
            "generation": None,
            "package_valid": False,
            "pid": os.getpid(),
            "error": type(error).__name__ + ":" + str(error),
        }


def _reader(active, log_path, summary_path, reader_index, start_event, stop_event,
            phase, ready_event, initial_event, partial_seen_event):
    ready_event.set()
    rows = 0
    partial_observations = 0
    limit_hit = False
    error = None
    try:
        if not start_event.wait(30):
            raise TimeoutError("start event timeout")
        with Path(log_path).open("x", encoding="utf-8", newline="\n") as log:
            row = _read_once(Path(active), phase)
            log.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            rows += 1
            initial_event.set()
            if row["phase_before"] == 1 and row["package_valid"] is not True:
                partial_observations += 1
                partial_seen_event.set()
            while not stop_event.is_set() and rows < MAX_OBSERVATIONS_PER_READER:
                row = _read_once(Path(active), phase)
                log.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
                rows += 1
                if row["phase_before"] == 1 and row["package_valid"] is not True:
                    partial_observations += 1
                    partial_seen_event.set()
            limit_hit = rows >= MAX_OBSERVATIONS_PER_READER and not stop_event.is_set()
            log.flush()
            os.fsync(log.fileno())
    except Exception:
        error = traceback.format_exc()
    finally:
        Path(summary_path).write_text(json.dumps({
            "reader_index": reader_index,
            "pid": os.getpid(),
            "rows": rows,
            "partial_observations": partial_observations,
            "limit_hit": limit_hit,
            "error": error,
        }, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _wait_all(events, timeout, name):
    deadline = time.monotonic() + timeout
    for event in events:
        if not event.wait(max(0.0, deadline - time.monotonic())):
            raise TimeoutError(name + " timeout")


def _run_arm(arm, seed_raw, seed_package, out: Path, ctx) -> dict:
    work = out / "work" / arm
    work.mkdir(parents=True, exist_ok=False)
    active = work / "ACTIVE.json"
    active.write_bytes(seed_raw)
    start_event = ctx.Event()
    stop_event = ctx.Event()
    phase = ctx.Value("i", 0)
    ready = [ctx.Event() for _ in range(READERS)]
    initial = [ctx.Event() for _ in range(READERS)]
    partial_seen = [ctx.Event() for _ in range(READERS)]
    processes = []
    log_records = []
    for index in range(READERS):
        log_path = out / "reads" / f"{arm}-{index}.jsonl"
        summary_path = out / "reads" / f"{arm}-{index}.summary.json"
        process = ctx.Process(
            target=_reader,
            args=(str(active), str(log_path), str(summary_path), index, start_event, stop_event,
                  phase, ready[index], initial[index], partial_seen[index]),
            name=f"publication-reader-{arm}-{index}",
        )
        process.start()
        processes.append((process, log_path, summary_path))
    publications = []
    writer_error = None
    partial_bytes = None
    start_ns = None
    end_ns = None
    try:
        _wait_all(ready, 20, arm + "_reader_ready")
        start_event.set()
        _wait_all(initial, 20, arm + "_initial_read")
        start_ns = time.monotonic_ns()
        if arm == "atomic":
            for sequence in range(1, PUBLICATIONS + 1):
                candidate = package_for_sequence(seed_package, sequence)
                temp = work / f".candidate-{sequence:04d}.tmp"
                temp.write_bytes(candidate)
                call_start = time.monotonic_ns()
                os.replace(temp, active)
                call_end = time.monotonic_ns()
                publications.append({
                    "sequence": sequence,
                    "generation": OLD_GENERATION + sequence,
                    "start_ns": call_start,
                    "end_ns": call_end,
                })
        elif arm == "diagnostic":
            sequence = PUBLICATIONS + 1
            candidate = package_for_sequence(seed_package, sequence)
            partial_bytes = len(candidate) // 2
            phase.value = 1
            call_start = time.monotonic_ns()
            with active.open("wb") as stream:
                stream.write(candidate[:partial_bytes])
                stream.flush()
                _wait_all(partial_seen, 20, "diagnostic_partial_readers")
                stream.write(candidate[partial_bytes:])
                stream.flush()
                call_end = time.monotonic_ns()
            phase.value = 2
            publications.append({
                "sequence": sequence,
                "generation": OLD_GENERATION + sequence,
                "start_ns": call_start,
                "end_ns": call_end,
                "partial_bytes": partial_bytes,
            })
        else:
            raise ValueError("unknown publication arm")
        end_ns = time.monotonic_ns()
    except Exception:
        writer_error = traceback.format_exc()
    finally:
        phase.value = 2
        stop_event.set()
        for process, _, _ in processes:
            process.join(20)
        for process, _, _ in processes:
            if process.is_alive():
                process.terminate()
                process.join(5)
        for process, log_path, summary_path in processes:
            summary = {}
            if summary_path.exists():
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
            log_records.append({
                "reader_index": len(log_records),
                "pid": process.pid,
                "exit_code": process.exitcode,
                "path": str(log_path.relative_to(out)).replace("\\", "/"),
                "summary": summary,
            })
    return {
        "arm": arm,
        "writer_start_ns": start_ns,
        "writer_end_ns": end_ns,
        "writer_error": writer_error,
        "publication_count": len(publications),
        "publications": publications,
        "reader_count": len(log_records),
        "readers": log_records,
        "reader_initial_samples_ready": sum(event.is_set() for event in initial),
        "reader_partial_barrier_ready": sum(event.is_set() for event in partial_seen) if arm == "diagnostic" else None,
        "partial_bytes": partial_bytes,
    }


def main() -> int:
    out = Path("/out")
    if not out.is_dir():
        raise RuntimeError("/out must be a fresh writable mounted directory")
    frozen_image = os.environ.get("FROZEN_IMAGE_ID")
    if frozen_image != "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9":
        raise RuntimeError("frozen image identity environment mismatch")
    seed_raw, seed_package = load_seed(Path("/src"))
    if git_blob_sha1(seed_raw) != INPUT_GIT_BLOB:
        raise RuntimeError("seed Git blob identity mismatch")
    if (out / "work").exists() or (out / "reads").exists():
        raise RuntimeError("formal output contains a pre-existing run directory")
    (out / "reads").mkdir()
    ctx = mp.get_context("spawn")
    arms = []
    for arm in ("atomic", "diagnostic"):
        arms.append(_run_arm(arm, seed_raw, seed_package, out, ctx))
    raw = {
        "schema": "needle-publication-overlap-raw-v1",
        "allocation": "needle-cross-process-publication-overlap-5066-v3-20260928-01",
        "issue": 5082,
        "formal_invocations": 1,
        "image_id": frozen_image,
        "input_git_blob": git_blob_sha1(seed_raw),
        "input_sha256": sha256(seed_raw),
        "input_bytes": len(seed_raw),
        "publication_operations_expected": PUBLICATIONS,
        "reader_count_per_arm": READERS,
        "max_observations_per_reader": MAX_OBSERVATIONS_PER_READER,
        "dispatch_count": 0,
        "authority_granted": False,
        "arms": arms,
    }
    (out / "raw.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "raw_written": True,
        "publication_counts": {a["arm"]: a["publication_count"] for a in arms},
        "reader_exit_codes": {a["arm"]: [r["exit_code"] for r in a["readers"]] for a in arms},
    }, sort_keys=True))
    return 0 if all(a["writer_error"] is None for a in arms) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print(traceback.format_exc(), file=sys.stderr)
        raise
