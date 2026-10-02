import argparse
import hashlib
import json
from pathlib import Path
import sys


ALLOCATION = "MAP01-TERMINAL-WAIT-BOUNDARY-3211-T5-AUDIT-SUCCESSOR2-20261002-01"
T5_ALLOCATION = "MAP01-TERMINAL-WAIT-BOUNDARY-3211-T5-CONTAINER-20261002-01"
T5_MAIN = "c4d2d4b1ccf4512ec79af75bd8eaecfcada39947"
T4_BLOB = "afd5d4ea1bbbede29ecb67ff49f6e944b4d22320"
RUNNER_BLOB = "f5caf71a743a563b7de046b82d44db7ebe49e829"
CASE_NAMES = {"within_bound", "wrong_id", "absent", "late_exact"}
TIMEOUT = {"type": "TimeoutError", "message": "session event timeout"}


def parse_events(raw: bytes) -> list[dict]:
    if not raw:
        raise ValueError("empty event trace")
    parts = raw.split(b"\\n")
    if parts[-1] == b"":
        parts.pop()
    if not parts or any(not part for part in parts):
        raise ValueError("empty event record")
    events = []
    for part in parts:
        try:
            value = json.loads(part.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid literal-delimited JSON event") from exc
        if not isinstance(value, dict):
            raise ValueError("event record is not an object")
        events.append(value)
    return events


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_package(bundle: Path) -> tuple[dict, str, int]:
    manifest = (bundle / "SHA256SUMS").read_text(encoding="ascii").splitlines()
    seen = set()
    for line in manifest:
        digest, name = line.split(None, 1)
        name = name.strip()
        if name in seen or Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("invalid or duplicate package manifest path")
        seen.add(name)
        raw = (bundle / name).read_bytes()
        if sha256(raw).upper() != digest.upper():
            raise ValueError(f"package SHA-256 mismatch: {name}")
    if len(seen) != 13:
        raise ValueError("frozen package manifest entry count mismatch")
    freeze_raw = (bundle / "FREEZE.json").read_bytes()
    freeze = json.loads(freeze_raw)
    if freeze.get("allocation_id") != T5_ALLOCATION or freeze.get("main_sha") != T5_MAIN:
        raise ValueError("frozen T5 identity mismatch")
    if freeze.get("predecessor_t4_candidate_git_blob") != T4_BLOB or freeze.get("runner_git_blob") != RUNNER_BLOB:
        raise ValueError("frozen source blob identity mismatch")
    for name, expected in freeze["files"].items():
        if sha256((bundle / name).read_bytes()).upper() != expected.upper():
            raise ValueError(f"frozen source hash mismatch: {name}")
    if freeze.get("candidate_invocations") != 1 or freeze.get("independent_auditor_invocations") != 1 or freeze.get("retries") != 0:
        raise ValueError("historical T5 invocation counts mismatch")
    return freeze, sha256(freeze_raw), len(seen)


def audit(bundle: Path, candidate_dir: Path) -> dict:
    freeze, freeze_digest, manifest_count = verify_package(bundle)
    candidate_path = candidate_dir / "candidate.json"
    candidate_raw = candidate_path.read_bytes()
    candidate = json.loads(candidate_raw)
    identity = {
        "schema": "map01-terminal-wait-boundary-container-candidate-v1",
        "allocation_id": T5_ALLOCATION,
        "main_sha": T5_MAIN,
        "candidate_source_t4_git_blob": T4_BLOB,
        "runner_git_blob": RUNNER_BLOB,
        "freeze_sha256": freeze_digest,
        "candidate_invocations": 1,
        "synthetic_child_cases": 4,
        "retries": 0,
    }
    for key, expected in identity.items():
        if candidate.get(key) != expected:
            raise ValueError(f"candidate identity mismatch: {key}")
    cases = candidate.get("cases")
    if not isinstance(cases, list) or len(cases) != 4 or {x.get("case") for x in cases} != CASE_NAMES:
        raise ValueError("candidate case set mismatch")
    by_name = {case["case"]: case for case in cases}
    traces = {}
    for name, case in by_name.items():
        relative = Path(case["trace_file"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"unsafe trace path: {name}")
        raw = (candidate_dir / relative).read_bytes()
        if sha256(raw) != case.get("trace_sha256") or len(raw) != case.get("trace_byte_count"):
            raise ValueError(f"trace digest/byte-count mismatch: {name}")
        events = parse_events(raw)
        if events != case.get("events"):
            raise ValueError(f"raw event reconstruction mismatch: {name}")
        if case.get("child_reaped") is not True or case.get("reader_joined") is not True:
            raise ValueError(f"child/reader cleanup missing: {name}")
        start, deadline, end = (case.get(k) for k in ("wait_start_ns", "wait_deadline_ns", "wait_end_ns"))
        if any(type(value) is not int for value in (start, deadline, end)) or deadline <= start or end < start:
            raise ValueError(f"invalid wait timing fields: {name}")
        if not events or events[0].get("event") != "ready":
            raise ValueError(f"ready event absent: {name}")
        traces[name] = events

    within = by_name["within_bound"]
    wt = [e for e in traces["within_bound"] if e.get("event") == "terminal"]
    if (within.get("disposition") != "MATCHED_TERMINAL" or within.get("wait_error") is not None
            or len(wt) != 1 or wt[0].get("id") != within.get("expected_id")
            or within.get("expected_id") != "fallback-within"
            or wt[0].get("child_emit_monotonic_ns", deadline + 1) > within["wait_deadline_ns"]
            or within.get("wait_return") != wt[0]
            or within.get("wait_end_ns") >= within.get("wait_deadline_ns")):
        raise ValueError("within-bound terminal reconstruction mismatch")

    wrong = by_name["wrong_id"]
    wrong_terms = [e for e in traces["wrong_id"] if e.get("event") == "terminal"]
    if (wrong.get("disposition") != "TIMEOUT" or wrong.get("wait_error") != TIMEOUT
            or wrong.get("wait_return") is not None or wrong.get("expected_id") != "fallback-expected"
            or len(wrong_terms) != 1 or wrong_terms[0].get("id") == wrong.get("expected_id")
            or wrong_terms[0].get("id") != "other-terminal"
            or wrong_terms[0].get("child_emit_monotonic_ns", 0) > wrong["wait_deadline_ns"]
            or wrong.get("wait_end_ns") < wrong.get("wait_deadline_ns")):
        raise ValueError("wrong-ID timeout reconstruction mismatch")

    absent = by_name["absent"]
    if (absent.get("disposition") != "TIMEOUT" or absent.get("wait_error") != TIMEOUT
            or absent.get("wait_return") is not None
            or any(e.get("event") == "terminal" for e in traces["absent"])):
        raise ValueError("absent-terminal reconstruction mismatch")

    late = by_name["late_exact"]
    lt = [e for e in traces["late_exact"] if e.get("event") == "terminal"]
    if (late.get("disposition") != "TIMEOUT" or late.get("wait_error") != TIMEOUT
            or late.get("wait_return") is not None or len(lt) != 1
            or lt[0].get("id") != late.get("expected_id")
            or late.get("expected_id") != "fallback-late"
            or lt[0].get("child_emit_monotonic_ns", 0) <= late.get("wait_deadline_ns", 0)
            or late.get("wait_end_ns", 0) >= lt[0].get("child_emit_monotonic_ns", 0)):
        raise ValueError("late-exact timeout reconstruction mismatch")

    return {
        "schema": "map01-terminal-wait-boundary-audit-successor2-v1",
        "allocation_id": ALLOCATION,
        "decision": "PASS_AUDIT_SUCCESSOR2_SCOPED",
        "input_commit": "49f2940ce79bd48bab376d8825f07bd8535a7361",
        "historical_t5_allocation": T5_ALLOCATION,
        "freeze_sha256": freeze_digest,
        "package_manifest_entries_verified": manifest_count,
        "candidate_invocations": 0,
        "historical_auditor_invocations_in_successor": 0,
        "new_auditor_invocations": 1,
        "retries": 0,
        "case_count": 4,
        "cleanup_verified": True,
        "candidate_receipt_sha256": sha256(candidate_raw),
        "scope_limit": "Independent audit of retained synthetic JsonSession.wait traces only; original T5 remains HOLD and no MAP01 or product behavior is established.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.bundle.resolve(), args.candidate_dir.resolve())
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
