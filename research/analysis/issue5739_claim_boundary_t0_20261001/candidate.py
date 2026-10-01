"""Deterministic finite claim-boundary candidate; no external I/O."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build_result(screen, confirmatory):
    selection = screen["selection"]
    baseline = screen["baseline"]
    survivors = []
    screened_out = []
    screen_attempts = []
    for arm, row in sorted(screen["arms"].items()):
        selected = row["correct"] >= selection["minimum_correct"] and not (
            selection["exclude_hard_safety_violation"] and row["hard_safety_violation"]
        )
        if arm == baseline:
            selected = True
        elif selected:
            survivors.append(arm)
        else:
            screened_out.append(arm)
        screen_attempts.append({
            "attempt_id": f"screen:{arm}:0",
            "phase": "screen",
            "arm": arm,
            "survived": selected,
            "correct": row["correct"],
            "opportunities": row["opportunities"],
            "hard_safety_violation": row["hard_safety_violation"],
        })

    baseline_rows = {row["variant"]: row for row in confirmatory["arms"][baseline]}
    confirm_attempts = []
    per_arm = {}
    for arm in survivors:
        deltas = []
        safety_failed = False
        for row in confirmatory["arms"][arm]:
            variant = row["variant"]
            baseline_row = baseline_rows[variant]
            confirm_attempts.append({
                "attempt_id": f"confirm:{screen['family_id']}:{arm}:{variant}",
                "phase": "confirm",
                "family_id": screen["family_id"],
                "arm": arm,
                "baseline": baseline,
                "variant": variant,
                "candidate_latency_ms": row["latency_ms"],
                "baseline_latency_ms": baseline_row["latency_ms"],
                "hard_safety_violation": row["hard_safety_violation"],
            })
            deltas.append(baseline_row["latency_ms"] - row["latency_ms"])
            safety_failed = safety_failed or row["hard_safety_violation"]
        per_arm[arm] = {
            "finite_descriptive_deltas_ms": deltas,
            "mean_descriptive_delta_ms": sum(deltas) / len(deltas),
            "disposition": "WITHHOLD_HARD_SAFETY_FAILURE" if safety_failed else "DESCRIPTIVE_ONLY_NO_PROMOTION",
        }

    family_members = [arm for arm in survivors if arm != baseline]
    return {
        "schema": "issue5739-candidate-output-v1",
        "screen_attempts": screen_attempts,
        "confirm_attempts": confirm_attempts,
        "survivors": survivors,
        "screened_out": screened_out,
        "family": {
            "family_id": screen["family_id"],
            "members": family_members,
            "rule": screen["survivor_family_rule"],
            "claim": "WITHHELD_NO_FAMILYWISE_INFERENCE",
        },
        "per_arm": per_arm,
        "global_best_claim": "NOT_ESTABLISHED_SCREENED_ARM_NOT_CONFIRMED",
        "promotion": "WITHHELD",
    }


def main():
    screen = json.loads((ROOT / "screen.json").read_text(encoding="utf-8"))
    confirmatory = json.loads((ROOT / "confirmatory.json").read_text(encoding="utf-8"))
    raw = (json.dumps(build_result(screen, confirmatory), sort_keys=True, indent=2) + "\n").encode()
    (ROOT / "CANDIDATE.json").write_bytes(raw)
    (ROOT / "STDOUT.bin").write_bytes(raw)
    (ROOT / "STDERR.bin").write_bytes(b"")
    (ROOT / "EXECUTION.json").write_text(json.dumps({
        "command": "python -B candidate.py",
        "exit_code": 0,
        "stdout_sha256": hashlib.sha256(raw).hexdigest(),
        "stderr_sha256": hashlib.sha256(b"").hexdigest(),
        "candidate_sha256": hashlib.sha256(raw).hexdigest(),
        "candidate_invocations": 1,
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(raw.decode("utf-8"), end="")


if __name__ == "__main__":
    main()
