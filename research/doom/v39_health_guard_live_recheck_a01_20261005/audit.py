"""Raw-bound recheck of the retained V39 live health-guard interruption."""
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "research/doom/results/map01-v39-coast-liveness-live-01"
FREEZE_COMMIT = "5ffa6e0716515841575f70b8f0dba32843bf3e98"
RESULT_COMMIT = "ebb8c7837edf86cc9d02c60bec58828e45fb6c77"
CURRENT_MAIN_SNAPSHOT = "b5be19963454ce5edafc945b78b100012952dd15"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def git_blob(commit, path):
    return subprocess.check_output(
        ["git", "show", f"{commit}:{path}"], cwd=ROOT)


def main():
    retained = json.loads((RUN / "retention-manifest.json").read_text())
    expected = {row["path"]: row["sha256"] for row in retained["files"]}
    checked = ["report.json", "runtime/events.jsonl", "runtime/sources.json",
               "runtime/218.png", "audit-v2.json"]
    hashes = {}
    for relative in checked:
        actual = sha256(RUN / relative)
        if expected.get(relative) != actual:
            raise SystemExit(f"retained hash mismatch: {relative}")
        hashes[relative] = actual

    audit = json.loads((RUN / "audit-v2.json").read_text())
    if audit.get("formal_pass") is not True or audit.get("completed") is not True:
        raise SystemExit("retained V39 audit is not a completed scoped PASS")
    report = json.loads((RUN / "report.json").read_text())
    decision = report["decisions"][5]
    source = decision["cover_validity_admission"]["source_signal"]
    invalidation = decision["policy_invalidation"]
    event_rows = [json.loads(line) for line in
                  (RUN / "runtime/events.jsonl").read_text().splitlines()]
    typed = next(row for row in event_rows
                 if row.get("event") == "typed_observation"
                 and row.get("sequence") == invalidation["sequence"])
    soft = next(row for row in event_rows
                if row.get("event") == "typed_observation"
                and row.get("sequence") == 200)
    terminal = next(row for row in event_rows
                    if row.get("event") == "terminal"
                    and row.get("id") == "cover-5")
    sources = json.loads((RUN / "runtime/sources.json").read_text())

    # The retained preregistration pins the production controller, while the
    # runtime source manifest pins imported dependencies. Verify both against
    # the earlier frozen Git tree; the two lists are complementary.
    subprocess.check_call(
        ["git", "merge-base", "--is-ancestor", FREEZE_COMMIT, RESULT_COMMIT],
        cwd=ROOT)
    prereg = json.loads(git_blob(
        FREEZE_COMMIT,
        "research/doom/map01_v39_coast_liveness_live_v1_prereg.json"))
    expected_sources = prereg.get("source_sha256", {})
    if (prereg.get("allocation_id") != "map01-v39-coast-liveness-live-01"
            or prereg.get("status") != "FROZEN_BEFORE_FIRST_V38_MODEL_CALL"
            or len(expected_sources) != 28):
        raise SystemExit("retained V39 preregistration identity mismatch")
    prereg_verified = []
    for path, expected_hash in expected_sources.items():
        if sha256_bytes(git_blob(FREEZE_COMMIT, path)) != expected_hash:
            raise SystemExit(f"preregistered source mismatch: {path}")
        prereg_verified.append(path)
    runtime_verified = []
    for path, expected_hash in sources.items():
        repository_path = f"research/{path}"
        if sha256_bytes(git_blob(FREEZE_COMMIT, repository_path)) != expected_hash:
            raise SystemExit(f"runtime source differs from freeze tree: {path}")
        runtime_verified.append(repository_path)
    controller_path = "research/doom/map01_overlap_controller_v39.py"
    frozen_controller_sha = expected_sources.get(controller_path)
    current_controller_sha = sha256_bytes(
        git_blob(CURRENT_MAIN_SNAPSHOT, controller_path))
    if (frozen_controller_sha is None
            or sha256_bytes(git_blob(FREEZE_COMMIT, controller_path))
               != frozen_controller_sha):
        raise SystemExit("frozen controller source identity missing or mismatched")
    prereg_runtime_overlap = sorted(set(prereg_verified) & set(runtime_verified))
    if len(prereg_runtime_overlap) != 9:
        raise SystemExit("unexpected preregistration/runtime source overlap")

    if (source.get("status") != "observed" or source.get("value") != 61
            or source.get("sequence") != 166):
        raise SystemExit("decision-5 source health identity mismatch")
    soft_summary = decision.get("cover_validity_latest_soft_event", {})
    if (soft.get("signals", {}).get("health", {}).get("value") != 51
            or soft_summary.get("sequence") != 200
            or soft_summary.get("signal", {}).get("value") != 51
            or soft_summary.get("outcome", {}).get("status") != "SOFT_CHANGED"
            or soft_summary.get("outcome", {}).get("keep_existing_policy") is not True):
        raise SystemExit("soft-boundary observation did not preserve the cover")
    guard = invalidation["outcome"]
    if (typed.get("signals", {}).get("health", {}).get("value") != 48
            or guard.get("status") != "HARD_INVALIDATED"
            or guard.get("reason") != "below_hard_minimum"
            or guard.get("hard_minimum") != 51):
        raise SystemExit("typed health event does not match guard invalidation")
    if (decision.get("planner_turn_status") != "interrupted"
            or decision.get("planner_answer_eligible") is not False
            or decision.get("model_action_discarded") is not True):
        raise SystemExit("pending planner answer was not recorded as discarded")
    if ("doom/session_map01_v12.py" not in sources
            or "live_control/input_owner_v10.py" not in sources
            or "doom/session_map01_v15.py" in sources
            or "live_control/input_owner_v12.py" in sources):
        raise SystemExit("source manifest no longer matches the stated legacy closure")
    release = terminal.get("release", {})
    if (terminal.get("status") != "cancelled"
            or release.get("verified") is not True
            or release.get("keys_down") != []
            or release.get("buttons_down") != []):
        raise SystemExit("cover terminal did not verify empty release")

    source_ns = source["capture_ns"]
    invalidation_ns = invalidation["outcome_evaluated_ns"]
    release_ns = release["verified_ns"]
    planner_terminal_ns = decision["planner_terminal_observed_ns"]
    if not source_ns < invalidation_ns < release_ns < planner_terminal_ns:
        raise SystemExit("source, guard, release, planner chronology is invalid")

    result = {
        "schema": "v39-health-guard-live-recheck-a01",
        "allocation_id": "map01-v39-coast-liveness-live-01",
        "retained_hashes": hashes,
        "retained_audit_formal_pass": True,
        "source_provenance": {
            "freeze_commit": FREEZE_COMMIT,
            "result_commit": RESULT_COMMIT,
            "freeze_is_ancestor_of_result": True,
            "preregistration_status": prereg["status"],
            "preregistered_sources_verified_against_freeze_tree": len(prereg_verified),
            "runtime_sources_verified_against_freeze_tree": len(runtime_verified),
            "combined_unique_sources_verified": len(set(prereg_verified)
                                                     | set(runtime_verified)),
            "prereg_runtime_overlap": len(prereg_runtime_overlap),
            "controller_sha256_at_freeze": frozen_controller_sha,
            "controller_sha256_at_current_main_snapshot": current_controller_sha,
            "controller_differs_from_current_main": (
                frozen_controller_sha != current_controller_sha),
        },
        "decision": 5,
        "cover_source": {"sequence": source["sequence"], "health": source["value"]},
        "soft_boundary_observation": {"sequence": soft["sequence"],
                                       "health": soft["signals"]["health"]["value"],
                                       "outcome": soft_summary["outcome"]["status"]},
        "hard_guard_observation": {"sequence": typed["sequence"],
                                   "health": typed["signals"]["health"]["value"],
                                   "hard_minimum": guard["hard_minimum"],
                                   "outcome": guard["status"],
                                   "frame": "runtime/218.png",
                                   "frame_sha256": hashes["runtime/218.png"]},
        "planner": {"model_ns": decision["model_ns"],
                    "terminal_status": decision["planner_turn_status"],
                    "answer_eligible": decision["planner_answer_eligible"],
                    "dependent_action_discarded": decision["model_action_discarded"]},
        "timing_ms": {
            "source_capture_to_guard_evaluation": (invalidation_ns-source_ns)/1e6,
            "guard_evaluation_to_empty_release": (release_ns-invalidation_ns)/1e6,
            "guard_evaluation_to_planner_terminal": (planner_terminal_ns-invalidation_ns)/1e6,
        },
        "release": {"verified": release["verified"], "keys_down": release["keys_down"],
                    "buttons_down": release["buttons_down"]},
        "source_closure": sorted(sources),
        "scope": {
            "kind": "read-only recheck of one retained live V39 episode",
            "source_version_boundary": "preregistration pins the older V39 controller and V12/V10 path; this is not today's V15/V12 startup closure",
            "proves": ["authored health guard invalidated during pending model turn",
                       "dependent answer was ineligible/discarded",
                       "cover ended with verified empty release"],
            "does_not_prove": ["current-main V15/V12 composition",
                               "per-key release identity", "independently useful feedback",
                               "bounded recovery efficacy", "MAP01 exit or survival benefit"],
            "new_game_or_model_allocation": False,
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
