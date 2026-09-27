"""Frozen finite-schedule multi-process publisher/reader probe for #5045.

Formal invocation only inside the pinned offline Docker image. Construction
unit tests must not import or invoke main().
"""
from __future__ import annotations

import copy
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import shlex
import sys
import time
import traceback
from typing import Any

from protocol import (
    NEW_GENERATION,
    OLD_GENERATION,
    READER_COUNT,
    candidate_from,
    canonical_bytes,
    payload_digest,
    proposal_disposition,
    validate_package,
)

SRC = Path("/src")
OUT = Path("/out")
SEED_PACKAGE = SRC / "skill3788.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_observation(path: str, phase: str, request_id: str) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    try:
        package = json.loads(raw)
        valid = validate_package(package)
        generation = package.get("generation")
        embedded_digest = package.get("payload_sha256")
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError, TypeError):
        package = None
        valid = False
        generation = None
        embedded_digest = None
    return {
        "phase": phase,
        "request_id": request_id,
        "pid": os.getpid(),
        "bytes": len(raw),
        "raw_sha256": sha(raw),
        "parse_ok": package is not None,
        "package_valid": valid,
        "generation": generation,
        "embedded_digest": embedded_digest,
    }


def reader_worker(index: int, active: str, commands, responses) -> None:
    while True:
        command = commands.get()
        if command is None:
            return
        phase, request_id = command
        try:
            record = read_observation(active, phase, request_id)
            record["reader_index"] = index
        except BaseException as exc:
            record = {
                "phase": phase,
                "request_id": request_id,
                "pid": os.getpid(),
                "reader_index": index,
                "reader_error": type(exc).__name__ + ":" + str(exc),
            }
        responses.put(record)


def write_bytes(path: Path, data: bytes) -> None:
    path.write_bytes(data)


def ask_all(active: Path, workers, phase: str, serial: int, records: list[dict]) -> list[dict]:
    request_id = f"{phase}-{serial:02d}"
    for index, (process, commands, _) in enumerate(workers):
        if not process.is_alive():
            raise RuntimeError(f"reader {index} exited before {request_id}")
        commands.put((phase, request_id))
    rows = []
    for index, (_, _, responses) in enumerate(workers):
        row = responses.get(timeout=5.0)
        if row.get("request_id") != request_id or row.get("reader_index") != index:
            raise RuntimeError(f"reader response mismatch for {request_id}: {row}")
        rows.append(row)
    records.extend(rows)
    return rows


def expect_generation(rows: list[dict], generation: int, valid: bool = True) -> None:
    if any(row.get("generation") != generation or row.get("package_valid") is not valid for row in rows):
        raise RuntimeError(f"unexpected observations; expected generation={generation}, valid={valid}: {rows}")


