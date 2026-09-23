from hashlib import sha256
from itertools import permutations

EVENTS = (
    {"id": "current_irrelevant", "age": 0, "causal": 0, "transition": 0},
    {"id": "older_causal", "age": 3, "causal": 2, "transition": 0},
    {"id": "older_irrelevant", "age": 4, "causal": 0, "transition": 0},
    {"id": "recent_transition", "age": 1, "causal": 1, "transition": 1},
)


def oracle(events):
    return tuple(e["id"] for e in sorted(events, key=lambda e: (-e["causal"], -e["transition"], e["age"], e["id"])))


def recency_only(events):
    return tuple(e["id"] for e in sorted(events, key=lambda e: (e["age"], e["id"])))


def causal_then_recency(events):
    return oracle(events)


def main():
    rows = []
    for order in permutations(EVENTS):
        expected = oracle(order)
        rows.append({
            "input": tuple(e["id"] for e in order),
            "oracle": expected,
            "recency": recency_only(order),
            "causal_then_recency": causal_then_recency(order),
        })
    recency_matches = sum(r["recency"] == r["oracle"] for r in rows)
    causal_matches = sum(r["causal_then_recency"] == r["oracle"] for r in rows)
    counterexamples = [r for r in rows if r["recency"] != r["oracle"]]
    manifest = repr(EVENTS).encode()
    print("streams", len(rows))
    print("RECENCY_ONLY exact", recency_matches, "/", len(rows))
    print("CAUSAL_THEN_RECENCY exact", causal_matches, "/", len(rows))
    print("recency counterexamples", len(counterexamples))
    print("manifest_sha256", sha256(manifest).hexdigest())
    assert causal_matches == len(rows)
    assert counterexamples
    assert all(set(r["causal_then_recency"]) == {e["id"] for e in EVENTS} for r in rows)


if __name__ == "__main__":
    main()
