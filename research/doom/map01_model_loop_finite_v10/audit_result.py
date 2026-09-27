"""Read-only audit of the one-time v10 formal MAP01 allocation."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RUN = HERE / "results/map01-model-loop-finite-v10-20260927-02"
EXPECTED_WAD = "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b"
EXPECTED_EFFECTIVE = "81eeadd9626c064ad18de15d80a08c0a3c986f93d6e6c83c777be71b315d1e39"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    events = jsonl(RUN / "runtime/events.jsonl")
    protocol = jsonl(RUN / "planner-protocol.jsonl")
    owners = json.loads((RUN / "runtime/owner-events.json").read_text())
    environment = json.loads((RUN / "runtime/environment.json").read_text())
    sources = json.loads((RUN / "runtime/sources.json").read_text())
    translations = jsonl(RUN / "runtime/lease-deadline-translations.jsonl")
    effective = HERE / "frozen-source/effective-controller-990637.py"
    effective_text = effective.read_text()
    refresh_literal = '"valid_until_ns":clock_ns+15_000_000_000'
    original_literal = '"valid_until_ns":clock_ns+5_000_000_000'

    completed_turns = [
        row["message"]["params"]["turn"]
        for row in protocol
        if row.get("message", {}).get("method") == "turn/completed"
    ]
    accepted = {row.get("id"): row for row in events if row.get("event") == "accepted"}
    terminal = {row.get("id"): row for row in events if row.get("event") == "terminal"}
    refresh_ids = sorted(
        identifier for identifier in accepted
        if isinstance(identifier, str) and "-refresh-after-" in identifier
    )
    completed_refreshes = [
        identifier for identifier in refresh_ids
        if terminal.get(identifier, {}).get("status") == "completed"
        and terminal[identifier].get("release", {}).get("verified") is True
        and terminal[identifier].get("release", {}).get("keys_down") == []
        and terminal[identifier].get("release", {}).get("buttons_down") == []
    ]
    refresh_translations = [
        row for row in translations
        if isinstance(row.get("id"), str) and "-refresh-after-" in row["id"]
    ]
    refresh_horizons_ns = {
        row["id"]: row["host_deadline_ns"] - row["translated_at_host_ns"]
        for row in refresh_translations
    }

    source_mismatches = []
    for relative, expected in sources.items():
        path = REPO / "research" / relative
        actual = sha256(path) if path.is_file() else None
        if actual != expected:
            source_mismatches.append({"path": relative, "expected": expected, "actual": actual})

    verified_empty_owners = [
        row for row in owners
        if row.get("event") == "owner_release"
        and row.get("verified") is True
        and row.get("keys_down") == []
        and row.get("buttons_down") == []
    ]
    primary_programs = [
        row for row in events
        if row.get("event") == "terminal"
        and row.get("status") == "completed"
        and isinstance(row.get("id"), str)
        and "-primary-" in row["id"]
    ]
    raw_hashes = {
        str(path.relative_to(RUN)): sha256(path)
        for path in sorted(RUN.rglob("*"))
        if path.is_file() and path.name != "V10_RESULT_AUDIT.json"
    }

    result = {
        "classification": "HOLD_INCOMPLETE_24_DECISION_CLOCK_BOUNDARY_ERROR",
        "scoped_refresh_hypothesis": (
            "PASS_OBSERVE_REFRESH_AND_SUBSEQUENT_ACTION"
            if len(completed_refreshes) == len(refresh_ids) >= 1
            and primary_programs and verified_empty_owners
            else "HOLD_REFRESH_GATE_NOT_FULLY_OBSERVED"
        ),
        "scope": "read-only protocol/event/source/release audit; no replay, model call, or input",
        "allocation": {
            "issue": 4516,
            "predecessor_stop_issue": 4513,
            "seed": 990637,
            "output": str(RUN.relative_to(REPO)),
            "model": "gpt-5.6-luna",
            "effort": "low",
            "iterations_requested": 24,
            "fresh_map": "MAP01",
        },
        "observed": {
            "protocol_rows": len(protocol),
            "model_turn_status_counts": dict(Counter(row.get("status") for row in completed_turns)),
            "completed_model_turns": sum(row.get("status") == "completed" for row in completed_turns),
            "interrupted_model_turns": sum(row.get("status") == "interrupted" for row in completed_turns),
            "completed_model_authored_primary_programs": len(primary_programs),
            "exact_observations": sum(row.get("event") == "observation" for row in events),
            "typed_observations": sum(row.get("event") == "typed_observation" for row in events),
            "physical_input_admissions": sum(row.get("event") == "input_admission" for row in events),
            "refresh_ids": refresh_ids,
            "completed_verified_refreshes": completed_refreshes,
            "refresh_host_horizon_ns_after_clock_translation": refresh_horizons_ns,
            "refresh_deadline_is_15_seconds": bool(refresh_horizons_ns) and all(
                abs(value - 15_000_000_000) <= 10_000_000 for value in refresh_horizons_ns.values()
            ),
            "owner_release_count": len(owners),
            "verified_empty_owner_releases": len(verified_empty_owners),
            "all_owner_releases_verified_empty": bool(owners) and len(verified_empty_owners) == len(owners),
            "score_present": (RUN / "runtime/score.json").exists(),
            "report_present": (RUN / "report.json").exists(),
            "wad_sha256_matches": environment.get("iwad_sha256") == EXPECTED_WAD,
            "runtime_source_count": len(sources),
            "runtime_source_manifest_matches": not source_mismatches,
            "runtime_source_mismatches": source_mismatches,
            "effective_source_sha256": sha256(effective),
            "effective_source_sha256_matches_freeze": sha256(effective) == EXPECTED_EFFECTIVE,
            "only_15_second_refresh_anchor_present": (
                effective_text.count(refresh_literal) == 1
                and original_literal not in effective_text
            ),
            "runtime_event_counts": dict(Counter(row.get("event") for row in events)),
            "raw_file_count": len(raw_hashes),
            "raw_total_bytes": sum((RUN / name).stat().st_size for name in raw_hashes),
        },
        "classification_basis": [
            "all observed inter-segment observe-only 15-second refreshes were admitted and completed",
            "multiple later model-authored primary action programs completed after refreshes",
            "the runner stopped before the requested 24-decision horizon at final action admission",
            "there is no final report or independent score; do not infer gameplay failure or map exit",
            "all recorded owner releases must independently verify empty physical input",
        ],
        "raw_sha256": raw_hashes,
    }
    (RUN / "V10_RESULT_AUDIT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "classification": result["classification"],
        "scoped_refresh_hypothesis": result["scoped_refresh_hypothesis"],
        "observed": result["observed"],
    }, indent=2, sort_keys=True))
    if (not result["observed"]["runtime_source_manifest_matches"]
            or not result["observed"]["all_owner_releases_verified_empty"]
            or not result["observed"]["effective_source_sha256_matches_freeze"]
            or not result["observed"]["refresh_deadline_is_15_seconds"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