def run_arm(root: Path, arm: str, old_raw: bytes, old: dict, new: dict) -> dict:
    case = root / arm
    case.mkdir()
    active = case / "ACTIVE.json"
    records: list[dict] = []
    write_bytes(active, old_raw)
    workers = []
    for index in range(READER_COUNT):
        commands = mp.Queue()
        responses = mp.Queue()
        process = mp.Process(target=reader_worker, args=(index, str(active), commands, responses))
        process.start()
        workers.append((process, commands, responses))
    pids = [process.pid for process, _, _ in workers]
    if len(set(pids)) != READER_COUNT or os.getpid() in pids:
        raise RuntimeError(f"reader processes are not independent: publisher={os.getpid()} readers={pids}")
    phase_serial = 0
    stopped = False

    def stop_workers() -> list[int | None]:
        nonlocal stopped
        if not stopped:
            for _, commands, _ in workers:
                commands.put(None)
            for process, _, _ in workers:
                process.join(timeout=3.0)
                if process.is_alive():
                    process.terminate()
                    process.join()
            stopped = True
        codes = [process.exitcode for process, _, _ in workers]
        if any(code != 0 for code in codes):
            raise RuntimeError(f"reader process exits: {codes}")
        return codes

    def ask(phase: str):
        nonlocal phase_serial
        phase_serial += 1
        return ask_all(active, workers, phase, phase_serial, records)

    try:
        if arm == "atomic":
            expect_generation(ask("atomic_before_validation"), OLD_GENERATION)
            candidate_path = case / "candidate.tmp"
            candidate_raw = canonical_bytes(new)
            write_bytes(candidate_path, candidate_raw)
            # Deliberately delayed validation is represented by a parent/reader
            # phase barrier, not by an uncontrolled sleep.
            if not validate_package(json.loads(candidate_path.read_bytes())):
                raise RuntimeError("candidate failed validation before publish")
            expect_generation(ask("atomic_candidate_ready_unpublished"), OLD_GENERATION)
            os.replace(candidate_path, active)
            rows = ask("atomic_after_publish")
            expect_generation(rows, NEW_GENERATION)
            stale = proposal_disposition(OLD_GENERATION, NEW_GENERATION)
            current = proposal_disposition(NEW_GENERATION, NEW_GENERATION)
            before = sha(active.read_bytes())
            invalid = copy.deepcopy(new)
            invalid["payload_sha256"] = "0" * 64
            invalid_path = case / "invalid.tmp"
            write_bytes(invalid_path, canonical_bytes(invalid))
            invalid_accepted = validate_package(json.loads(invalid_path.read_bytes()))
            if invalid_accepted:
                raise RuntimeError("invalid candidate unexpectedly validated")
            after = sha(active.read_bytes())
            if before != after:
                raise RuntimeError("invalid candidate mutated ACTIVE")
            expect_generation(ask("invalid_candidate_refused"), NEW_GENERATION)
            exit_codes = stop_workers()
            return {
                "arm": arm,
                "publisher_pid": os.getpid(),
                "reader_pids": pids,
                "reader_exit_codes": exit_codes,
                "observations": records,
                "stale_proposal": {"generation": OLD_GENERATION, "active_generation": NEW_GENERATION, "disposition": stale, "dispatch": False},
                "current_proposal": {"generation": NEW_GENERATION, "active_generation": NEW_GENERATION, "disposition": current, "dispatch": False},
                "invalid_candidate_accepted": invalid_accepted,
                "active_before_invalid_sha256": before,
                "active_after_invalid_sha256": after,
            }
        if arm == "diagnostic":
            expect_generation(ask("diagnostic_before_write"), OLD_GENERATION)
            candidate_raw = canonical_bytes(new)
            with active.open("wb") as stream:
                stream.write(candidate_raw[: len(candidate_raw) // 2])
                stream.flush()
                os.fsync(stream.fileno())
            partial = ask("diagnostic_partial_write")
            if not any(not row.get("package_valid") for row in partial):
                raise RuntimeError("diagnostic failed to expose partial bytes")
            with active.open("ab") as stream:
                stream.write(candidate_raw[len(candidate_raw) // 2 :])
                stream.flush()
                os.fsync(stream.fileno())
            expect_generation(ask("diagnostic_after_write"), NEW_GENERATION)
            exit_codes = stop_workers()
            return {
                "arm": arm,
                "publisher_pid": os.getpid(),
                "reader_pids": pids,
                "reader_exit_codes": exit_codes,
                "observations": records,
                "partial_invalid_reader_count": sum(not row.get("package_valid") for row in partial),
                "dispatch_count": 0,
            }
        raise ValueError(f"unknown arm: {arm}")
    finally:
        stop_workers()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if any(OUT.iterdir()):
        raise RuntimeError("formal output directory is not empty")
    old_raw = SEED_PACKAGE.read_bytes()
    old = json.loads(old_raw)
    if old.get("generation") != OLD_GENERATION or not validate_package(old):
        raise RuntimeError("exact seed package failed frozen schema/digest gate")
    new = candidate_from(old)
    if not validate_package(new) or new.get("generation") != NEW_GENERATION:
        raise RuntimeError("candidate construction failed")
    root = Path("/tmp/issue5045")
    root.mkdir()
    atomic = run_arm(root, "atomic", old_raw, old, new)
    diagnostic = run_arm(root, "diagnostic", old_raw, old, new)
    raw = {
        "allocation": "needle-cross-process-publication-5045-v1",
        "issue": 5045,
        "formal_invocations": 1,
        "publisher_container_pid": os.getpid(),
        "python": sys.version,
        "platform": platform.platform(),
        "image_id": os.environ.get("FROZEN_IMAGE_ID"),
        "command": shlex.join([sys.executable, str(SRC / "runner.py")]),
        "input_git_blob": "45b80150dac503f4eb6f3cb5d82f9afa2c587107",
        "input_sha256": sha(old_raw),
        "input_bytes": len(old_raw),
        "candidate_sha256": new["payload_sha256"],
        "reader_count_per_arm": READER_COUNT,
        "query_count": len(atomic["observations"]) + len(diagnostic["observations"]),
        "dispatch_count": 0,
        "authority_granted": False,
        "arms": [atomic, diagnostic],
    }
    path = OUT / "raw.json"
    path.write_bytes(canonical_bytes(raw) + b"\n")
    print(json.dumps({"raw_sha256": sha(path.read_bytes()), "query_count": raw["query_count"], "publisher_pid": os.getpid()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BaseException as exc:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "runner_error.json").write_text(
            json.dumps({"type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc()}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        raise

