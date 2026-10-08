"""Independent raw-only reconstruction of retained held-input bounds."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from statistics import median


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
DATA = {
    "v38": ROOT / "research/doom/results/map01-v38-integrated-threat-live-01/runtime/events.jsonl",
    "v39": ROOT / "research/doom/results/map01-v39-coast-liveness-live-01/runtime/events.jsonl",
}
LIMITATIONS = [
    "bounds owner-commanded X11 input, not continuous query_keymap occupancy",
    "requires the retained session-v4/session-v5 hold source ordering",
    "does not identify task-useful effect",
    "does not turn v38/v39 into a causal comparison",
]


def read_trace(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def reconstruct(trace: list[dict]) -> dict:
    plans: dict[tuple[str, int], dict] = {}
    for event in trace:
        if event.get("event") == "command":
            command = event.get("command", {})
            if command.get("op") == "submit":
                for pos, step in enumerate(command.get("steps", [])):
                    plans[(command["id"], pos)] = step

    finished: list[dict] = []
    cut_short: list[dict] = []
    current: dict | None = None
    for event in trace:
        kind = event.get("event")
        if kind == "step_started" and event.get("operation") == "hold":
            ident = (event["id"], event["step"])
            if current is not None:
                raise ValueError("overlap in retained hold trace")
            plan = plans.get(ident)
            if not isinstance(plan, dict) or plan.get("op") != "hold":
                raise ValueError(f"missing raw submit step {ident}")
            current = {
                "id": ident[0], "step": ident[1],
                "duration": plan["duration_ms"], "keys": plan["keys"],
                "acks": [], "observations": [],
            }
            continue
        if current is None:
            continue

        if kind == "input_admission":
            current["acks"].append(event["input_ack_ns"])
        elif kind == "observation" and (event.get("id"), event.get("step")) == (current["id"], current["step"]):
            current["observations"].append(event)
        elif kind == "input_released" and event.get("id") == current["id"]:
            release = event.get("owner_release", {})
            if release.get("verified") is True:
                if not current["acks"]:
                    raise ValueError("verified interruption lacks input admission")
                acknowledged = max(current["acks"])
                cut_short.append({
                    "id": current["id"], "step": current["step"],
                    "requested_ms": current["duration"], "keys": current["keys"],
                    "full_keyset_ack_ns": acknowledged,
                    "empty_verified_ns": release["verified_ns"],
                    "ack_to_empty_verified_ms": (release["verified_ns"] - acknowledged) / 1e6,
                    "classification": "interrupted_empty_verified",
                })
        elif kind == "step_completed" and (event.get("id"), event.get("step")) == (current["id"], current["step"]):
            if len(current["acks"]) != len(current["keys"]):
                raise ValueError("admitted-key count differs from raw hold key set")
            if len(current["observations"]) < 2:
                raise ValueError("fewer than two raw observations around release")
            ack = max(current["acks"])
            lower_ns = current["observations"][-2]["artifact_ready_ns"]
            upper_ns = current["observations"][-1]["capture_ns"]
            if not ack <= lower_ns <= upper_ns <= event["completed_ns"]:
                raise ValueError("raw event chronology violates the bound")
            lower = (lower_ns - ack) / 1e6
            upper = (upper_ns - ack) / 1e6
            requested = current["duration"]
            finished.append({
                "id": current["id"], "step": current["step"],
                "requested_ms": requested, "keys": current["keys"],
                "full_keyset_ack_ns": ack, "release_issue_lower_ns": lower_ns,
                "release_complete_upper_ns": upper_ns,
                "owner_commanded_hold_lower_ms": lower,
                "owner_commanded_hold_upper_ms": upper,
                "overshoot_lower_ms": lower - requested,
                "overshoot_upper_ms": upper - requested,
                "bound_width_ms": (upper_ns - lower_ns) / 1e6,
                "classification": "ordinary_completed_bounded",
            })
            current = None
        elif kind == "terminal" and event.get("id") == current["id"]:
            current = None

    requested = sum(row["requested_ms"] for row in finished)
    lower_total = sum(row["owner_commanded_hold_lower_ms"] for row in finished)
    upper_total = sum(row["owner_commanded_hold_upper_ms"] for row in finished)
    return {
        "schema": "held-input-telemetry-bound-v1",
        "completed_holds": finished,
        "interrupted_holds": cut_short,
        "summary": {
            "completed_hold_count": len(finished),
            "interrupted_verified_count": len(cut_short),
            "requested_total_ms": requested,
            "owner_commanded_hold_total_lower_ms": lower_total,
            "owner_commanded_hold_total_upper_ms": upper_total,
            "overshoot_total_lower_ms": lower_total - requested,
            "overshoot_total_upper_ms": upper_total - requested,
            "overshoot_fraction_lower": (lower_total - requested) / requested if requested else None,
            "overshoot_fraction_upper": (upper_total - requested) / requested if requested else None,
            "median_overshoot_lower_ms": median(row["overshoot_lower_ms"] for row in finished) if finished else None,
            "median_overshoot_upper_ms": median(row["overshoot_upper_ms"] for row in finished) if finished else None,
        },
        "limitations": LIMITATIONS,
    }


def same_value(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=0.0, abs_tol=1e-9)
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same_value(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same_value(x, y) for x, y in zip(a, b))
    return a == b


def main() -> None:
    checks = []
    details = {}
    for label, raw_path in DATA.items():
        expected = reconstruct(read_trace(raw_path))
        candidate_path = OUT / f"candidate_{label}.json"
        claimed = json.loads(candidate_path.read_text(encoding="utf-8"))
        row_ok = same_value(expected["completed_holds"], claimed.get("completed_holds"))
        stop_ok = same_value(expected["interrupted_holds"], claimed.get("interrupted_holds"))
        summary_ok = same_value(expected["summary"], claimed.get("summary"))
        limits_ok = same_value(expected["limitations"], claimed.get("limitations"))
        expected_rows = 11 if label == "v38" else 27
        expected_interrupts = 0 if label == "v38" else 1
        counts_ok = len(expected["completed_holds"]) == expected_rows and len(expected["interrupted_holds"]) == expected_interrupts

        # Negative controls exercise the auditor's own comparison gate.
        omitted = dict(claimed)
        omitted["completed_holds"] = claimed["completed_holds"][:-1]
        wrong_time = json.loads(json.dumps(claimed))
        wrong_time["completed_holds"][0]["full_keyset_ack_ns"] += 1
        wrong_total = json.loads(json.dumps(claimed))
        wrong_total["summary"]["completed_hold_count"] += 1
        mutations_rejected = not same_value(expected, omitted) and not same_value(expected, wrong_time) and not same_value(expected, wrong_total)
        checks.extend([row_ok, stop_ok, summary_ok, limits_ok, counts_ok, mutations_rejected])
        details[label] = {
            "completed_rows": len(expected["completed_holds"]),
            "interrupted_rows": len(expected["interrupted_holds"]),
            "candidate_rows_match": row_ok,
            "candidate_interrupted_match": stop_ok,
            "aggregate_match": summary_ok,
            "limitations_match": limits_ok,
            "expected_counts_match": counts_ok,
            "three_auditor_mutations_rejected": mutations_rejected,
            "raw_reconstructed_summary": expected["summary"],
        }

    result = {
        "status": "PASS_RAW_RECEIPT_REPRODUCED" if all(checks) else "FAIL_RAW_RECEIPT_MISMATCH",
        "checks_passed": sum(checks), "checks_total": len(checks),
        "independent_raw_only_reconstruction": True,
        "details": details,
        "scope": "historical owner-commanded X11 input interval bounds only; physical keymap occupancy, task-useful feedback, causality, live safety and product benefit are not identified",
    }
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (OUT / "audit.json").write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    raise SystemExit(0 if all(checks) else 1)


if __name__ == "__main__":
    main()
