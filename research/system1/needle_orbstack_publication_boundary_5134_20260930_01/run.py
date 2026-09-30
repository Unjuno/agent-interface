"""One-transition OrbStack bind-mount boundary pilot; construction class only."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import multiprocessing as mp
import os
from pathlib import Path
import time

EXP = Path("/src/research/system1/needle_orbstack_publication_boundary_5134_20260930_01")
SEED = Path("/src/research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json")
OUT = Path("/out")
ALLOCATION = "needle-publication-orbstack-boundary-20260930-01"
IMAGE = "sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e"
READERS = 4


def canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def package_digest(obj: dict) -> str:
    body = {k: v for k, v in obj.items() if k != "payload_sha256"}
    return digest(canonical(body))


def reader(conn, path: str, index: int) -> None:
    held = None
    try:
        while True:
            command = conn.recv()
            if command == "open":
                held = open(path, "rb")
                conn.send({"event": "opened", "reader": index, "pid": os.getpid(),
                           "fd_open_ns": time.monotonic_ns()})
            elif command == "atomic_read":
                start = time.monotonic_ns(); held.seek(0); held_raw = held.read(); end = time.monotonic_ns()
                path_start = time.monotonic_ns(); path_raw = Path(path).read_bytes(); path_end = time.monotonic_ns()
                conn.send({"event": "atomic_read", "reader": index, "pid": os.getpid(),
                           "fd_read_start_ns": start, "fd_read_end_ns": end,
                           "held_b64": base64.b64encode(held_raw).decode(),
                           "held_sha256": digest(held_raw),
                           "path_read_start_ns": path_start, "path_read_end_ns": path_end,
                           "path_b64": base64.b64encode(path_raw).decode(),
                           "path_sha256": digest(path_raw)})
                held.close(); held = None
            elif command in ("partial_read", "complete_read"):
                start = time.monotonic_ns(); raw = Path(path).read_bytes(); end = time.monotonic_ns()
                conn.send({"event": command, "reader": index, "pid": os.getpid(),
                           "read_start_ns": start, "read_end_ns": end,
                           "bytes_b64": base64.b64encode(raw).decode(), "sha256": digest(raw)})
            elif command == "stop":
                conn.send({"event": "stopped", "reader": index, "pid": os.getpid()})
                return
            else:
                raise ValueError(f"unknown command: {command!r}")
    finally:
        if held is not None:
            held.close()
        conn.close()


def start_readers(path: Path):
    ctx = mp.get_context("spawn")
    workers = []
    for i in range(READERS):
        parent, child = ctx.Pipe()
        proc = ctx.Process(target=reader, args=(child, str(path), i))
        proc.start(); child.close(); workers.append((proc, parent))
    pids = [p.pid for p, _ in workers]
    if len(set(pids)) != READERS or os.getpid() in pids:
        raise RuntimeError("reader process identity mismatch")
    return workers


def command_all(workers, command: str) -> list[dict]:
    for _, conn in workers:
        conn.send(command)
    rows = []
    for i, (_, conn) in enumerate(workers):
        if not conn.poll(15):
            raise TimeoutError(f"reader {i} timeout on {command}")
        row = conn.recv()
        expected_event = {"open": "opened", "stop": "stopped"}.get(command, command)
        if row.get("reader") != i or row.get("event") != expected_event:
            raise RuntimeError(f"reader response mismatch: {row!r}")
        rows.append(row)
    return rows


def stop_readers(workers) -> list[int]:
    command_all(workers, "stop")
    for proc, conn in workers:
        proc.join(10); conn.close()
        if proc.is_alive():
            proc.terminate(); proc.join()
    exits = [p.exitcode for p, _ in workers]
    if exits != [0] * READERS:
        raise RuntimeError(f"reader exits: {exits!r}")
    return exits


def derive(seed: dict) -> tuple[bytes, bytes]:
    old = copy.deepcopy(seed)
    new = copy.deepcopy(seed)
    new["generation"] = old["generation"] + 1
    new["provenance"] = dict(new["provenance"])
    new["provenance"]["allocation"] = ALLOCATION
    new["provenance"]["predecessor_issue"] = 5134
    new["payload_sha256"] = package_digest(new)
    return canonical(old), canonical(new)


def atomic_arm(root: Path, old: bytes, new: bytes) -> dict:
    folder = root / "atomic"; folder.mkdir()
    active = folder / "ACTIVE.json"; active.write_bytes(old)
    staged = folder / "candidate.tmp"
    workers = start_readers(active)
    try:
        opened = command_all(workers, "open")
        staged.write_bytes(new)
        with staged.open("rb") as f:
            os.fsync(f.fileno())
        start = time.monotonic_ns(); os.replace(staged, active); returned = time.monotonic_ns()
        rows = command_all(workers, "atomic_read")
        return {"reader_pids": [p.pid for p, _ in workers], "opened": opened,
                "replace_start_ns": start, "replace_return_ns": returned,
                "rows": rows, "exit_codes": stop_readers(workers)}
    finally:
        if any(p.is_alive() for p, _ in workers):
            stop_readers(workers)


def unsafe_arm(root: Path, old: bytes, new: bytes) -> dict:
    folder = root / "unsafe"; folder.mkdir()
    active = folder / "ACTIVE.json"; active.write_bytes(old)
    workers = start_readers(active)
    try:
        prefix = new[:len(new)//2]
        write_start = time.monotonic_ns()
        with active.open("wb") as stream:
            stream.write(prefix); stream.flush(); os.fsync(stream.fileno())
            partial_rows = command_all(workers, "partial_read")
            write_complete_start = time.monotonic_ns()
            stream.write(new[len(prefix):]); stream.flush(); os.fsync(stream.fileno())
        write_end = time.monotonic_ns()
        complete_rows = command_all(workers, "complete_read")
        return {"reader_pids": [p.pid for p, _ in workers],
                "write_start_ns": write_start, "write_complete_start_ns": write_complete_start,
                "write_end_ns": write_end, "expected_prefix_b64": base64.b64encode(prefix).decode(),
                "expected_complete_b64": base64.b64encode(new).decode(),
                "partial_rows": partial_rows, "complete_rows": complete_rows,
                "exit_codes": stop_readers(workers)}
    finally:
        if any(p.is_alive() for p, _ in workers):
            stop_readers(workers)


def main() -> None:
    if os.environ.get("OBSTAC_CONSTRUCTION") != "1":
        raise RuntimeError("this pilot must run only as OBSTAC_CONSTRUCTION=1")
    if os.environ.get("OBSTAC_IMAGE_ID") != IMAGE:
        raise RuntimeError("image identity mismatch")
    if not os.environ.get("OBSTAC_SOURCE_COMMIT") or not os.environ.get("OBSTAC_FREEZE_SHA256"):
        raise RuntimeError("missing Obstac provenance environment")
    if {p.name for p in OUT.iterdir()} != {"invocation_receipt.json"}:
        raise RuntimeError("output must contain only the host-created invocation receipt")
    receipt = json.loads((OUT / "invocation_receipt.json").read_text())
    for key, envkey in (("source_commit", "OBSTAC_SOURCE_COMMIT"), ("image_id", "OBSTAC_IMAGE_ID"),
                        ("freeze_sha256", "OBSTAC_FREEZE_SHA256"), ("construction", "OBSTAC_CONSTRUCTION")):
        if receipt.get(key) != os.environ.get(envkey):
            raise RuntimeError(f"receipt/environment mismatch: {key}")
    seed_raw = SEED.read_bytes()
    if digest(seed_raw) != "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a":
        raise RuntimeError("seed digest mismatch")
    old, new = derive(json.loads(seed_raw))
    if json.loads(old).get("generation") != 3788 or json.loads(new).get("generation") != 3789:
        raise RuntimeError("generation mismatch")
    root = OUT / "work"; root.mkdir()
    atomic = atomic_arm(root, old, new)
    unsafe = unsafe_arm(root, old, new)
    raw = {"allocation": ALLOCATION, "issue": 5134, "publisher_pid": os.getpid(),
           "class": "CONSTRUCTION_BOUNDARY_PILOT",
           "formal_allocation_consumed": False, "formal_denominators_met": False,
           "construction": "1", "source_commit": receipt["source_commit"],
           "image_id": IMAGE, "platform": "linux/arm64", "seed_sha256": digest(seed_raw),
           "old_b64": base64.b64encode(old).decode(), "new_b64": base64.b64encode(new).decode(),
           "old_sha256": digest(old), "new_sha256": digest(new),
           "atomic": atomic, "unsafe": unsafe}
    raw_bytes = (json.dumps(raw, sort_keys=True, indent=2) + "\n").encode()
    (OUT / "raw.json").write_bytes(raw_bytes)
    print(json.dumps({"status": "RAW_CAPTURED", "atomic_readers": len(atomic["rows"]),
                      "unsafe_readers": len(unsafe["partial_rows"]),
                      "raw_sha256": digest(raw_bytes)}, sort_keys=True))


if __name__ == "__main__":
    main()
