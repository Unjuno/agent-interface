"""Deterministic synthetic 2x2 feedback/update-rule experiment for Issue #8319."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SEEDS = tuple(range(100))
FEEDBACKS = ("FULL", "CONTROLLED")
UPDATERS = ("CASE_PATCH", "STRATUM_PATCH")
PATCHES = tuple([f"case:{i}" for i in range(8)] + [f"stratum:{i}" for i in range(4)])
ROUNDS = 4


def cohort(seed: int, fresh: bool) -> list[dict]:
    prefix = "F" if fresh else "D"
    return [
        {"id": f"{prefix}{seed:03d}-{i:02d}", "stratum": (i + seed) % 4,
         "base_ok": ((i * 3 + seed) % 5) not in (0, 1)}
        for i in range(32)
    ]


def patch_changes(case: dict, patch: str) -> bool:
    kind, value = patch.split(":")
    if kind == "case":
        return not case["id"].startswith("F") and int(case["id"].split("-")[1]) == int(value)
    return case["stratum"] == int(value)


def score(cases: list[dict], patches: list[str]) -> tuple[int, int]:
    correct = sum(case["base_ok"] or any(patch_changes(case, p) for p in patches) for case in cases)
    return correct, len(cases)


def observe(feedback: str, cases: list[dict], patches: list[str]) -> dict:
    wrong = [case for case in cases if not (case["base_ok"] or any(patch_changes(case, p) for p in patches))]
    correct, total = score(cases, patches)
    common = {"kind": feedback, "aggregate_correct": correct, "aggregate_total": total}
    if feedback == "FULL":
        common["error_ids"] = [c["id"] for c in wrong]
        common["error_by_stratum"] = {
            str(s): sum(c["stratum"] == s for c in wrong) for s in range(4)
        }
    else:
        common["improvement_over_previous"] = None
        common["threshold_met"] = False
    return common


def choose_patch(updater: str, observation: dict, patches: list[str], round_no: int) -> str:
    available = [p for p in PATCHES if p not in patches]
    if updater == "CASE_PATCH":
        ranked = [f"case:{int(e.split('-')[1])}" for e in observation.get("error_ids", [])]
    else:
        counts = observation.get("error_by_stratum", {})
        ranked = [f"stratum:{s}" for s in sorted(range(4), key=lambda s: (-int(counts.get(str(s), 0)), s))]
    ranked.extend(PATCHES[round_no:] + PATCHES[:round_no])
    return next(p for p in ranked if p in available)


def run_cell(seed: int, feedback: str, updater: str) -> dict:
    dev, fresh, patches, trace = cohort(seed, False), cohort(seed, True), [], []
    previous = score(dev, patches)[0]
    last_feedback = observe(feedback, dev, patches)
    for round_no in range(ROUNDS):
        if round_no == 2:
            # Exact, immediate veto: this proposal is never scored or promoted.
            trace.append({"round": round_no, "proposal": "safety_regression", "safety_event": True,
                          "disclosed_exactly": True, "veto": True, "fresh_read": False})
            continue
        patch = choose_patch(updater, last_feedback, patches, round_no)
        patches.append(patch)
        new_score = score(dev, patches)[0]
        response = observe(feedback, dev, patches)
        if feedback == "CONTROLLED":
            delta = new_score - previous
            response["improvement_over_previous"] = delta
            response["threshold_met"] = delta >= 1
            response.pop("error_ids", None)
            response.pop("error_by_stratum", None)
        previous, last_feedback = new_score, response
        trace.append({"round": round_no, "proposal": patch, "feedback": response,
                      "safety_event": False, "veto": False, "fresh_read": False})
    dev_correct, dev_total = score(dev, patches)
    # The fresh cohort is first read only after the fixed candidate is locked.
    fresh_correct, fresh_total = score(fresh, patches)
    return {
        "seed": seed, "feedback": feedback, "updater": updater,
        "query_count": ROUNDS + 1, "initial_feedback": observe(feedback, dev, []),
        "patches": patches, "trace": trace,
        "candidate_locked_before_fresh": True,
        "dev_correct": dev_correct, "dev_total": dev_total,
        "fresh_correct": fresh_correct, "fresh_total": fresh_total,
        "optimism": dev_correct / dev_total - fresh_correct / fresh_total,
        "safety_veto_count": sum(int(r["veto"]) for r in trace),
        "raw_released_after_lock": True,
    }


def main(output: str) -> None:
    rows = [run_cell(seed, feedback, updater)
            for seed in SEEDS for feedback in FEEDBACKS for updater in UPDATERS]
    Path(output).write_text(json.dumps(rows, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: candidate.py OUTPUT.json")
    main(sys.argv[1])
