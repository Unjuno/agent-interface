from __future__ import annotations

import hashlib
import json
from pathlib import Path


PACKET = Path(__file__).resolve().parent


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit() -> dict:
    conditions_path = PACKET / "conditions.json"
    conditions = read_json(conditions_path)
    freeze = read_json(PACKET / "FREEZE.json")
    require(freeze["source_main"] == conditions["source_main"], "source main mismatch")
    require(freeze["conditions_sha256"] == sha256(conditions_path), "frozen conditions hash mismatch")
    require(freeze["runtime_tree_oid"] == conditions["runtime_tree_oid"], "runtime tree mismatch")
    for rel, expected in freeze["input_hashes"].items():
        require(sha256(PACKET / rel) == expected, f"frozen input hash mismatch: {rel}")
    preflight = read_json(PACKET / "raw" / "preflight-attempts.json")
    require(len(preflight["attempts"]) == 6, "preflight attempt receipt incomplete")
    for row in preflight["attempts"][:4]:
        require(row["status"] == "FAIL_SETUP" and row["observations"] == 0 and row["dispatches"] == 0, "setup-only failure was lost or misclassified")
    for row in preflight["attempts"][4:]:
        require(row["status"] == "PASS_HANDSHAKE_AND_TASK_ORACLE_REGISTERED" and row["tools"] == 12 and row["observations"] == 0 and row["dispatches"] == 0 and row["exit"] == 0, "final handshake preflight did not pass")
    require(len(conditions["trials"]) == 5, "frozen denominator is not five")
    require([x["ordinal"] for x in conditions["trials"]] == [1, 2, 3, 4, 5], "trial order mismatch")
    require(conditions["computer_use_activation"] == "activate exact returned window; verify title/HWND/PID and foreground; send no pointer or key input", "Computer Use activation method mismatch")
    ids = [cfg[k] for cfg in conditions["trials"] for k in ("trial_id", "program_id", "lease_id", "followup_program_id", "followup_lease_id")]
    require(len(ids) == 25 and len(set(ids)) == 25, "trial/program/lease identifiers are not all unique")

    for rel, expected in conditions["source_hashes"].items():
        require(sha256(PACKET / rel) == expected, f"source hash mismatch: {rel}")

    summary = read_json(PACKET / "raw" / "cohort-summary.json")
    require(summary["source_main"] == conditions["source_main"], "summary source main mismatch")
    require(summary["frozen_trials"] == 5, "summary denominator mismatch")
    require(len(summary["attempts"]) == 5, "not all frozen attempts have a result")
    require(summary["stopped_early"] is False, "cohort stopped early")
    require(summary["cohort_outcome"] == "PASS_SCOPED_FIVE_ATTEMPT_POST_RECOVERY_TASK_COHORT", "cohort did not pass")
    start_progress = read_json(PACKET / "raw" / "cohort-progress-start.json")
    final_progress = read_json(PACKET / "raw" / "cohort-progress.json")
    require(start_progress["completed_trials"] == 0 and start_progress["trials"] == [], "frozen initial progress is not empty")
    require(final_progress["completed_trials"] == 5 and len(final_progress["trials"]) == 5, "final progress denominator mismatch")

    audited = []
    for cfg, attempt in zip(conditions["trials"], summary["attempts"], strict=True):
        ordinal = cfg["ordinal"]
        folder = PACKET / "raw" / f"trial-{ordinal:02d}"
        require(attempt["ordinal"] == ordinal, f"trial {ordinal}: ordinal mismatch")
        require(attempt["trial_id"] == cfg["trial_id"], f"trial {ordinal}: trial identity mismatch")
        require(attempt["outcome"] == "RECOVERY_AND_NEW_TASK_VERIFIED", f"trial {ordinal}: outcome failed")
        require(attempt["fixture_closed"] is True and attempt["fresh_fixture_closed"] is True, f"trial {ordinal}: fixture cleanup failed")
        require(attempt["fence_status_after"] == "clear", f"trial {ordinal}: durable fence not clear")

        source = attempt["source"]
        require(source["status"] == "unknown", f"trial {ordinal}: source action not UNKNOWN")
        require(source["input_dispatched"] is True, f"trial {ordinal}: source dispatch absent")
        require(source["release_confirmed"] is False, f"trial {ordinal}: source release not uncertain")
        require(source["task_success"] is None, f"trial {ordinal}: source task result was attributed")
        require(source["replay_allowed"] is False, f"trial {ordinal}: source replay allowed")

        program = read_json(folder / "program.json")
        effect = read_json(folder / "effect.json")
        require(effect["verified"] is True and effect["text"] == "a", f"trial {ordinal}: delayed A effect missing")
        require(effect["effect_observed_ns"] > program["authority"]["expires_at_ns"], f"trial {ordinal}: A effect not post-expiry")

        recovery = read_json(folder / "orphan-recovery-body.json")
        receipt = recovery["recovery_receipt"]
        require(recovery["status"] == "recovered", f"trial {ordinal}: public recovery failed")
        require(recovery["source_action_status"] == "unknown" and recovery["replay_allowed"] is False, f"trial {ordinal}: source custody changed")
        require(recovery["source_operation_id"] == source["operation_id"], f"trial {ordinal}: recovery operation mismatch")
        require(receipt["release_confirmed"] is True and receipt["late_input_horizon_verified"] is True, f"trial {ordinal}: release/horizon unverified")
        require(receipt["late_input_horizon_ns"] == cfg["horizon_ms"] * 1_000_000, f"trial {ordinal}: wrong recovery horizon")
        require(receipt["readback"]["neutral"] is True, f"trial {ordinal}: non-neutral readback")

        for name, position, title in (
            ("foreground-pre-dispatch.json", cfg["source_window_position"], cfg["window_title"]),
            ("foreground-pre-followup.json", cfg["followup_window_position"], cfg["followup_window_title"]),
        ):
            fg = read_json(folder / name)
            require(fg["foreground_matches"] is True and fg["title"] == title, f"trial {ordinal}: {name} identity mismatch")
            require(fg["window_rect"][:2] == position, f"trial {ordinal}: {name} position mismatch")

        for name, title in (
            ("computer-use-foreground-confirmed.json", cfg["window_title"]),
            ("computer-use-followup-foreground-confirmed.json", cfg["followup_window_title"]),
        ):
            marker = read_json(folder / name)
            require(marker["title"] == title, f"trial {ordinal}: {name} title mismatch")
            require(marker["activated_exact_target"] is True and marker["computer_input_sent"] is False, f"trial {ordinal}: {name} activation evidence missing or injected input occurred")

        target = read_json(folder / "window.json")
        fresh = read_json(folder / "fresh-task-target" / "target.json")
        for name, expected in (("computer-use-foreground-confirmed.json", target), ("computer-use-followup-foreground-confirmed.json", fresh)):
            marker = read_json(folder / name)
            require(marker["hwnd"] == expected["hwnd"] and marker["pid"] == expected["pid"], f"trial {ordinal}: {name} target identity mismatch")
        require(target["hwnd"] != fresh["hwnd"] and target["pid"] != fresh["pid"], f"trial {ordinal}: target process/window reused")
        followup = read_json(folder / "followup-action-result.json")
        action = followup["action"]
        execution = action["result"]["execution"]
        require(action["status"] == "completed" and action["release_confirmed"] is True, f"trial {ordinal}: follow-up action failed/release unverified")
        require(action["replay_allowed"] is False, f"trial {ordinal}: follow-up replay allowed")
        require(action["operation_id"] == attempt["followup_operation_id"], f"trial {ordinal}: follow-up operation mismatch")
        require(action["target_generation"] != source["target_generation"], f"trial {ordinal}: generation reused")

        verify = read_json(folder / "followup-task-verification.json")
        oracle = verify["receipt"]
        require(verify["status"] == "verified" and verify["task_success"] is True, f"trial {ordinal}: independent task oracle failed")
        require(oracle["call_id"] == attempt["followup_call_id"], f"trial {ordinal}: oracle call mismatch")
        require(oracle["operation_id"] == action["operation_id"], f"trial {ordinal}: oracle operation mismatch")
        require(oracle["target_generation"] == action["target_generation"], f"trial {ordinal}: oracle generation mismatch")
        events = [json.loads(line) for line in (folder / "fresh-task-target" / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        matching = [e for e in events if e.get("kind") == "char" and e.get("text") == "b"]
        require(any(execution["started_ns"] <= e["monotonic_ns"] <= execution["ended_ns"] for e in matching), f"trial {ordinal}: no B event inside dispatch interval")

        before = read_json(folder / "fence-before.json")
        after = read_json(folder / "fence-after.json")
        require(before["status"] == "clear" and before.get("pending") is None, f"trial {ordinal}: fence not clear before")
        require(after["status"] == "clear" and after.get("pending") is None, f"trial {ordinal}: fence not clear after")
        audited.append({"ordinal": ordinal, "trial_id": cfg["trial_id"], "outcome": attempt["outcome"], "recovery": "verified", "task_success": True})

    manifest_path = PACKET / "SHA256SUMS.txt"
    manifest_verified = False
    if manifest_path.exists():
        rows = [line.strip() for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        require(bool(rows), "empty SHA256 manifest")
        for row in rows:
            digest, rel = row.split("  ", 1)
            path = PACKET / rel
            require(path.is_file() and sha256(path) == digest, f"manifest hash mismatch: {rel}")
        manifest_verified = True

    return {"status": "PASS_R43_EVIDENCE_RECOMPUTATION", "manifest_verified": manifest_verified, "source_main": conditions["source_main"], "audited_trials": audited}


if __name__ == "__main__":
    try:
        print(json.dumps(audit(), indent=2, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status": "FAIL_R43_EVIDENCE_RECOMPUTATION", "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        raise
