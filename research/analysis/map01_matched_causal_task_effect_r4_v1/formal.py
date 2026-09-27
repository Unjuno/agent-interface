"""Single exhaustive 65,536-row allocation for Issue #3885."""
import itertools
import json
import sys
from pathlib import Path

from candidate import GATES, classify
from oracle import expected


def main():
    out = Path(sys.argv[1])
    if out.exists():
        if any(out.iterdir()):
            raise FileExistsError("formal output directory must be empty")
    else:
        out.mkdir(parents=True, exist_ok=False)
    rows_path = out / "truth_table.jsonl"
    counts = {}
    mismatches = 0
    causal_with_failed_gate = 0
    with rows_path.open("x", encoding="utf-8") as stream:
        for bits in itertools.product((False, True), repeat=len(GATES)):
            gates = dict(zip(GATES, bits))
            for polarity in ("useful", "harmful"):
                row = {**gates, "polarity": polarity}
                result = classify(row)
                oracle_label = expected(row)
                label = result["disposition"]
                mismatches += label != oracle_label
                valid = all(row[g] for g in GATES if g != "baseline_same_effect_present")
                valid = valid and not row["baseline_same_effect_present"]
                causal_with_failed_gate += label != "UNRESOLVED" and not valid
                counts[label] = counts.get(label, 0) + 1
                stream.write(json.dumps({"gates": gates, "polarity": polarity,
                                         "candidate": result,
                                         "oracle": oracle_label},
                                        sort_keys=True, separators=(",", ":")) + "\n")
    result = {
        "decision": "FORMAL_COMPLETE",
        "rows": 2 * (2 ** len(GATES)),
        "gate_count": len(GATES),
        "candidate_oracle_mismatches": mismatches,
        "causal_with_failed_gate": causal_with_failed_gate,
        "disposition_counts": counts,
        "formal_invocations": 1,
        "reruns": 0,
        "replacements": 0,
        "tuning": 0,
        "truth_table": rows_path.name,
    }
    (out / "FORMAL_RESULT.json").write_text(
        json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
