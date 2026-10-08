"""Independent raw-only oracle for #6501; intentionally does not import candidate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


MODES = ("no_coalescing", "naive_predicate_key", "scope_typed")


def _scope(case: dict, request: dict) -> dict:
    scope = dict(case["scope"])
    for field, value in request.get("scope_override", {}).items():
        scope[field] = value
    return scope


def _independent_key(case: dict, request: dict, mode: str, fields: list[str]) -> tuple:
    scope = _scope(case, request)
    if mode == "no_coalescing":
        return (request["id"],)
    if mode == "naive_predicate_key":
        return (scope["predicate"],)
    return tuple((field, json.dumps(scope[field], sort_keys=True, separators=(",", ":"))) for field in fields)


def _decision(request: dict, scope: dict, verdict: str, end_ms: int) -> str:
    cancelled_at = request.get("cancel_at_ms")
    if cancelled_at is not None and cancelled_at < end_ms:
        return "CANCELLED_WAITER"
    if end_ms > request["deadline_ms"]:
        return "DEADLINE_MISSED"
    if verdict == "ERROR":
        return "OWNER_FAILED"
    if verdict == "UNKNOWN":
        return "UNKNOWN"
    observed_generation = request.get("generation_at_return", scope["target_generation"])
    if observed_generation != scope["target_generation"]:
        return "STALE_ON_RETURN"
    if end_ms < scope["valid_from_ms"] or end_ms > scope["valid_until_ms"]:
        return "STALE_ON_RETURN"
    if verdict != request["truth"]:
        return "WRONG_SHARED_TRUE" if verdict == "TRUE" else "WRONG_SHARED_FALSE"
    return "ADMISSIBLE_TRUE" if verdict == "TRUE" else "ADMISSIBLE_FALSE"


def _reference(case: dict, fixtures: dict, mode: str) -> dict:
    pending_calls = []
    in_flight = {}
    capacity_available_at = 0
    ordered = sorted(case["requests"], key=lambda item: (item["at_ms"], item["id"]))
    for request in ordered:
        identity = _independent_key(case, request, mode, fixtures["scope_fields"])
        group = in_flight.get(identity)
        if group is not None and request["at_ms"] >= group["end_ms"]:
            group = None
        if group is None:
            begin = max(request["at_ms"], capacity_available_at)
            group = {
                "identity": identity,
                "owner": request,
                "scope": _scope(case, request),
                "end_ms": begin + fixtures["service_ms"],
                "waiters": [],
            }
            pending_calls.append(group)
            in_flight[identity] = group
            capacity_available_at = group["end_ms"]
        group["waiters"].append(request)

    answers = {}
    waits = {}
    receipts = {}
    for group in pending_calls:
        receipts[group["owner"]["id"]] = group["end_ms"]
        for request in group["waiters"]:
            answers[request["id"]] = _decision(
                request, group["scope"], group["owner"]["truth"], group["end_ms"]
            )
            waits[request["id"]] = group["end_ms"] - request["at_ms"]
    return {
        "verifier_invocations": len(pending_calls),
        "completion_ms": receipts,
        "decision_latency_ms": waits,
        "per_caller": answers,
    }


def audit(raw: dict, fixtures: dict, fixture_sha256: str | None = None) -> dict:
    violations = []
    if raw.get("schema") != "scope-typed-singleflight-t0-candidate-v1":
        violations.append("candidate schema mismatch")
    if fixture_sha256 is not None and raw.get("fixture_sha256") != fixture_sha256:
        violations.append("frozen fixture digest mismatch")
    expected_ids = {row["id"] for row in fixtures["cases"]}
    if set(raw.get("cases", {})) != expected_ids:
        violations.append("case denominator differs from frozen fixture")
    for case in fixtures["cases"]:
        case_id = case["id"]
        actual_case = raw.get("cases", {}).get(case_id)
        if actual_case is None:
            continue
        if set(actual_case) != set(MODES):
            violations.append(f"{case_id}: mechanism set mismatch")
            continue
        for mode in MODES:
            expected = _reference(case, fixtures, mode)
            if actual_case[mode] != expected:
                violations.append(f"{case_id}/{mode}: raw output differs from independent replay")
        scoped = actual_case["scope_typed"]
        frozen_oracle = case["oracle"]
        if scoped["verifier_invocations"] != frozen_oracle["invocations"]:
            violations.append(f"{case_id}: scoped invocation count differs from independent fixture oracle")
        if scoped["per_caller"] != frozen_oracle["per_caller"]:
            violations.append(f"{case_id}: scoped decisions differ from hand-authored fixture oracle")
    return {
        "status": "PASS_METHOD_SCOPED" if not violations else "FAIL_RAW_AUDIT",
        "violations": violations,
        "cases_audited": len(expected_ids),
    }


def audit_files(raw_path: str | Path, fixture_path: str | Path) -> dict:
    raw_bytes = Path(raw_path).read_bytes()
    fixture_bytes = Path(fixture_path).read_bytes()
    return audit(
        json.loads(raw_bytes),
        json.loads(fixture_bytes),
        hashlib.sha256(fixture_bytes).hexdigest(),
    )


def main() -> int:
    result = audit_files("candidate-raw.json", "fixtures.json")
    Path("audit-raw.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
