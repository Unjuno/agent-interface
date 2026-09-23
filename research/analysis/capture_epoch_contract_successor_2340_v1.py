import json
from dataclasses import dataclass
from hashlib import sha256

@dataclass(frozen=True)
class Obs:
    epoch: str | None
    seq: int | None
    scope: str
    role: str
    current_epoch: str
    current_seq: int

def classify(o: Obs) -> str:
    if o.epoch is None or o.seq is None or o.scope == "":
        return "ABSTAIN"
    if o.epoch != o.current_epoch:
        return "HISTORICAL_CONTEXT"
    if o.seq < o.current_seq:
        return "HISTORICAL_CONTEXT"
    if o.seq > o.current_seq:
        return "REOBSERVE"
    if o.role != "CURRENT_PLANNER_CONTEXT":
        return "HISTORICAL_CONTEXT"
    return "CURRENT_CONTEXT"

CASES = [
    ("fresh", Obs("e2", 4, "surface-A", "CURRENT_PLANNER_CONTEXT", "e2", 4), "CURRENT_CONTEXT"),
    ("late-old-epoch", Obs("e1", 4, "surface-A", "CURRENT_PLANNER_CONTEXT", "e2", 4), "HISTORICAL_CONTEXT"),
    ("late-old-seq", Obs("e2", 3, "surface-A", "CURRENT_PLANNER_CONTEXT", "e2", 4), "HISTORICAL_CONTEXT"),
    ("future-seq", Obs("e2", 5, "surface-A", "CURRENT_PLANNER_CONTEXT", "e2", 4), "REOBSERVE"),
    ("wrong-role", Obs("e2", 4, "surface-A", "HISTORICAL_CONTEXT", "e2", 4), "HISTORICAL_CONTEXT"),
    ("dropped-epoch", Obs(None, 4, "surface-A", "CURRENT_PLANNER_CONTEXT", "e2", 4), "ABSTAIN"),
    ("corrupt-seq", Obs("e2", None, "surface-A", "CURRENT_PLANNER_CONTEXT", "e2", 4), "ABSTAIN"),
    ("scope-lost", Obs("e2", 4, "", "CURRENT_PLANNER_CONTEXT", "e2", 4), "ABSTAIN"),
]

def main():
    for name, obs, expected in CASES:
        got = classify(obs)
        assert got == expected, (name, got, expected)
    # JSON round-trip is the only transport exercised here; missing fields fail closed.
    payload = json.dumps(CASES[0][1].__dict__, sort_keys=True)
    decoded = json.loads(payload)
    assert classify(Obs(**decoded)) == "CURRENT_CONTEXT"
    print("PASS_CAPTURE_EPOCH_CONTRACT cases=8 current=1 historical=3 reobserve=1 abstain=3")

if __name__ == "__main__":
    main()
