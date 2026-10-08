"""Raw-only audit for the retained v13 controlled timestamp-boundary rows."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
PREFLIGHT = RESULTS / "zero-model-preflight-v13-20260927-01-retry04"
BOUNDARY = RESULTS / "real-observation-boundary-v13-20260927-02"
EXPECTED = {
    "summary.json": "05445612872a796002fe91e68cf447454a74b78a0dfc3a706345da138ca4478e",
    "inverted.jsonl": "d0cdd76ea8183abe8057fa8a4cdd0b18e7e86dd49166466427ff9a9649f0bc4c",
    "equal.jsonl": "f8558e148b8acd06ce882f75fe257b0b8bbf8ac6873a6a81d28ac79dd62e67be",
    "ordered.jsonl": "22f6dd74d8f6f519ed919634dc46659432c9b652eec95d37e010ee72a900c5c2",
    "events.jsonl": "a040a342471df48580c1207ac88c25d711c2753ecdb9ef71417ec4cb6627d1e7",
    "owner-events.json": "e7b623459820d1c6eb71073d08e725959d8949898484c3f6646ee20d695aadce",
    "environment.json": "72072edf1a1ee3e72b21511019a5992918e86cc8882d189ffce07afdbab7a0b9",
}
EXPECTED_ERROR = "controller decision precedes current snapshot"


def validate_case(result: dict, row: dict, source_event: dict,
                  delta: int, error: str | None) -> list[str]:
    """Reconstruct one case without importing the candidate or replay gate."""
    failures = []
    sequence = result.get("observation_sequence")
    gates = {
        "schema": row.get("schema") == "running-action-clock-check-v1",
        "capture": row.get("capture_ns") == result.get("capture_ns") == source_event.get("capture_ns"),
        "decision": row.get("controller_decided_ns") == result.get("controller_decided_ns"),
        "delta": result.get("controller_decided_ns") - result.get("capture_ns") == delta
                 and result.get("delta_ns") == delta
                 and row.get("comparison_delta_ns") == delta,
        "sequence": row.get("sequence") == sequence == source_event.get("sequence")
                    and row.get("observation_event", {}).get("sequence") == sequence,
        "event-times": row.get("observation_event", {}).get("capture_ns") == source_event.get("capture_ns")
                       and row.get("observation_event", {}).get("typed_ready_ns") == source_event.get("typed_ready_ns")
                       and row.get("observation_event", {}).get("emit_ns") == source_event.get("emit_ns"),
        "outcome": result.get("error") == error,
        "guard": result.get("guard_state") == "INPUT_ACTIVE"
                 and result.get("logical_authority_still_active") is True,
        "logged": result.get("logged_before_result") is True,
        "null-injected-calibration": row.get("calibration") is None
                                     and row.get("calibration_sha256") is None
                                     and row.get("offset_lower_ns") is None
                                     and row.get("host_clock") is None
                                     and row.get("runtime_clock") is None,
    }
    failures.extend(gate for gate, passed in gates.items() if not passed)
    return failures


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> list[str]:
    errors: list[str] = []
    paths = {
        "summary.json": BOUNDARY / "summary.json",
        "inverted.jsonl": BOUNDARY / "inverted.jsonl",
        "equal.jsonl": BOUNDARY / "equal.jsonl",
        "ordered.jsonl": BOUNDARY / "ordered.jsonl",
        "events.jsonl": PREFLIGHT / "runtime/events.jsonl",
        "owner-events.json": PREFLIGHT / "runtime/owner-events.json",
        "environment.json": PREFLIGHT / "runtime/environment.json",
    }
    for name, path in paths.items():
        if not path.is_file():
            errors.append(f"missing:{name}")
        elif sha256(path) != EXPECTED[name]:
            errors.append(f"sha256:{name}")

    summary = load_json(paths["summary.json"])
    event_rows = [json.loads(line) for line in paths["events.jsonl"].read_text(
        encoding="utf-8").splitlines()]
    events = {row.get("sequence"): row for row in event_rows
              if row.get("event") == "typed_observation"}
    if summary.get("schema") != "map01-real-observation-clock-boundary-v1":
        errors.append("summary-schema")
    if summary.get("scope") != "controlled timestamp injection; no model; no physical input":
        errors.append("summary-scope")
    if summary.get("source_sequence") != 1:
        errors.append("source-sequence")
    cases = summary.get("cases", {})
    if set(cases) != {"inverted", "equal", "ordered"}:
        errors.append("case-set")

    expected = {"inverted": (-1, EXPECTED_ERROR), "equal": (0, None),
                "ordered": (1, None)}
    for name, (delta, error) in expected.items():
        result = cases.get(name, {})
        row_path = BOUNDARY / f"{name}.jsonl"
        raw_lines = row_path.read_text(encoding="utf-8").splitlines()
        if len(raw_lines) != 1:
            errors.append(f"row-count:{name}")
            continue
        row = json.loads(raw_lines[0])
        sequence = result.get("observation_sequence")
        source_event = events.get(sequence)
        if source_event is None:
            errors.append(f"source-event:{name}")
            continue
        errors.extend(f"{name}:{gate}" for gate in validate_case(
            result, row, source_event, delta, error))

    owner_events = load_json(paths["owner-events.json"])
    releases = [row for row in owner_events if row.get("event") == "owner_release"]
    if len(releases) != 3 or any(
            row.get("verified") is not True or row.get("buttons_down") != []
            or row.get("keys_down") != [] for row in releases):
        errors.append("owner-release")
    if summary.get("pass") is not True:
        errors.append("summary-decision")
    return errors


if __name__ == "__main__":
    findings = audit()
    print(json.dumps({"decision": "PASS_RAW_AUDIT" if not findings else "STOP_RAW_AUDIT",
                      "errors": findings}, indent=2))
    raise SystemExit(bool(findings))
