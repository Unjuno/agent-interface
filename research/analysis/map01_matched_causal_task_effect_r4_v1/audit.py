"""Independent post-formal audit of #3885 output and laundering controls."""
import itertools
import json
import sys
from pathlib import Path

GATES = (
    "pair_identity_match", "initial_state_match", "seed_match",
    "exogenous_schedule_match", "scorer_identity_match",
    "measurement_window_match", "deterministic_fixture_attested",
    "sole_actuation_difference", "baseline_task_input_zero",
    "candidate_ledger_valid", "clock_comparable", "candidate_effect_present",
    "baseline_same_effect_present", "candidate_effect_inside_window",
    "scorer_independent",
)


def audit_expected(row):
    """Third implementation, local to the auditor; imports neither peer."""
    if any(type(row.get(g)) is not bool for g in GATES):
        return "UNRESOLVED"
    if row.get("polarity") not in ("useful", "harmful"):
        return "UNRESOLVED"
    required = tuple(g for g in GATES if g != "baseline_same_effect_present")
    if not all(row[g] is True for g in required):
        return "UNRESOLVED"
    if row["baseline_same_effect_present"] is not False:
        return "UNRESOLVED"
    return ("CAUSAL_USEFUL_TASK_EFFECT" if row["polarity"] == "useful"
            else "CAUSAL_HARMFUL_TASK_EFFECT")


def main():
    root = Path(sys.argv[1])
    result = json.loads((root / "FORMAL_RESULT.json").read_text())
    rows = (root / "truth_table.jsonl").read_text().splitlines()
    assert result["decision"] == "FORMAL_COMPLETE"
    assert result["rows"] == 65536 and result["gate_count"] == 15
    assert result["formal_invocations"] == 1
    assert result["reruns"] == result["replacements"] == result["tuning"] == 0
    assert len(rows) == 65536
    seen = set()
    mismatch = 0
    authority = 0
    counts = {}
    for line in rows:
        row = json.loads(line)
        gates = row["gates"]
        assert all(type(gates[g]) is bool for g in GATES)
        key = tuple(gates[g] for g in GATES) + (row["polarity"],)
        assert key not in seen
        seen.add(key)
        wanted = audit_expected({**gates, "polarity": row["polarity"]})
        got = row["candidate"]["disposition"]
        mismatch += got != wanted or row["oracle"] != wanted
        authority += row["candidate"]["authority_granted"] is not False
        counts[got] = counts.get(got, 0) + 1
    assert len(seen) == 65536
    assert mismatch == result["candidate_oracle_mismatches"] == 0
    assert authority == 0
    assert result["causal_with_failed_gate"] == 0
    assert counts == result["disposition_counts"]
    assert counts == {"UNRESOLVED": 65534,
                      "CAUSAL_USEFUL_TASK_EFFECT": 1,
                      "CAUSAL_HARMFUL_TASK_EFFECT": 1}

    # Independent directed audit: perfect pairs remain polarity-distinct;
    # each individual gate corruption and additional laundering controls hold.
    good = {g: g != "baseline_same_effect_present" for g in GATES}
    controls = []
    for polarity, label in (("useful", "CAUSAL_USEFUL_TASK_EFFECT"),
                            ("harmful", "CAUSAL_HARMFUL_TASK_EFFECT")):
        row = {**good, "polarity": polarity}
        assert audit_expected(row) == label
        for gate in GATES:
            bad = dict(row)
            bad[gate] = not bad[gate]
            assert audit_expected(bad) == "UNRESOLVED", gate
            controls.append("corrupt:" + gate + ":" + polarity)
    assert audit_expected({**good, "baseline_same_effect_present": True,
                     "polarity": "useful"}) == "UNRESOLVED"
    assert audit_expected({**good, "candidate_effect_present": False,
                     "polarity": "useful"}) == "UNRESOLVED"
    assert audit_expected({**good, "candidate_effect_inside_window": False,
                     "polarity": "harmful"}) == "UNRESOLVED"
    print(json.dumps({"audit": "PASS", "rows": len(seen), "mismatch": mismatch,
                      "authority_grants": authority, "directed_corruptions": len(controls),
                      "extra_laundering_controls": 3}, sort_keys=True))


if __name__ == "__main__":
    main()
