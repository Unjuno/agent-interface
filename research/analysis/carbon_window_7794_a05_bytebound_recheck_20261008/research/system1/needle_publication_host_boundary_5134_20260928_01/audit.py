"""Independent auditor for #5134's one-shot host boundary raw capture."""
from __future__ import annotations

import base64
import copy
import hashlib
import json
from pathlib import Path

ALLOCATION = "needle-publication-host-boundary-5134-20260928-01"
ISSUE = 5134
SEED_SHA256 = "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a"
SEED_BLOB = "45b80150dac503f4eb6f3cb5d82f9afa2c587107"
GENERATIONS = tuple(range(3789, 3796))
PHASES = tuple(f"phase_{i}" for i in range(1, 8))
READERS = 4


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def expected_package(seed: dict, generation: int) -> bytes:
    value = copy.deepcopy(seed)
    value["generation"] = generation
    value["provenance"] = dict(value["provenance"])
    value["provenance"]["allocation"] = ALLOCATION
    value["provenance"]["predecessor_issue"] = ISSUE
    value.pop("payload_sha256", None)
    value["payload_sha256"] = sha(canonical(value))
    return canonical(value)


def decode_row(row: object, errors: list[str], label: str, key: str) -> bytes | None:
    if not isinstance(row, dict):
        errors.append(label + "_not_object")
        return None
    try:
        data = base64.b64decode(row[key], validate=True)
    except Exception:
        errors.append(label + "_base64")
        return None
    expected_sha = row.get(key.replace("_b64", "_sha256"))
    if sha(data) != expected_sha:
        errors.append(label + "_sha256")
        return None
    return data


