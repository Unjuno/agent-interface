"""Recover and preserve the first frozen early-typed allocation failure."""
import hashlib
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path[:0] = [str(HERE), str(HERE.parent / "live_control")]
from doom_hud_signal_v3 import DoomStatusNumberReader
from doom_typed_observation_v1 import reconcile_artifact


ROOT = REPO / "results-local/doom/map01-early-typed-cancel-live-01"
PREREG = HERE / "map01_early_typed_cancel_live_v1_prereg.json"
WAD = REPO / "_vizdoom/vizdoom/freedoom2.wad"
IDENTIFIER = "early-typed-running-action-fire-01"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    plan = read(PREREG)
    events = [json.loads(line) for line in
              (ROOT / "runtime/events.jsonl").read_text(encoding="utf-8").splitlines()]
    typed = {row["sequence"]: row for row in events
             if row.get("event") == "typed_observation"}
    full = {row["sequence"]: row for row in events
            if row.get("event") == "observation"}
    readers = {name: DoomStatusNumberReader(WAD, signal_id=name)
               for name in ("health", "ammo")}
    reconciliations = []
    for sequence, early in sorted(typed.items()):
        receipt = reconcile_artifact(early, full.get(sequence), readers)
        receipt["sequence"] = sequence
        reconciliations.append(receipt)
    accepted = next(row for row in events if row.get("event") == "accepted" and
                    row.get("id") == IDENTIFIER)
    cancel = next(row for row in events if row.get("event") == "cancel_requested" and
                  row.get("id") == IDENTIFIER)
    terminal = next(row for row in events if row.get("event") == "terminal" and
                    row.get("id") == IDENTIFIER)
    invalidating = next(row for row in typed.values()
                        if row["signals"]["ammo"]["value"] == 47)
    artifact = full[invalidating["sequence"]]
    owner = read(ROOT / "runtime/owner-events.json")
    cancel_release = next(row for row in owner if row.get("reason") == "cancelled")
    score = read(ROOT / "runtime/score.json")
    capture_ns = invalidating["capture_ns"]
    metrics = {
        "capture_to_typed_ready_ms":
            (invalidating["typed_ready_ns"] - capture_ns) / 1e6,
        "capture_to_typed_emit_ms":
            (invalidating["emit_ns"] - capture_ns) / 1e6,
        "typed_emit_to_cancel_requested_ms":
            (cancel["requested_ns"] - invalidating["emit_ns"]) / 1e6,
        "capture_to_cancel_requested_ms":
            (cancel["requested_ns"] - capture_ns) / 1e6,
        "capture_to_owner_cancel_release_ms":
            (cancel_release["verified_ns"] - capture_ns) / 1e6,
        "capture_to_terminal_release_ms":
            (terminal["release"]["verified_ns"] - capture_ns) / 1e6,
        "capture_to_artifact_ready_ms":
            (artifact["artifact_ready_ns"] - capture_ns) / 1e6,
        "cancel_requested_before_artifact_ms":
            (artifact["artifact_ready_ns"] - cancel["requested_ns"]) / 1e6,
    }
    later_inputs = [row for row in events if row.get("event") == "input_admission" and
                    row.get("admitted_ns", 0) > cancel["requested_ns"]]
    evidence = {
        "frozen_sources_match": all(sha(REPO / name) == digest
                                    for name, digest in plan["source_sha256"].items()),
        "three_typed_full_pairs_reconcile":
            len(typed) == len(full) == 3 and all(row["matched"] for row in reconciliations),
        "natural_visible_ammo_decrement":
            typed[1]["signals"]["ammo"]["value"] == 48 and
            invalidating["signals"]["ammo"]["value"] == 47,
        "attested_acceptance": isinstance(accepted.get("program_sha256"), str) and
                                len(accepted["program_sha256"]) == 64,
        "matched_cancel": cancel["matched"] is True,
        "cancel_before_artifact": cancel["requested_ns"] < artifact["artifact_ready_ns"],
        "owner_cancel_release_empty": cancel_release["verified"] is True and
                                      cancel_release["keys_down"] == [] and
                                      cancel_release["buttons_down"] == [],
        "no_later_input_admission": not later_inputs,
        "terminal_failed_wrong_exception_identity":
            terminal["status"] == "failed" and terminal["error"] == "Cancelled()",
        "terminal_release_empty": terminal["release"]["verified"] is True and
                                  terminal["release"]["keys_down"] == [] and
                                  terminal["release"]["buttons_down"] == [],
        "score_and_owner_close_retained":
            score["event"] == "post_control_score" and
            any(row.get("reason") == "close" and row.get("verified") is True
                for row in owner),
    }
    thresholds = {
        "capture_to_cancel_requested":
            metrics["capture_to_cancel_requested_ms"] <=
            plan["thresholds_ms"]["capture_to_cancel_requested_lte"],
        "capture_to_terminal_release":
            metrics["capture_to_terminal_release_ms"] <=
            plan["thresholds_ms"]["capture_to_release_verified_lte"],
        "capture_to_guard_decision": "unknown because the frozen wrapper failed before report serialization",
    }
    failure = {
        "allocation_id": plan["allocation_id"],
        "allocation_passed": False,
        "wrapper_exit_code": 1,
        "child_process_exit_code": "not serialized; post_control_score and owner close retained",
        "failure_class": "executor_exception_identity_mismatch",
        "failure": "typed coast backend raises executor_v3.Cancelled while executor_v10 catches a separately defined Cancelled class; terminal is failed rather than cancelled",
        "evidence": evidence,
        "threshold_outcomes": thresholds,
        "metrics_ms": metrics,
        "accepted": accepted,
        "cancel_requested": cancel,
        "terminal": terminal,
        "owner_cancel_release": cancel_release,
        "typed_artifact_reconciliations": reconciliations,
        "score": score,
        "repair_candidate": "version Executor again and reuse executor_v3 Cancelled/DecisionRequired identities while retaining program attestation; do not alter frozen v10 or retry this allocation",
        "limits": "posthoc recovery from retained raw events; exact guard-decision timestamp and child exit code were not serialized",
    }
    (ROOT / "failure.json").write_text(
        json.dumps(failure, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"allocation_passed": False,
                      "failure_class": failure["failure_class"],
                      "metrics_ms": metrics,
                      "evidence_all": all(evidence.values())}, indent=2))


if __name__ == "__main__":
    main()
