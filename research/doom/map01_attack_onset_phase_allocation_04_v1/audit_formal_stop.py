"""Independent evidence audit for a one-shot pre-observation formal STOP."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(formal: Path, runtime_source: Path | None = None) -> dict:
    formal = formal.resolve()
    if runtime_source is not None:
        runtime_source = runtime_source.resolve()
    result = read_json(formal / "FORMAL_RESULT.json")
    execution = read_json(ROOT / "FORMAL_EXECUTION.json")
    case = formal / "p1-immediate"
    launch = read_json(case / "launch.json")
    controller = read_json(case / "controller_events.json")
    runtime = case / "runtime"
    runtime_sources = read_json(runtime / "sources.json")
    source_manifest = read_json(ROOT / "RUNTIME_SOURCE_HASHES.json")
    stderr = launch.get("failure")

    expected_sources = source_manifest.get("files", {})
    identity_checks = {
        relative: runtime_sources.get(relative) == record.get("sha256")
        for relative, record in expected_sources.items()
    }
    local_file_checks = {}
    if runtime_source is not None:
        for relative, record in expected_sources.items():
            source = runtime_source / "research" / relative
            local_file_checks[relative] = source.is_file() and sha(source) == record.get("sha256")

    no_session_streams = all(
        not (runtime / name).exists()
        for name in (
            "events.jsonl",
            "delivered.jsonl",
            "scorer-samples.jsonl",
            "score.json",
            "owner-events.json",
        )
    )
    checks = {
        "single_formal_invocation": result.get("formal_invocations") == 1
        and execution.get("formal_invocations") == 1,
        "no_retry_replacement_or_tuning": all(
            result.get(k) == 0 and execution.get(k) == 0
            for k in ("reruns", "replacements", "tuning_after_freeze")
        ),
        "typed_stop_matches_first_scheduled_case": result.get("decision")
        == "FAIL_FORMAL_RUNTIME_OR_SCHEMA"
        and isinstance(result.get("stop"), dict)
        and result["stop"].get("case_id") == "p1-immediate"
        and result["stop"].get("arm") == "IMMEDIATE"
        and result["stop"].get("error") == "RuntimeError('stdout closed: ')"
        and launch.get("case_id") == "p1-immediate"
        and launch.get("arm") == "IMMEDIATE"
        and launch.get("seed") == 992600
        and launch.get("pre_roll_ms") == 0,
        "no_controller_command_or_physical_edge": controller == []
        and result.get("rows") == []
        and result.get("pairs") == []
        and result.get("physical_clean") is False,
        "no_ready_observation_or_scorer_stream": no_session_streams
        and not launch.get("markers"),
        "setup_diagnostics_are_empty": (runtime / "setup.txt").is_file()
        and (runtime / "setup.txt").stat().st_size == 0
        and stderr == "RuntimeError('stdout closed: ')",
        "result_is_not_scientific": result.get("decision")
        == "FAIL_FORMAL_RUNTIME_OR_SCHEMA"
        and result.get("rows") == []
        and execution.get("scientific_result") is False,
        "runtime_source_identities_match_frozen_manifest": bool(identity_checks)
        and len(runtime_sources) == len(expected_sources)
        and all(identity_checks.values()),
        "execution_manifest_matches_runner": execution.get("exit_code") == 1
        and execution.get("runner_decision") == result.get("decision")
        and execution.get("root_cause", "").startswith("UNDETERMINED"),
    }
    return {
        "schema": "map01-attack-onset-allocation-04-formal-stop-audit-v1",
        "decision": "PASS_STOP_EVIDENCE_COMPLETE" if all(checks.values()) else "HOLD_STOP_EVIDENCE_INCOMPLETE",
        "checks": checks,
        "runtime_source_entries": len(identity_checks),
        "runtime_source_entries_matching": sum(identity_checks.values()),
        "runtime_source_local_files_checked": len(local_file_checks),
        "runtime_source_local_files_matching": sum(local_file_checks.values()),
        "formal_invocations": result.get("formal_invocations"),
        "session_attempts": 1,
        "completed_sessions": 0,
        "first_observations": 0,
        "physical_inputs": 0,
        "scientific_result": False,
        "root_cause": "UNDETERMINED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--formal", type=Path, required=True)
    parser.add_argument("--runtime-source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.formal, args.runtime_source)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["decision"] == "PASS_STOP_EVIDENCE_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
