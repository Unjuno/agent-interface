"""One deterministic mutation-adequacy candidate invocation; no external I/O."""
import hashlib
import itertools
import json
import platform
import sys
from pathlib import Path

from candidate import FIELDS, MUTANTS, decide, mutated_decide

HERE = Path(__file__).resolve().parent
KEYS = (*FIELDS, "terminal_failure")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scores(state):
    return {
        "candidate": decide(state),
        **{name: mutated_decide(state, name) for name in MUTANTS},
    }


def main(output):
    nominal = dict(evidence_present=True, evidence_fresh=True,
                   authority_matches=True, outcome_known=True,
                   terminal_failure=False)
    baseline_states = [
        ("nominal_commit", nominal),
        ("missing_provenance", {**nominal, "evidence_present": False}),
        ("unknown_outcome", {**nominal, "outcome_known": False}),
    ]
    baseline = [
        {"case": name, "state": state, "expected_commit": name == "nominal_commit",
         "decisions": scores(state)}
        for name, state in baseline_states
    ]

    downgrade_fields = ("evidence_fresh", "authority_matches", "terminal_failure")
    metamorphic = []
    for field in downgrade_fields:
        degraded = {**nominal, field: not nominal[field]}
        metamorphic.append({
            "relation": f"degrade_{field}_must_not_commit",
            "base_state": nominal,
            "degraded_state": degraded,
            "base_decisions": scores(nominal),
            "degraded_decisions": scores(degraded),
        })

    exhaustive = []
    for values in itertools.product((False, True), repeat=len(KEYS)):
        state = dict(zip(KEYS, values))
        exhaustive.append({"state": state, "decisions": scores(state)})

    raw = {
        "schema": "issue5541-mutation-adequacy-t0-v1",
        "python": sys.version,
        "platform": platform.platform(),
        "source_sha256": {
            "candidate.py": sha256(HERE / "candidate.py"),
            "run.py": sha256(HERE / "run.py"),
        },
        "field_order": list(KEYS),
        "mutants": list(MUTANTS),
        "baseline": baseline,
        "metamorphic": metamorphic,
        "exhaustive": exhaustive,
    }
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python run.py OUTPUT.json")
    main(sys.argv[1])
