from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ALLOCATION = "MAP01-TERMINAL-WAIT-BOUNDARY-3211-T5-CONTAINER-20261002-01"
MAIN_SHA = "c4d2d4b1ccf4512ec79af75bd8eaecfcada39947"
T4_BLOB = "afd5d4ea1bbbede29ecb67ff49f6e944b4d22320"
RUNNER_BLOB = "f5caf71a743a563b7de046b82d44db7ebe49e829"
NAMES = {"within_bound", "wrong_id", "absent", "late_exact"}


def verify_freeze(bundle: Path) -> tuple[dict, str]:
    raw = (bundle / "FREEZE.json").read_bytes()
    freeze = json.loads(raw)
    if freeze.get("main_sha") != MAIN_SHA or freeze.get("allocation_id") != ALLOCATION:
        raise ValueError("allocation/main freeze mismatch")
    for name, expected in freeze["files"].items():
        if hashlib.sha256((bundle / name).read_bytes()).hexdigest().upper() != expected:
            raise ValueError(f"frozen source mismatch: {name}")
    return freeze, hashlib.sha256(raw).hexdigest()


def parse_trace(raw: bytes) -> list[dict]:
    text = raw.decode("utf-8")
    decoder = json.JSONDecoder()
    rows, offset = [], 0
    while offset < len(text):
        if text.startswith("\\n", offset):
            offset += 2
            continue
        if text[offset] in "\r\n \t":
            offset += 1
            continue
        row, offset = decoder.raw_decode(text, offset)
        if not isinstance(row, dict):
            raise ValueError("trace row is not an object")
        rows.append(row)
    return rows


def audit(bundle: Path, candidate_dir: Path) -> dict:
    freeze, freeze_sha = verify_freeze(bundle)
    candidate = json.loads((candidate_dir / "candidate.json").read_text(encoding="utf-8"))
    expected_identity = {
        "schema": "map01-terminal-wait-boundary-container-candidate-v1",
        "allocation_id": ALLOCATION,
        "main_sha": MAIN_SHA,
        "candidate_source_t4_git_blob": T4_BLOB,
        "runner_git_blob": RUNNER_BLOB,
        "freeze_sha256": freeze_sha,
        "candidate_invocations": 1,
        "synthetic_child_cases": 4,
        "retries": 0,
    }
    for key, value in expected_identity.items():
        if candidate.get(key) != value:
            raise ValueError(f"candidate identity mismatch: {key}")
    cases = candidate.get("cases")
    if not isinstance(cases, list) or len(cases) != 4 or {x.get("case") for x in cases} != NAMES:
        raise ValueError("case set mismatch")
    by_name = {x["case"]: x for x in cases}
    traces = {}
    for name, case in by_name.items():
        raw = (candidate_dir / case["trace_file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != case.get("trace_sha256"):
            raise ValueError(f"{name}: trace SHA mismatch")
        if len(raw) != case.get("trace_byte_count"):
            raise ValueError(f"{name}: trace byte count mismatch")
        rows = parse_trace(raw)
        if rows != case.get("events"):
            raise ValueError(f"{name}: raw trace differs from candidate event list")
        if case.get("child_reaped") is not True or case.get("reader_joined") is not True:
            raise ValueError(f"{name}: child/reader cleanup absent")
        if type(case.get("wait_start_ns")) is not int or type(case.get("wait_deadline_ns")) is not int or type(case.get("wait_end_ns")) is not int:
            raise ValueError(f"{name}: wait boundaries absent")
        if case["wait_deadline_ns"] <= case["wait_start_ns"] or case["wait_end_ns"] < case["wait_start_ns"]:
            raise ValueError(f"{name}: invalid wait boundaries")
        if not any(e.get("event") == "ready" for e in rows):
            raise ValueError(f"{name}: ready event absent")
        traces[name] = rows

    within = by_name["within_bound"]
    term = [e for e in traces["within_bound"] if e.get("event") == "terminal"]
    if within.get("disposition") != "MATCHED_TERMINAL" or not isinstance(within.get("wait_return"), dict) or within["wait_return"].get("id") != "fallback-within":
        raise ValueError("within-bound terminal did not match")
    if len(term) != 1 or term[0].get("id") != "fallback-within" or term[0].get("child_emit_monotonic_ns", 0) > within["wait_deadline_ns"]:
        raise ValueError("within-bound terminal timing mismatch")

    wrong = by_name["wrong_id"]
    timeout = {"type": "TimeoutError", "message": "session event timeout"}
    wrong_terms = [e for e in traces["wrong_id"] if e.get("event") == "terminal"]
    if wrong.get("disposition") != "TIMEOUT" or wrong.get("wait_error") != timeout or len(wrong_terms) != 1 or wrong_terms[0].get("id") != "other-terminal":
        raise ValueError("wrong-ID case mismatch")

    absent = by_name["absent"]
    if absent.get("disposition") != "TIMEOUT" or absent.get("wait_error") != timeout or any(e.get("event") == "terminal" for e in traces["absent"]):
        raise ValueError("absent-terminal case mismatch")

    late = by_name["late_exact"]
    late_terms = [e for e in traces["late_exact"] if e.get("event") == "terminal"]
    if late.get("disposition") != "TIMEOUT" or late.get("wait_error") != timeout or len(late_terms) != 1 or late_terms[0].get("id") != late.get("expected_id"):
        raise ValueError("late-exact timeout/terminal mismatch")
    emitted = late_terms[0].get("child_emit_monotonic_ns", 0)
    if emitted <= late["wait_deadline_ns"] or late["wait_end_ns"] >= emitted:
        raise ValueError("late terminal is not after deadline and returned timeout")

    return {
        "schema": "map01-terminal-wait-boundary-container-audit-v1",
        "allocation_id": ALLOCATION,
        "decision": "PASS_CONTAINER_TRANSFER_SCOPED",
        "main_sha": MAIN_SHA,
        "candidate_source_t4_git_blob": T4_BLOB,
        "runner_git_blob": RUNNER_BLOB,
        "freeze_sha256": freeze_sha,
        "candidate_invocations": 1,
        "auditor_invocations": 1,
        "retries": 0,
        "case_count": 4,
        "cleanup_verified": True,
        "scope_limit": "Synthetic JsonSession.wait boundary in pinned CPU container only; does not identify the original recovery-arm terminal cause or establish MAP01 behavior.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--candidate-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = audit(args.bundle.resolve(), args.candidate_dir.resolve())
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "audit.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
