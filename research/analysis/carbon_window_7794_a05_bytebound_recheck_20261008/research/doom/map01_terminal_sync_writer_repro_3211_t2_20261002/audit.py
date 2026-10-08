from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED_SOURCE_BLOB = "f5caf71a743a563b7de046b82d44db7ebe49e829"
SOURCE_REL = Path("research/doom/map01_recovery_cover_matched_v2_runner_3211_diagnostic_v2.py")
OUTPUT_REL = Path("research/doom/map01_terminal_sync_writer_repro_3211_t2_20261002/results/t2-01")


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def parse_object_stream(raw: bytes) -> list[dict]:
    text = raw.decode("utf-8")
    decoder = json.JSONDecoder()
    rows: list[dict] = []
    offset = 0
    while offset < len(text):
        if text.startswith("\\n", offset):
            offset += 2
            continue
        if text[offset] in "\r\n \t":
            offset += 1
            continue
        row, end = decoder.raw_decode(text, offset)
        if not isinstance(row, dict):
            raise ValueError(f"event object expected at {offset}")
        rows.append(row)
        offset = end
    return rows


def audit(repo_root: Path) -> dict:
    root = repo_root.resolve()
    actual_source_blob = git_blob_sha1((root / SOURCE_REL).read_bytes())
    if actual_source_blob != EXPECTED_SOURCE_BLOB:
        raise ValueError(f"frozen source mismatch: {actual_source_blob}")
    out = root / OUTPUT_REL
    candidate = json.loads((out / "candidate.json").read_text(encoding="utf-8"))
    raw = (out / "session-events.jsonl").read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    if candidate.get("source_git_blob") != EXPECTED_SOURCE_BLOB:
        raise ValueError("candidate source identity mismatch")
    if candidate.get("child_exit_code") != 0:
        raise ValueError("synthetic child did not exit successfully")
    if candidate.get("trace_sha256") != actual_sha or candidate.get("trace_byte_count") != len(raw):
        raise ValueError("raw sidecar hash/size mismatch")

    expected = [
        {"event": "probe", "index": 1, "text": "embedded\nvalue"},
        {"event": "terminal", "id": "synthetic-terminal"},
    ]
    memory_events = candidate.get("memory_events")
    if memory_events != expected:
        raise ValueError("in-memory child event order/content mismatch")
    rows = parse_object_stream(raw)
    if rows != expected:
        raise ValueError("reconstructed raw event objects mismatch")

    jsonl_error = None
    try:
        lines = raw.splitlines()
        if len(lines) != len(expected):
            raise ValueError(f"expected {len(expected)} physical JSONL lines, got {len(lines)}")
        parsed_lines = [json.loads(line) for line in lines]
        if parsed_lines != expected:
            raise ValueError("line-based JSONL contents mismatch")
    except (ValueError, json.JSONDecodeError) as exc:
        jsonl_error = str(exc)
    if jsonl_error is None:
        raise ValueError("sidecar unexpectedly satisfies ordinary JSONL parsing")

    return {
        "schema": "map01-terminal-sync-writer-reproduction-audit-v1",
        "source_git_blob": actual_source_blob,
        "child_exit_code": candidate["child_exit_code"],
        "memory_event_count": len(memory_events),
        "reconstructed_object_count": len(rows),
        "physical_line_count": len(raw.splitlines()),
        "raw_byte_count": len(raw),
        "raw_sha256": actual_sha,
        "ordinary_jsonl_error": jsonl_error,
        "decoded_events": rows,
        "decision": "CONFIRMED_JSONL_TRACE_FORMAT_DEFECT",
        "scope_limit": "Synthetic JsonSession writer boundary only; no MAP01 recovery-arm event or timeout cause inferred.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.repo_root), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
