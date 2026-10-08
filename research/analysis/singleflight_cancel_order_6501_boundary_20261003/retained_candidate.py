"""Deterministic candidate for the #6501 scope-typed singleflight T0."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _resolved_scope(case: dict, request: dict) -> dict:
    scope = dict(case["scope"])
    scope.update(request.get("scope_override", {}))
    return scope


def _key(case: dict, request: dict, mode: str, scope_fields: list[str]) -> str:
    scope = _resolved_scope(case, request)
    if mode == "none":
        fields = {"request_id": request["id"]}
    elif mode == "naive":
        fields = {"predicate": scope["predicate"]}
    else:
        fields = {name: scope[name] for name in scope_fields}
    return json.dumps(fields, sort_keys=True, separators=(",", ":"))


def _classify(request: dict, scope: dict, returned_truth: str, completed_at: int) -> str:
    if request.get("cancel_at_ms") is not None and request["cancel_at_ms"] < completed_at:
        return "CANCELLED_WAITER"
    if completed_at > request["deadline_ms"]:
        return "DEADLINE_MISSED"
    if returned_truth == "ERROR":
        return "OWNER_FAILED"
    if returned_truth == "UNKNOWN":
        return "UNKNOWN"
    if request.get("generation_at_return", scope["target_generation"]) != scope["target_generation"]:
        return "STALE_ON_RETURN"
    if not scope["valid_from_ms"] <= completed_at <= scope["valid_until_ms"]:
        return "STALE_ON_RETURN"
    if returned_truth != request["truth"]:
        return "WRONG_SHARED_TRUE" if returned_truth == "TRUE" else "WRONG_SHARED_FALSE"
    return "ADMISSIBLE_TRUE" if returned_truth == "TRUE" else "ADMISSIBLE_FALSE"


def _simulate(case: dict, service_ms: int, scope_fields: list[str], mode: str) -> dict:
    requests = sorted(case["requests"], key=lambda row: (row["at_ms"], row["id"]))
    units = []
    caller_unit = {}
    verifier_free_at = 0

    for request in requests:
        key = _key(case, request, mode, scope_fields)
        pending = next(
            (unit for unit in units if unit["key"] == key and request["at_ms"] < unit["completed_at"]),
            None,
        )
        if pending is None:
            started_at = max(request["at_ms"], verifier_free_at)
            pending = {
                "key": key,
                "started_at": started_at,
                "completed_at": started_at + service_ms,
                "owner": request,
                "scope": _resolved_scope(case, request),
                "waiters": [],
            }
            units.append(pending)
            verifier_free_at = pending["completed_at"]
        pending["waiters"].append(request)
        caller_unit[request["id"]] = pending

    outcomes = {}
    latencies = {}
    for request in requests:
        unit = caller_unit[request["id"]]
        outcomes[request["id"]] = _classify(
            request, unit["scope"], unit["owner"]["truth"], unit["completed_at"]
        )
        latencies[request["id"]] = unit["completed_at"] - request["at_ms"]
    return {
        "verifier_invocations": len(units),
        "completion_ms": {unit["owner"]["id"]: unit["completed_at"] for unit in units},
        "decision_latency_ms": latencies,
        "per_caller": outcomes,
    }


def run(fixtures_path: str | Path) -> dict:
    fixtures_path = Path(fixtures_path)
    fixture_bytes = fixtures_path.read_bytes()
    fixtures = json.loads(fixture_bytes)
    result = {
        "schema": "scope-typed-singleflight-t0-candidate-v1",
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "cases": {},
    }
    for case in fixtures["cases"]:
        result["cases"][case["id"]] = {
            "no_coalescing": _simulate(case, fixtures["service_ms"], fixtures["scope_fields"], "none"),
            "naive_predicate_key": _simulate(case, fixtures["service_ms"], fixtures["scope_fields"], "naive"),
            "scope_typed": _simulate(case, fixtures["service_ms"], fixtures["scope_fields"], "scope"),
        }
    return result


def main() -> int:
    result = run("fixtures.json")
    Path("candidate-raw.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"schema": result["schema"], "fixture_sha256": result["fixture_sha256"], "cases": len(result["cases"])}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
