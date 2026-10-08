"""Exhaustive prefix-certificate candidate for Issue #6689 T0."""
import json
import sys
from functools import lru_cache
from pathlib import Path

from fixture import FIELDS, classify, reachable, successors, terminal


@lru_cache(None)
def completion_outcomes(s):
    found = {terminal(s)}  # cutoff is legal at every reachable prefix
    for _, nxt in successors(s):
        found.update(completion_outcomes(nxt))
    return tuple(sorted(found))


def build_raw():
    states = reachable()
    rows = []
    for s, prefix in sorted(states.items()):
        outcomes = completion_outcomes(s)
        pending = []
        if not s[3] and not s[4]:
            pending.append("mandatory_check_vector")
        if not s[7]:
            pending.append("source_a_completion")
        if not s[8]:
            pending.append("source_b_completion")
        rows.append({"state": dict(zip(FIELDS, s)), "representative_prefix": list(prefix),
                     "terminal_outcomes": list(outcomes), "classification": classify(s, outcomes),
                     "pending_obligations": pending})
    # An unknown completion contract is outside the enumerable language and must fail closed.
    rows.append({"state": {"contract_known": False}, "representative_prefix": [],
                 "terminal_outcomes": ["UNKNOWN"], "classification": "UNKNOWN",
                 "pending_obligations": ["continuation_contract"]})
    return {"schema": "prefix-stability-6689-raw-v1", "rows": rows}


def main():
    out = Path(sys.argv[1])
    if out.exists():
        raise SystemExit("refusing to overwrite candidate raw")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_raw(), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(build_raw()["rows"]), "output": str(out)}))


if __name__ == "__main__":
    main()
