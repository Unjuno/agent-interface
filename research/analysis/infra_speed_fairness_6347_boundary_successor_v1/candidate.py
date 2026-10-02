"""Boundary-instrumented finite scheduler study for Issue #6347."""
import json
import sys
from pathlib import Path


def decide(case_id, ready, pointer, window, eligible_at, submitted_at, pair=None, round_id=None):
    first_ready = min(ready.values())
    close = first_ready + window
    offered = ["A", "B"]
    collected = sorted([p for p in offered if ready[p] <= close])
    deferred = sorted([p for p in offered if ready[p] > close])
    frfs = min(collected, key=lambda p: (ready[p], p)) if collected else None
    batch_winner = min(collected, key=lambda p: (p != pointer, p)) if collected else None
    after = ("B" if batch_winner == "A" else "A") if batch_winner else pointer
    return {
        "case": case_id, "pair": pair, "round": round_id,
        "eligible_at": eligible_at, "submitted_at": submitted_at, "ready": ready,
        "first_ready": first_ready, "window": window, "close": close,
        "offered": offered, "collected": collected, "deferred": deferred,
        "frfs_winner": frfs, "batch_winner": batch_winner,
        "pointer_before": pointer, "pointer_after": after,
        "status": "ADMITTED" if batch_winner else "HOLD_EMPTY_BATCH",
    }


def run(fixture):
    output = []
    for item in fixture["paired"]:
        output.append(decide(item["id"], item["ready"], fixture["initial_pointer"],
                             fixture["window"], item["eligible_at"],
                             item["submitted_at"], pair=item["pair"]))
    pointer = fixture["initial_pointer"]
    for index, ready_b in enumerate(fixture["multi_window_ready_b"], 1):
        eligible = {"A": index * 10, "B": index * 10}
        submitted = {"A": index * 10, "B": index * 10}
        ready = {"A": index * 10, "B": index * 10 + ready_b}
        row = decide(f"multi-{index:02d}", ready, pointer, fixture["window"],
                     eligible, submitted, pair="multi-window", round_id=index)
        # Store local window times as offsets; the full absolute times remain recorded above.
        row["first_ready"] = index * 10
        row["close"] = index * 10 + fixture["window"]
        pointer = row["pointer_after"]
        output.append(row)
    return {"schema": "infra-speed-fairness-6347-boundary-raw-v1",
            "fixture_id": fixture["schema"], "window": fixture["window"],
            "rows": output}


if __name__ == "__main__":
    print(json.dumps(run(json.loads(Path(sys.argv[1]).read_text())), sort_keys=True, separators=(",", ":")))
