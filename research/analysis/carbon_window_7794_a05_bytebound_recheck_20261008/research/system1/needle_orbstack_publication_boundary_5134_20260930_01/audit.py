"""Independent raw-only audit; intentionally imports no pilot runner modules."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path

EXP = Path("/src/research/system1/needle_orbstack_publication_boundary_5134_20260930_01")
SEED = Path("/src/research/needle_role_skill_reload_3780_v1/formal/seed-3788/builder/skill.json")
IN = Path("/in")
OUT = Path("/out")
ALLOCATION = "needle-publication-orbstack-boundary-20260930-01"
IMAGE = "sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canon(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def package_digest(obj: dict) -> str:
    return sha(canon({k: v for k, v in obj.items() if k != "payload_sha256"}))


def decode(field: object, label: str, errors: list[str]) -> bytes:
    try:
        if not isinstance(field, str):
            raise ValueError("not string")
        return base64.b64decode(field, validate=True)
    except (ValueError, TypeError):
        errors.append(label + "_base64")
        return b""


def main() -> None:
    errors: list[str] = []
    if os.environ.get("OBSTAC_CONSTRUCTION") != "1":
        errors.append("construction_flag")
    try:
        raw_bytes = (IN / "raw.json").read_bytes()
        receipt_bytes = (IN / "invocation_receipt.json").read_bytes()
        manifest = json.loads((IN / "input_manifest.json").read_text())
        raw = json.loads(raw_bytes); receipt = json.loads(receipt_bytes)
    except (OSError, ValueError, TypeError) as exc:
        raise SystemExit("STOP_BOUNDARY_PILOT input read/parse: " + repr(exc))
    for name, content in (("raw.json", raw_bytes), ("invocation_receipt.json", receipt_bytes)):
        if manifest.get("files", {}).get(name) != sha(content):
            errors.append("input_manifest_" + name)
    if raw.get("allocation") != ALLOCATION or raw.get("issue") != 5134:
        errors.append("allocation_issue")
    if raw.get("formal_allocation_consumed") is not False or raw.get("formal_denominators_met") is not False:
        errors.append("formal_boundary")
    if raw.get("construction") != "1" or receipt.get("construction") != "1":
        errors.append("construction_receipt")
    for key in ("source_commit", "image_id"):
        if raw.get(key) != receipt.get(key):
            errors.append("raw_receipt_" + key)
    if raw.get("image_id") != IMAGE or receipt.get("image_id") != IMAGE:
        errors.append("pinned_image")
    if raw.get("platform") != "linux/arm64" or receipt.get("platform") != "linux/arm64":
        errors.append("platform")
    formal_container = receipt.get("formal_container", {})
    formal_mounts = {m.get("Destination"): m for m in formal_container.get("mounts", [])}
    if set(formal_mounts) != {"/src", "/out"}:
        errors.append("formal_mount_set")
    if formal_mounts.get("/src", {}).get("RW") is not False or formal_mounts.get("/out", {}).get("RW") is not True:
        errors.append("formal_mount_modes")
    if formal_container.get("mount_errors") or formal_container.get("returncode") != 0:
        errors.append("formal_container_execution")
    host_config = formal_container.get("host_config", {})
    if host_config.get("NetworkMode") != "none" or host_config.get("ReadonlyRootfs") is not True:
        errors.append("formal_container_isolation")
    security = host_config.get("SecurityOpt", [])
    if host_config.get("CapDrop") != ["ALL"] or not any(
            str(v) == "no-new-privileges" or str(v).startswith("no-new-privileges:") for v in security):
        errors.append("formal_container_security")
    if not receipt.get("source_sha256") or not isinstance(receipt.get("source_sha256"), dict):
        errors.append("source_hash_map")
    else:
        for filename, expected in receipt["source_sha256"].items():
            try:
                if sha((EXP / filename).read_bytes()) != expected:
                    errors.append("source_hash_" + filename)
            except OSError:
                errors.append("source_missing_" + filename)
    seed = SEED.read_bytes()
    if sha(seed) != "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a":
        errors.append("seed_hash")
    seed_obj = json.loads(seed)
    old_obj = json.loads(canon(seed_obj))
    new_obj = json.loads(canon(seed_obj))
    new_obj["generation"] = old_obj["generation"] + 1
    new_obj["provenance"] = dict(new_obj["provenance"])
    new_obj["provenance"]["allocation"] = ALLOCATION
    new_obj["provenance"]["predecessor_issue"] = 5134
    new_obj["payload_sha256"] = package_digest(new_obj)
    expected_old, expected_new = canon(old_obj), canon(new_obj)
    old = decode(raw.get("old_b64"), "old", errors)
    new = decode(raw.get("new_b64"), "new", errors)
    if old != expected_old or new != expected_new:
        errors.append("seed_candidate_reconstruction")
    if raw.get("old_sha256") != sha(expected_old) or raw.get("new_sha256") != sha(expected_new):
        errors.append("candidate_hashes")
    for name, content in (("old", expected_old), ("new", expected_new)):
        package = json.loads(content)
        if package.get("payload_sha256") != package_digest(package):
            errors.append(name + "_package_digest")

    atomic = raw.get("atomic", {})
    apids = atomic.get("reader_pids")
    arows = atomic.get("rows")
    if not isinstance(apids, list) or len(apids) != 4 or len(set(apids)) != 4:
        errors.append("atomic_pid_denominator")
    if raw.get("publisher_pid") in (apids if isinstance(apids, list) else []):
        errors.append("atomic_publisher_pid")
    if not isinstance(arows, list) or len(arows) != 4:
        errors.append("atomic_row_denominator")
        arows = []
    if atomic.get("exit_codes") != [0] * 4:
        errors.append("atomic_exit_codes")
    start, returned = atomic.get("replace_start_ns"), atomic.get("replace_return_ns")
    if not isinstance(start, int) or not isinstance(returned, int) or not start < returned:
        errors.append("atomic_replace_interval")
    seen = set()
    for row in arows:
        index = row.get("reader")
        if index in seen or index not in range(4):
            errors.append("atomic_reader_index")
        seen.add(index)
        if not isinstance(apids, list) or row.get("pid") != (apids[index] if index in range(4) else None):
            errors.append("atomic_pid_binding")
        opened, fs, fe = row.get("fd_open_ns"), row.get("fd_read_start_ns"), row.get("fd_read_end_ns")
        if not all(isinstance(v, int) for v in (opened, fs, fe, start, returned)) or not opened < start < returned <= fs <= fe:
            errors.append("atomic_fd_order")
        try:
            held = base64.b64decode(row["held_b64"], validate=True)
            path = base64.b64decode(row["path_b64"], validate=True)
        except (ValueError, KeyError, TypeError):
            errors.append("atomic_bytes_base64"); continue
        if held != expected_old or sha(held) != row.get("held_sha256"):
            errors.append("atomic_held_old_bytes")
        if path != expected_new or sha(path) != row.get("path_sha256"):
            errors.append("atomic_path_new_bytes")
        if not (returned <= row.get("path_read_start_ns", 0) <= row.get("path_read_end_ns", 0)):
            errors.append("atomic_path_order")
    if seen != set(range(4)):
        errors.append("atomic_reader_coverage")

    unsafe = raw.get("unsafe", {})
    upids, partial_rows, complete_rows = (unsafe.get("reader_pids"), unsafe.get("partial_rows"),
                                          unsafe.get("complete_rows"))
    if not isinstance(upids, list) or len(upids) != 4 or len(set(upids)) != 4:
        errors.append("unsafe_pid_denominator")
    if raw.get("publisher_pid") in (upids if isinstance(upids, list) else []):
        errors.append("unsafe_publisher_pid")
    if not isinstance(partial_rows, list) or len(partial_rows) != 4:
        errors.append("unsafe_partial_denominator"); partial_rows = []
    if not isinstance(complete_rows, list) or len(complete_rows) != 4:
        errors.append("unsafe_complete_denominator"); complete_rows = []
    if unsafe.get("exit_codes") != [0] * 4:
        errors.append("unsafe_exit_codes")
    prefix = expected_new[:len(expected_new)//2]
    if decode(unsafe.get("expected_prefix_b64"), "expected_prefix", errors) != prefix:
        errors.append("unsafe_expected_prefix")
    if decode(unsafe.get("expected_complete_b64"), "expected_complete", errors) != expected_new:
        errors.append("unsafe_expected_complete")
    partial_by_id = {r.get("reader"): r for r in partial_rows if isinstance(r, dict)}
    complete_by_id = {r.get("reader"): r for r in complete_rows if isinstance(r, dict)}
    if set(partial_by_id) != set(range(4)) or set(complete_by_id) != set(range(4)):
        errors.append("unsafe_reader_coverage")
    for i in range(4):
        p, c = partial_by_id.get(i, {}), complete_by_id.get(i, {})
        if not isinstance(upids, list) or p.get("pid") != (upids[i] if i < len(upids) else None) or c.get("pid") != (upids[i] if i < len(upids) else None):
            errors.append("unsafe_pid_binding")
        try:
            observed_partial = base64.b64decode(p["bytes_b64"], validate=True)
            observed_complete = base64.b64decode(c["bytes_b64"], validate=True)
        except (ValueError, KeyError, TypeError):
            errors.append("unsafe_bytes_base64"); continue
        if observed_partial != prefix or sha(observed_partial) != p.get("sha256"):
            errors.append("unsafe_partial_prefix")
        if observed_complete != expected_new or sha(observed_complete) != c.get("sha256"):
            errors.append("unsafe_complete_bytes")
        ws, wc, we = unsafe.get("write_start_ns"), unsafe.get("write_complete_start_ns"), unsafe.get("write_end_ns")
        if not all(isinstance(v, int) for v in (ws, wc, we)) or not ws <= p.get("read_start_ns", 0) <= p.get("read_end_ns", 0) <= wc < we:
            errors.append("unsafe_partial_order")
        if not (we <= c.get("read_start_ns", 0) <= c.get("read_end_ns", 0)):
            errors.append("unsafe_complete_order")
    result = {"allocation": ALLOCATION,
              "status": "PASS_BOUNDARY_PILOT_SCOPED" if not errors else "STOP_BOUNDARY_PILOT",
              "independent_audit": True, "errors": sorted(set(errors)),
              "atomic_rows_reconstructed": len(arows),
              "unsafe_partial_rows_reconstructed": len(partial_rows),
              "unsafe_complete_rows_reconstructed": len(complete_rows),
              "raw_sha256": sha(raw_bytes), "receipt_sha256": sha(receipt_bytes),
              "source_commit": receipt.get("source_commit"), "image_id": receipt.get("image_id"),
              "scope": "one OrbStack host, pinned linux/arm64 image, one transition, four readers per arm; not formal allocation -03"}
    (OUT / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
