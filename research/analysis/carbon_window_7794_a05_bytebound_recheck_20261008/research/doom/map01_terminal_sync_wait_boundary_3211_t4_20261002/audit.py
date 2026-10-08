from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SOURCE_BLOB = "f5caf71a743a563b7de046b82d44db7ebe49e829"
EXPECTED_MAIN = "bd77907946b7164e7513c3f5893f99348639e48a"
SOURCE_REL = Path("research/doom/map01_recovery_cover_matched_v2_runner_3211_diagnostic_v2.py")
CASE_NAMES = {"within_bound", "wrong_id", "absent", "late_exact"}


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def decode_object_stream(raw: bytes) -> list[dict]:
    text = raw.decode("utf-8")
    decoder = json.JSONDecoder()
    rows = []
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
            raise ValueError("trace row was not a JSON object")
        rows.append(row)
        offset = end
    return rows


def verify_freeze(bundle: Path) -> tuple[dict, str]:
    raw = (bundle / "FREEZE.json").read_bytes()
    freeze = json.loads(raw)
    if freeze.get("main_sha") != EXPECTED_MAIN:
        raise ValueError("freeze main mismatch")
    for name, expected in freeze.get("files", {}).items():
        actual = hashlib.sha256((bundle / name).read_bytes()).hexdigest().upper()
        if actual != expected:
            raise ValueError(f"freeze hash mismatch: {name}")
    return freeze, hashlib.sha256(raw).hexdigest()


def audit(repo_root: Path, out_dir: Path) -> dict:
    repo = repo_root.resolve()
    bundle = Path(__file__).resolve().parent
    freeze, freeze_sha = verify_freeze(bundle)
    if git_blob_sha1((repo / SOURCE_REL).read_bytes()) != SOURCE_BLOB:
        raise ValueError("runner source blob mismatch")
    candidate = json.loads((out_dir / "candidate.json").read_text(encoding="utf-8"))
    if candidate.get("main_sha") != EXPECTED_MAIN or candidate.get("runner_git_blob") != SOURCE_BLOB:
        raise ValueError("candidate identity mismatch")
    if candidate.get("freeze_sha256") != freeze_sha or candidate.get("retries") != 0:
        raise ValueError("candidate freeze/retry receipt mismatch")
    cases = candidate.get("cases")
    if not isinstance(cases, list) or {row.get("case") for row in cases} != CASE_NAMES:
        raise ValueError("case set mismatch")
    by_name = {row["case"]: row for row in cases}
    reconstructed = {}
    for name, row in by_name.items():
        raw = (out_dir / row["trace_file"]).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if row.get("trace_sha256") != digest or row.get("trace_byte_count") != len(raw):
            raise ValueError(f"{name}: sidecar integrity mismatch")
        parsed = decode_object_stream(raw)
        if parsed != row.get("events"):
            raise ValueError(f"{name}: raw trace differs from in-memory event list")
        if row.get("child_reaped") is not True or row.get("reader_joined") is not True:
            raise ValueError(f"{name}: child/reader cleanup not verified")
        if not any(event.get("event") == "ready" for event in parsed):
            raise ValueError(f"{name}: missing child-ready event")
        reconstructed[name] = parsed

    within = by_name["within_bound"]
    if within.get("disposition") != "MATCHED_TERMINAL":
        raise ValueError("within-bound terminal did not match")
    if within["wait_return"].get("id") != "fallback-within":
        raise ValueError("within-bound terminal ID mismatch")
    within_terminal = next(x for x in reconstructed["within_bound"] if x.get("event") == "terminal")
    if within_terminal["child_emit_monotonic_ns"] > within["wait_deadline_ns"]:
        raise ValueError("within-bound terminal was emitted after the deadline")

    wrong = by_name["wrong_id"]
    wrong_terms = [x for x in reconstructed["wrong_id"] if x.get("event") == "terminal"]
    if wrong.get("disposition") != "TIMEOUT" or wrong.get("wait_error") != {
        "type": "TimeoutError", "message": "session event timeout"
    }:
        raise ValueError("wrong-ID path did not produce the expected timeout")
    if len(wrong_terms) != 1 or wrong_terms[0].get("id") != "other-terminal":
        raise ValueError("wrong-ID terminal evidence missing")

    absent = by_name["absent"]
    if absent.get("disposition") != "TIMEOUT" or absent.get("wait_error") != wrong.get("wait_error"):
        raise ValueError("absent-terminal path did not produce the identical timeout")
    if any(x.get("event") == "terminal" for x in reconstructed["absent"]):
        raise ValueError("absent-terminal path unexpectedly retained a terminal")

    late = by_name["late_exact"]
    late_terms = [x for x in reconstructed["late_exact"] if x.get("event") == "terminal"]
    if late.get("disposition") != "TIMEOUT" or late.get("wait_error") != wrong.get("wait_error"):
        raise ValueError("late-terminal path did not produce the identical timeout")
    if len(late_terms) != 1 or late_terms[0].get("id") != late.get("expected_id"):
        raise ValueError("late exact terminal not retained after wait timeout")
    if late_terms[0].get("child_emit_monotonic_ns", 0) <= late.get("wait_deadline_ns", 0):
        raise ValueError("late exact terminal was not emitted after the wait deadline")
    if late.get("wait_end_ns", 0) >= late_terms[0].get("child_emit_monotonic_ns", 0):
        raise ValueError("late event was emitted before the timed-out wait returned")

    return {
        "schema": "map01-terminal-wait-boundary-audit-v1",
        "decision": "PASS_WAIT_BOUNDARY_DISCRIMINATION_SCOPED",
        "main_sha": EXPECTED_MAIN,
        "runner_git_blob": SOURCE_BLOB,
        "freeze_sha256": freeze_sha,
        "case_count": len(by_name),
        "cases": {
            "within_bound": "matching ID returned before deadline",
            "wrong_id": "wrong terminal retained; wait timed out with the same message",
            "absent": "no terminal retained; wait timed out with the same message",
            "late_exact": "matching terminal retained after wait timed out with the same message",
        },
        "cleanup_verified": all(
            row.get("child_reaped") is True and row.get("reader_joined") is True
            for row in cases
        ),
        "scope_limit": "Synthetic JsonSession.wait boundary only. Does not identify the original #3202/#3211 recovery-arm event or timeout cause.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.repo_root, args.out), sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
