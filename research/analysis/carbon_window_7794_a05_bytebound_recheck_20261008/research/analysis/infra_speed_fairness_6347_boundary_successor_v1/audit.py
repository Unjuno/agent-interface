"""Independent raw-only boundary reconstruction. Does not import candidate."""
import copy
import json
import sys
from pathlib import Path


def _expect(case_id, ready, pointer, width, eligible_at, submitted_at, pair, round_id):
    start = min(ready.values())
    end = start + width
    offered = ["A", "B"]
    included = sorted(p for p in offered if ready[p] <= end)
    excluded = sorted(p for p in offered if ready[p] > end)
    arrival_first = min(included, key=lambda p: (ready[p], p)) if included else None
    chosen = min(included, key=lambda p: (p != pointer, p)) if included else None
    next_turn = ("B" if chosen == "A" else "A") if chosen is not None else pointer
    return {"case": case_id, "pair": pair, "round": round_id,
            "eligible_at": eligible_at, "submitted_at": submitted_at, "ready": ready,
            "first_ready": start, "window": width, "close": end,
            "offered": offered, "collected": included, "deferred": excluded,
            "frfs_winner": arrival_first, "batch_winner": chosen,
            "pointer_before": pointer, "pointer_after": next_turn,
            "status": "ADMITTED" if chosen else "HOLD_EMPTY_BATCH"}


def reconstruct(data):
    rows = []
    for case in data["paired"]:
        rows.append(_expect(case["id"], case["ready"], data["initial_pointer"],
                            data["window"], case["eligible_at"], case["submitted_at"],
                            case["pair"], None))
    current = data["initial_pointer"]
    for n, offset in enumerate(data["multi_window_ready_b"], 1):
        origin = n * 10
        eligibility = {"A": origin, "B": origin}
        submission = {"A": origin, "B": origin}
        due = {"A": origin, "B": origin + offset}
        result = _expect(f"multi-{n:02d}", due, current, data["window"],
                         eligibility, submission, "multi-window", n)
        current = result["pointer_after"]
        rows.append(result)
    return {"schema": "infra-speed-fairness-6347-boundary-raw-v1",
            "fixture_id": data["schema"], "window": data["window"], "rows": rows}


def audit(data, actual):
    expected = reconstruct(data)
    variants = []
    mutant = copy.deepcopy(expected); mutant["rows"][0]["collected"] = ["A"]; variants.append(mutant)
    mutant = copy.deepcopy(expected); mutant["rows"][1]["collected"] = ["A", "B"]; mutant["rows"][1]["deferred"] = []; variants.append(mutant)
    mutant = copy.deepcopy(expected); mutant["rows"][0]["batch_winner"] = "A"; variants.append(mutant)
    mutant = copy.deepcopy(expected); mutant["rows"][-1]["pointer_after"] = "B" if mutant["rows"][-1]["pointer_after"] == "A" else "A"; variants.append(mutant)
    return {"schema": "infra-speed-fairness-6347-boundary-audit-v1",
            "pass": actual == expected, "row_match": actual == expected,
            "reconstructed_rows": len(expected["rows"]),
            "mutation_rejections": [actual != v for v in variants],
            "all_mutations_rejected": all(actual != v for v in variants),
            "boundary_pairs": {pair: {r["case"]: {"collected": r["collected"], "deferred": r["deferred"], "winner": r["batch_winner"]}
                                      for r in expected["rows"] if r["pair"] == pair and r["round"] is None}
                               for pair in ("phase-jitter", "strategic-send")},
            "scope": "synthetic readiness boundary only"}


if __name__ == "__main__":
    fixture = json.loads(Path(sys.argv[1]).read_text())
    raw = json.loads(Path(sys.argv[2]).read_text())
    print(json.dumps(audit(fixture, raw), sort_keys=True, separators=(",", ":")))
