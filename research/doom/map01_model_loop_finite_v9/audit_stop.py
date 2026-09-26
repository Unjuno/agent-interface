"""Read-only audit of the consumed v9 MAP01 allocation after infrastructure HOLD."""
from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / "results/map01-model-loop-finite-v9-20260926-01"
EXPECTED_IWAD = "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b"
LAUNCH_MAIN = "74ad7e3afc5ddbf43e3544d86780a210012ced34"
EXPECTED_ADAPTER = "a92be1f3dbfc8c64f58287188d75db6081987245c9267791b7de05a69d7d6447"
EXPECTED_EFFECTIVE = "edd4cea89c541d42457e8c48992d3efe1bcb0ab7610489b47e8efa60660aab3a"
ISSUE_CLAIMED_EFFECTIVE = "edd4cea89c541d42457e8c48992d3efe1bcb0ab7610489b47e8efa60660aab3"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    protocol = read_jsonl(RUN / "planner-protocol.jsonl")
    events = read_jsonl(RUN / "runtime/events.jsonl")
    owners = json.loads((RUN / "runtime/owner-events.json").read_text())
    environment = json.loads((RUN / "runtime/environment.json").read_text())
    sources = json.loads((RUN / "runtime/sources.json").read_text())
    root = HERE.parents[2]
    effective_path = HERE / "frozen-source/effective-controller.py"
    effective_source = effective_path.read_text()

    completed_turns = [
        row["message"]["params"]["turn"]
        for row in protocol
        if row.get("direction") == "received"
        and row.get("message", {}).get("method") == "turn/completed"
    ]
    model_answers = []
    for row in protocol:
        message = row.get("message", {})
        item = message.get("params", {}).get("item", {})
        if row.get("direction") == "received" and item.get("type") == "agentMessage":
            try:
                model_answers.append(json.loads(item["text"]))
            except (KeyError, TypeError, json.JSONDecodeError):
                pass

    refresh_deadline_is_five_seconds = '"valid_until_ns":clock_ns+5_000_000_000' in effective_source
    wrapper_requires_five_second_margin = "if _remaining<5_000_000_000:" in effective_source
    wrapper_samples_clock_before_margin_check = (
        effective_source.find("for _ in range(3):", effective_source.find("class _LeaseClockStdin"))
        < effective_source.find("_remaining=host_deadline-time.perf_counter_ns()")
    )

    completed_actions = [
        row for row in events
        if row.get("event") == "terminal"
        and row.get("status") == "completed"
        and str(row.get("id", "")).startswith("plan-")
    ]
    verified_empty_releases = [
        row for row in owners
        if row.get("event") == "owner_release"
        and row.get("verified") is True
        and row.get("buttons_down") == []
        and row.get("keys_down") == []
    ]
    all_owner_releases_verified_empty = (
        len(verified_empty_releases) == len(owners) and bool(owners)
    )
    planned_input = [row for row in events if row.get("event") == "input_admission"]
    observations = [row for row in events if row.get("event") == "observation"]
    typed = [row for row in events if row.get("event") == "typed_observation"]
    calibration = json.loads((RUN / "runtime/lease-clock-calibration.json").read_text())
    terminal_score_exists = (RUN / "runtime/score.json").exists()
    report_exists = (RUN / "report.json").exists()

    source_manifest_matches_frozen_files = True
    source_mismatches = []
    for rel, expected in sources.items():
        git_path = "research/" + rel
        checked = subprocess.run(
            ["git", "show", f"{LAUNCH_MAIN}:{git_path}"],
            cwd=root, capture_output=True, check=False,
        )
        actual = hashlib.sha256(checked.stdout).hexdigest() if checked.returncode == 0 else None
        if actual != expected:
            source_manifest_matches_frozen_files = False
            source_mismatches.append({"path": rel, "expected": expected, "actual": actual})
    effective_sha_matches_freeze = sha256(effective_path) == EXPECTED_EFFECTIVE
    adapter_path = root / "research/doom/map01_model_loop_finite_v7/adapter.py"
    adapter_sha_matches_freeze = sha256(adapter_path) == EXPECTED_ADAPTER

    raw_hashes = {
        str(path.relative_to(RUN)): sha256(path)
        for path in sorted(RUN.rglob("*"))
        if path.is_file() and path.name not in {"V9_STOP_AUDIT.json", "STOP_RECORD.md"}
    }
    result = {
        "classification": "HOLD_INFRASTRUCTURE_HOST_LEASE_MARGIN_BELOW_5S",
        "scope": "read-only protocol, runtime, release, source-manifest and stop audit; no replay or retry",
        "allocation": {
            "issue": 4484,
            "seed": 990635,
            "output": str(RUN.relative_to(HERE.parents[2])),
            "model": "gpt-5.6-luna",
            "effort": "low",
            "iterations_requested": 24,
            "fresh_map": "MAP01",
            "skill": 1,
        },
        "observed": {
            "planner_protocol_rows": len(protocol),
            "completed_model_turns": len(completed_turns),
            "completed_turn_statuses": dict(Counter(turn.get("status") for turn in completed_turns)),
            "valid_model_answers": len(model_answers),
            "model_authored_commands": sum(len(answer.get("commands", [])) for answer in model_answers),
            "model_action_programs_completed": len(completed_actions),
            "exact_observations": len(observations),
            "typed_observations": len(typed),
            "physical_input_admissions": len(planned_input),
            "owner_release_count": len(owners),
            "verified_empty_owner_releases": len(verified_empty_releases),
            "all_owner_releases_verified_empty": all_owner_releases_verified_empty,
            "episode_score_present": terminal_score_exists,
            "formal_report_present": report_exists,
            "iwad_sha256_matches_freeze": environment.get("iwad_sha256") == EXPECTED_IWAD,
            "runtime_source_count": len(sources),
            "source_manifest_matches_frozen_files": source_manifest_matches_frozen_files,
            "source_mismatches": source_mismatches,
            "launch_main": LAUNCH_MAIN,
            "adapter_sha256_matches_freeze": adapter_sha_matches_freeze,
            "effective_controller_sha256_matches_freeze": effective_sha_matches_freeze,
            "issue_4484_claimed_effective_sha256": ISSUE_CLAIMED_EFFECTIVE,
            "issue_4484_claimed_effective_sha256_length": len(ISSUE_CLAIMED_EFFECTIVE),
            "issue_4484_effective_sha256_was_malformed": len(ISSUE_CLAIMED_EFFECTIVE) != 64,
            "refresh_deadline_is_five_seconds": refresh_deadline_is_five_seconds,
            "wrapper_requires_five_second_margin": wrapper_requires_five_second_margin,
            "wrapper_samples_clock_before_margin_check": wrapper_samples_clock_before_margin_check,
            "five_second_refresh_margin_conflict": (
                refresh_deadline_is_five_seconds
                and wrapper_requires_five_second_margin
                and wrapper_samples_clock_before_margin_check
            ),
            "clock_calibration_sample_count": calibration.get("sample_count"),
            "clock_calibration_uncertainty_ns": calibration.get("uncertainty_ns"),
            "runtime_event_counts": dict(Counter(row.get("event") for row in events)),
            "raw_file_count": len(raw_hashes),
            "raw_total_bytes": sum((RUN / name).stat().st_size for name in raw_hashes),
        },
        "classification_basis": [
            "formal adapter stopped at the explicit host lease margin gate (<5 seconds); it did not label gameplay outcome",
            "the run produced fewer than the frozen 24 decisions and has no independent terminal score",
            "therefore neither finite-clear PASS nor gameplay FAIL is supported",
            "all owner release records must independently verify empty physical input",
        ],
        "raw_sha256": raw_hashes,
    }
    if not all_owner_releases_verified_empty:
        result["classification"] = "STOP_UNVERIFIED_PHYSICAL_RELEASE"
    if (environment.get("iwad_sha256") != EXPECTED_IWAD
            or not source_manifest_matches_frozen_files
            or not adapter_sha_matches_freeze
            or not effective_sha_matches_freeze):
        result["classification"] = "HOLD_INFRASTRUCTURE_PROVENANCE_MISMATCH"
    target = RUN / "V9_STOP_AUDIT.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "raw_sha256"}, indent=2, sort_keys=True))
    if result["classification"] != "HOLD_INFRASTRUCTURE_HOST_LEASE_MARGIN_BELOW_5S":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
