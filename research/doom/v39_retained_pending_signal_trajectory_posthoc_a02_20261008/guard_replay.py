"""Replay exact frozen V39 guard semantics on the retained typed observations."""
import argparse
import hashlib
import importlib.util
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
FREEZE = json.loads((ROOT / "GUARD_FREEZE.json").read_text(encoding="utf-8"))


def load_guard():
    source = ROOT / FREEZE["runtime_guard"]["snapshot"]
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != FREEZE["runtime_guard"]["sha256"]:
        raise ValueError("frozen guard snapshot hash mismatch")
    blob = subprocess.check_output(
        ["git", "-C", str(REPO), "rev-parse",
         f"{FREEZE['current_main_commit']}:{FREEZE['runtime_guard']['path']}"],
        text=True,
    ).strip()
    if blob != FREEZE["runtime_guard"]["git_blob"]:
        raise ValueError("frozen main guard blob mismatch")
    spec = importlib.util.spec_from_file_location("frozen_observable_signal_guard", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ObservableSignalGuard


def compute():
    from analyze import reconstruct

    for name, expected in FREEZE["prior_a01_inputs"].items():
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"frozen A01 input hash mismatch: {name}")
    Guard = load_guard()
    result = reconstruct(ROOT)
    delivered = [json.loads(line) for line in (ROOT / "delivered.jsonl").read_text(encoding="utf-8").splitlines() if line]
    observations = {row["sequence"]: row for row in delivered
                    if row.get("event") == "typed_observation" and type(row.get("sequence")) is int}
    decisions = []
    for window in result["decision_windows"]:
        policy = window["authored_policy"]
        if policy is None:
            continue
        source_row = observations[window["source_sequence"]]
        source_signal = source_row["signals"]["health"]
        if source_signal["value"] != window["source_health"]:
            raise ValueError("source health differs from reconstructed window")
        floor = max(policy["critical_health_minimum"],
                    window["source_health"] - policy["maximum_health_loss"])
        if floor != window["effective_hard_minimum"]:
            raise ValueError("effective floor differs from authored policy")
        spec = {
            "op": "observable_signal_guard",
            "guard_id": f"retained-replay-{window['decision']}",
            "source_sequence": source_signal["sequence"],
            "signal_id": "health",
            "source_value": source_signal["value"],
            "hard_minimum": floor,
            "max_source_age_ms": policy["max_source_age_ms"],
            "on_soft_change": "preserve_existing_policy",
            "on_hard_change": "needs_decision",
            "on_unknown": "needs_decision",
        }
        guard = Guard(spec, source_signal, source_signal["binding"])
        statuses = Counter()
        equal_floor = []
        hard_events = []
        unknown_events = []
        for sequence in range(window["source_sequence"] + 1, window["last_pending_sequence"] + 1):
            row = observations.get(sequence)
            if row is None:
                raise ValueError(f"missing typed observation sequence {sequence}")
            signal = row["signals"]["health"]
            outcome = guard.evaluate(signal)
            statuses[outcome["status"]] += 1
            if signal.get("status") == "observed" and signal.get("value") == floor:
                equal_floor.append(sequence)
            if outcome["status"] == "HARD_INVALIDATED":
                hard_events.append({"sequence": sequence, "health": signal.get("value"),
                                    "reason": outcome["reason"],
                                    "grants_input_authority": outcome["grants_input_authority"]})
            if outcome["status"] == "UNKNOWN":
                unknown_events.append({"sequence": sequence, "reason": outcome["reason"]})
        decisions.append({
            "decision": window["decision"],
            "source_sequence": window["source_sequence"],
            "source_health": window["source_health"],
            "hard_minimum": floor,
            "observations_replayed": sum(statuses.values()),
            "status_counts": dict(sorted(statuses.items())),
            "floor_equal_sequences": equal_floor,
            "hard_events": hard_events,
            "unknown_events": unknown_events,
        })
    return {
        "schema": "v39-retained-guard-outcome-replay-v1",
        "classification": "POSTHOC_REPLAY_NOT_NEW_LIVE_ALLOCATION",
        "current_main_commit": FREEZE["current_main_commit"],
        "runtime_guard_git_blob": FREEZE["runtime_guard"]["git_blob"],
        "input_sha256": FREEZE["prior_a01_inputs"],
        "decision_count": len(decisions),
        "decisions": decisions,
        "recorded_policy_invalidations": result["recorded_policy_invalidations"],
        "limitations": [
            "Historical HUD-template signals are not independent game-state ground truth.",
            "The replay classifies guard outcomes only; it does not prove live scheduling, recovery, causality, or task effect.",
            "No game, model, controller, GUI, or OS input was run.",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = compute()
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        if args.output.exists():
            raise FileExistsError(f"refusing to overwrite {args.output}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