def audit_raw(raw: object, seed_raw: bytes, source_dir: Path | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(raw, dict):
        return ["raw_not_object"]
    if raw.get("schema") != "needle-publication-host-boundary-raw-v1": errors.append("schema")
    if raw.get("allocation") != ALLOCATION: errors.append("allocation")
    if raw.get("issue") != ISSUE: errors.append("issue")
    if raw.get("status") != "CAPTURED": errors.append("status")
    if raw.get("docker_invocations") != 0 or raw.get("container_id") is not None: errors.append("container_boundary")
    if raw.get("seed_sha256") != SEED_SHA256 or sha(seed_raw) != SEED_SHA256: errors.append("seed_sha256")
    if raw.get("seed_git_blob") != SEED_BLOB or blob_id(seed_raw) != SEED_BLOB: errors.append("seed_blob")
    if raw.get("seed_bytes") != len(seed_raw): errors.append("seed_bytes")
    if raw.get("phases") != list(PHASES) or raw.get("generations") != list(GENERATIONS): errors.append("schedule")
    if raw.get("readers_per_phase") != READERS: errors.append("readers_per_phase")
    # Platform identity is bound in run_receipt.json by audit_bundle; raw must carry the frozen commit.
    if not isinstance(raw.get("source_commit"), str) or len(raw["source_commit"]) != 40: errors.append("source_commit")
    if not isinstance(raw.get("source_tree"), str) or len(raw["source_tree"]) != 40: errors.append("source_tree")
    if raw.get("frozen_main") != "16421aefa2ec357b79e3fd3dc307b32955bc6fab": errors.append("frozen_main")
    seed = None
    try:
        seed = json.loads(seed_raw)
    except Exception:
        errors.append("seed_json")
    expected = {g: expected_package(seed, g) for g in GENERATIONS} if seed is not None else {}
    previous = seed_raw
    atomic = raw.get("atomic_rows")
    if not isinstance(atomic, list) or len(atomic) != len(PHASES) * READERS:
        errors.append("atomic_denominator")
        atomic = atomic if isinstance(atomic, list) else []
    unsafe = raw.get("unsafe_rows")
    if not isinstance(unsafe, list) or len(unsafe) != len(PHASES) * READERS:
        errors.append("unsafe_denominator")
        unsafe = unsafe if isinstance(unsafe, list) else []
    for phase, generation in zip(PHASES, GENERATIONS, strict=True):
        want = [row for row in atomic if isinstance(row, dict) and row.get("phase") == phase]
        if len(want) != READERS or len({row.get("reader") for row in want}) != READERS or len({row.get("pid") for row in want}) != READERS:
            errors.append(f"atomic_readers_{phase}")
        for row in want:
            label = f"atomic_{phase}_{row.get('reader')}"
            if row.get("generation") != generation: errors.append(label + "_generation")
            if row.get("child_exit_codes") != [0] * READERS: errors.append(label + "_child_exit_codes")
            times = [row.get(k) for k in ("fd_open_ns", "replace_start_ns", "replace_return_ns", "fd_read_start_ns", "fd_read_end_ns")]
            if any(not isinstance(v, int) for v in times) or times != sorted(times) or len(set(times)) != len(times): errors.append(label + "_fd_order")
            if row.get("fresh_open_ns", 0) < row.get("replace_return_ns", 0): errors.append(label + "_fresh_open_order")
            held = decode_row(row, errors, label + "_held", "held_b64")
            fresh = decode_row(row, errors, label + "_fresh", "fresh_b64")
            if held != previous: errors.append(label + "_held_not_old")
            if fresh != expected.get(generation): errors.append(label + "_fresh_not_new")
        previous = expected.get(generation, b"")
    for phase, generation in zip(PHASES, GENERATIONS, strict=True):
        want = [row for row in unsafe if isinstance(row, dict) and row.get("phase") == phase]
        if len(want) != READERS or len({row.get("reader") for row in want}) != READERS or len({row.get("pid") for row in want}) != READERS:
            errors.append(f"unsafe_readers_{phase}")
        for row in want:
            label = f"unsafe_{phase}_{row.get('reader')}"
            if row.get("generation") != generation: errors.append(label + "_generation")
            if row.get("child_exit_codes") != [0] * READERS: errors.append(label + "_child_exit_codes")
            times = [row.get(k) for k in ("fd_open_ns", "write_start_ns", "truncate_ns", "partial_complete_ns", "read_start_ns", "read_end_ns", "complete_write_start_ns", "write_end_ns")]
            if any(not isinstance(v, int) for v in times) or times != sorted(times) or len(set(times)) != len(times): errors.append(label + "_writer_reader_order")
            partial = decode_row(row, errors, label + "_partial", "partial_b64")
            held = decode_row(row, errors, label + "_held", "held_b64")
            fresh = decode_row(row, errors, label + "_fresh", "fresh_b64")
            completed = decode_row(row, errors, label + "_completed", "completed_b64")
            if not partial or partial == expected.get(generation) or not expected.get(generation, b"").startswith(partial): errors.append(label + "_not_strict_prefix")
            if held != partial or fresh != partial: errors.append(label + "_partial_not_observed")
            if completed != expected.get(generation): errors.append(label + "_completion_not_exact")
    if source_dir is not None:
        freeze = json.loads((source_dir / "FREEZE.json").read_text())
        if raw.get("source_commit") != freeze.get("base_main_sha"): errors.append("freeze_commit_binding")
        if raw.get("source_sha256") != freeze.get("source_sha256"): errors.append("freeze_source_inventory")
        for name, expected_hash in freeze.get("source_sha256", {}).items():
            if sha((source_dir / name).read_bytes()) != expected_hash: errors.append("source_hash_" + name)
    return errors


def audit_bundle(bundle: Path, seed_raw: bytes, source_dir: Path) -> dict:
    raw = json.loads((bundle / "raw.json").read_text())
    receipt = json.loads((bundle / "run_receipt.json").read_text())
    errors = audit_raw(raw, seed_raw, source_dir)
    if receipt.get("allocation") != ALLOCATION: errors.append("receipt_allocation")
    if receipt.get("issue") != ISSUE: errors.append("receipt_issue")
    if receipt.get("source_commit") != raw.get("source_commit"): errors.append("receipt_commit")
    if receipt.get("source_tree") != raw.get("source_tree"): errors.append("receipt_tree")
    if receipt.get("frozen_main") != raw.get("frozen_main"): errors.append("receipt_main")
    if receipt.get("source_sha256") != raw.get("source_sha256"): errors.append("receipt_source_inventory")
    if receipt.get("docker_invocations") != 0 or receipt.get("container_id") is not None: errors.append("receipt_container_boundary")
    if receipt.get("host", {}).get("system") != "Darwin": errors.append("receipt_not_macos")
    for filename in ("raw.json", "run_receipt.json"):
        if not (bundle / filename).is_file(): errors.append("missing_" + filename)
    return {"audit": "PASS_HOST_BOUNDARY_SCOPED" if not errors else "STOP_AUDIT", "errors": errors,
            "atomic_rows": len(raw.get("atomic_rows", [])), "unsafe_rows": len(raw.get("unsafe_rows", []))}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    source_dir = repo / "research/system1/needle_publication_host_boundary_5134_20260928_01"
    seed_raw = (repo / "research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json").read_bytes()
    result = audit_bundle(args.bundle.resolve(), seed_raw, source_dir)
    result["raw_sha256"] = sha((args.bundle.resolve() / "raw.json").read_bytes())
    result["receipt_sha256"] = sha((args.bundle.resolve() / "run_receipt.json").read_bytes())
    (args.bundle.resolve() / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["audit"] == "PASS_HOST_BOUNDARY_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
