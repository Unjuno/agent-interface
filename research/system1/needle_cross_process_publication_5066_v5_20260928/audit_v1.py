"""Independent raw-only auditor for Issue #5082; imports no runner code."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path


def canonical_package(seed: dict, generation: int) -> bytes:
    candidate = json.loads(json.dumps(seed))
    candidate["generation"] = generation
    candidate["provenance"]["seed"] = generation
    return (json.dumps(candidate, sort_keys=True, separators=(",", ":")) + "\n").encode()


def jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            try:
                value = json.loads(line)
            except Exception as exc:
                raise ValueError(f"invalid JSONL {path.name}:{line_no}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"non-object JSONL row {path.name}:{line_no}")
            rows.append(value)
    return rows


def audit(seed_path: Path, raw: Path) -> dict:
    errors: list[str] = []
    seed_bytes = seed_path.read_bytes()
    seed_hash = hashlib.sha256(seed_bytes).hexdigest()
    seed = json.loads(seed_bytes)
    atomic = raw / "atomic"
    publisher = jsonl(atomic / "publisher.jsonl")
    replace_rows = [r for r in publisher if r.get("kind") == "replace"]
    if any(r.get("kind") == "publisher_error" for r in publisher):
        errors.append("publisher_error")
    if len(replace_rows) != 4096 or {r.get("replace_index") for r in replace_rows} != set(range(4096)):
        errors.append("replacement_denominator")
    expected = {i: canonical_package(seed, 3789 + i) for i in range(4096)}
    expected_hash = {i: hashlib.sha256(b).hexdigest() for i, b in expected.items()}
    replace_intervals = []
    for r in replace_rows:
        i, begin, end = r.get("replace_index"), r.get("start_ns"), r.get("end_ns")
        if type(i) is not int or type(begin) is not int or type(end) is not int or begin >= end:
            errors.append("invalid_replace_row")
            continue
        if r.get("generation") != 3789 + i or r.get("sha256") != expected_hash.get(i):
            errors.append("replacement_payload_mismatch")
        replace_intervals.append((begin, end))
    reads: list[dict] = []
    exits = []
    for index in range(4):
        rows = jsonl(atomic / f"reader-{index}.jsonl")
        reader_rows = [r for r in rows if r.get("kind") == "read"]
        reads.extend(reader_rows)
        reader_exits = [r for r in rows if r.get("kind") == "reader_exit"]
        exits.extend(reader_exits)
        if (len(reader_exits) != 1 or
                (reader_exits and reader_exits[0].get("read_count") != len(reader_rows)) or
                {r.get("read_index") for r in reader_rows} != set(range(len(reader_rows)))):
            errors.append(f"reader_{index}_attempt_coverage")
        if any(r.get("kind") == "reader_error" for r in rows):
            errors.append(f"reader_{index}_error")
    pids: dict[int, int] = {}
    overlap_keys = set()
    read_keys = set()
    for r in reads:
        index, pid, read_id = r.get("reader_index"), r.get("reader_pid"), r.get("read_index")
        begin, end = r.get("open_start_ns"), r.get("open_end_ns")
        if (type(index) is not int or type(pid) is not int or type(read_id) is not int or
                type(begin) is not int or type(end) is not int or begin >= end):
            errors.append("invalid_read_row")
            continue
        if index in pids and pids[index] != pid:
            errors.append("reader_pid_changed")
        pids[index] = pid
        key = (pid, read_id)
        if key in read_keys:
            errors.append("duplicate_read")
        read_keys.add(key)
        generation = r.get("generation")
        try:
            observed_bytes = base64.b64decode(r["data_b64"], validate=True)
        except Exception:
            observed_bytes = None
        if type(generation) is not int or generation < 3788 or generation > 3788 + 4096:
            errors.append("unexpected_generation")
        elif generation == 3788 and (observed_bytes != seed_bytes or
                                     r.get("sha256") != seed_hash or
                                     r.get("bytes") != len(seed_bytes)):
            errors.append("baseline_seed_mismatch")
        elif generation != 3788:
            expected_bytes = canonical_package(seed, generation)
            if (not r.get("valid") or observed_bytes != expected_bytes or
                    r.get("sha256") != hashlib.sha256(expected_bytes).hexdigest() or
                    r.get("bytes") != len(expected_bytes)):
                errors.append("read_not_expected_whole_package")
        if any(max(begin, a) < min(end, b) for a, b in replace_intervals):
            overlap_keys.add(key)
    if len(pids) != 4 or len(set(pids.values())) != 4:
        errors.append("reader_process_identity")
    if len(exits) != 4 or {r.get("reader_index") for r in exits} != set(range(4)):
        errors.append("reader_exit_denominator")
    exit_file = json.loads((atomic / "process_exits.json").read_text(encoding="utf-8"))
    if (len(exit_file) != 4 or any(r.get("exitcode") != 0 for r in exit_file) or
            {r.get("pid") for r in exit_file} != set(pids.values())):
        errors.append("process_exit_mismatch")
    if len(overlap_keys) < 32 or len({pid for pid, _ in overlap_keys}) < 2:
        errors.append("overlap_gate")

    diagnostic = raw / "diagnostic"
    final_candidate = canonical_package(seed, 3789)
    observed = json.loads((diagnostic / "observations.json").read_text(encoding="utf-8"))
    if (len(observed) != 4 or len({r.get("pid") for r in observed}) != 4 or
            not all(r.get("ok") for r in observed)):
        errors.append("diagnostic_reader_gate")
    for index in range(4):
        rows = jsonl(diagnostic / f"reader-{index}.jsonl")
        matching = [r for r in rows if r.get("kind") == "diagnostic_read"]
        if len(matching) != 1:
            errors.append("diagnostic_raw_row_count")
            continue
        row = matching[0]
        try:
            partial = base64.b64decode(row["partial_b64"], validate=True)
        except Exception:
            partial = b""
        try:
            obj = json.loads(partial)
            reconstruct = canonical_package(obj, obj["generation"])
            valid = partial == reconstruct
        except Exception:
            valid = False
        expected_partial = final_candidate[:len(final_candidate) // 2]
        if (valid or partial != expected_partial or row.get("valid") is not False or
                row.get("sha256") != hashlib.sha256(partial).hexdigest() or
                row.get("bytes") != len(partial)):
            errors.append("diagnostic_partial_not_proven")
    if (diagnostic / "active.json").read_bytes() != final_candidate:
        errors.append("diagnostic_final_candidate_mismatch")
    return {"status": "PASS_ATOMIC_REPLACEMENT_OVERLAP_SCOPED" if not errors else "HOLD_EVIDENCE_INCOMPLETE",
            "errors": errors, "read_count": len(reads), "replacement_count": len(replace_rows),
            "overlap_count": len(overlap_keys), "reader_pids": sorted(set(pids.values()))}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not args.out.is_dir() or any(args.out.iterdir()):
        raise RuntimeError("audit output must be a pre-created empty directory")
    result = audit(args.seed, args.raw)
    (args.out / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                                         encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
