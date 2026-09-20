"""Construction-only assertions; no truth-table formal rows are allocated."""
from candidate import GATES, classify


def complete(polarity="useful"):
    return {**{key: key != "baseline_same_effect_present" for key in GATES},
            "polarity": polarity}


def main():
    assert len(GATES) == 15 and len(set(GATES)) == 15
    for polarity, expected in (("useful", "CAUSAL_USEFUL_TASK_EFFECT"),
                               ("harmful", "CAUSAL_HARMFUL_TASK_EFFECT")):
        row = complete(polarity)
        got = classify(row)
        assert got == {"disposition": expected, "authority_granted": False}
        for gate in GATES:
            bad = dict(row)
            bad[gate] = not bad[gate]
            assert classify(bad)["disposition"] == "UNRESOLVED", gate
    print("CONSTRUCTION_PASS gates=15 polarities=2 corruptions=30 formal_rows=0")


if __name__ == "__main__":
    main()
