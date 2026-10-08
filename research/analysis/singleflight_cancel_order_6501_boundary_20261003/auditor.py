"""Independent event-prefix oracle; does not import or execute candidate code."""
import copy
import hashlib
import itertools
import json
import sys
from pathlib import Path


def audit(raw, expected_source_hash):
    errors = []
    if raw.get("schema") != "6501-cancel-order-boundary-v1" or raw.get("source_sha256") != expected_source_hash:
        errors.append("source/schema")
    rows = raw.get("rows", [])
    expected = list(itertools.product(("TRUE", "FALSE"), (None, 4, 5, 6), (None, 4, 5, 6), itertools.permutations(("cancel_a", "cancel_b", "return"))))
    if len(rows) != len(expected):
        errors.append("denominator")
    counts = {"retained_timestamp_lt": {"wrong_admit": 0, "wrong_reject": 0}, "conservative_timestamp_le": {"wrong_admit": 0, "wrong_reject": 0}, "ordered": {"wrong_admit": 0, "wrong_reject": 0}}
    for index, (row, fixture) in enumerate(zip(rows, expected)):
        truth, ca, cb, permutation = fixture
        schedule = dict(cancel_a=ca, cancel_b=cb, return_at=5)
        events = [[name, 5 if name == "return" else schedule[name], permutation.index(name)] for name in permutation if name == "return" or schedule[name] is not None]
        if {k: row.get(k) for k in ("id", "truth", "cancel_a", "cancel_b", "events")} != dict(id=index, truth=truth, cancel_a=ca, cancel_b=cb, events=events):
            errors.append(f"fixture:{index}")
            continue
        ordered_events = sorted(events, key=lambda event: (event[1], event[2]))
        return_index = next(i for i, event in enumerate(ordered_events) if event[0] == "return")
        cancelled_before = {event[0].removeprefix("cancel_") for event in ordered_events[:return_index]}
        for caller, cancel in (("a", ca), ("b", cb)):
            reference = "CANCELLED_WAITER" if caller in cancelled_before else "ADMISSIBLE_" + truth
            predicted = {
                "ordered": reference,
                "retained_timestamp_lt": "CANCELLED_WAITER" if cancel is not None and cancel < 5 else "ADMISSIBLE_" + truth,
                "conservative_timestamp_le": "CANCELLED_WAITER" if cancel is not None and cancel <= 5 else "ADMISSIBLE_" + truth,
            }
            actual = row.get("outcomes", {}).get(caller)
            if actual != predicted:
                errors.append(f"outcome:{index}:{caller}")
            for mode, verdict in predicted.items():
                if verdict != reference:
                    counts[mode]["wrong_admit" if reference == "CANCELLED_WAITER" else "wrong_reject"] += 1
    return {"errors": errors, "counts": counts, "assignments": len(rows), "waiter_decisions": len(rows) * 2}


def mutations(raw):
    # Each changes bytes and a contract-relevant field; no no-op mutations.
    for kind in ("omit", "duplicate", "truth", "clock", "order", "scope", "verdict", "source"):
        value = copy.deepcopy(raw)
        if kind == "omit": value["rows"].pop()
        elif kind == "duplicate": value["rows"][1] = copy.deepcopy(value["rows"][0])
        elif kind == "truth": value["rows"][0]["truth"] = "FALSE"
        elif kind == "clock": value["rows"][0]["events"][0][1] += 1
        elif kind == "order": value["rows"][0]["events"][0][2] += 1
        elif kind == "scope": value["rows"][0]["outcomes"]["foreign"] = value["rows"][0]["outcomes"].pop("a")
        elif kind == "verdict": value["rows"][0]["outcomes"]["a"]["ordered"] = "CANCELLED_WAITER"
        elif kind == "source": value["source_sha256"] = "0" * 64
        yield kind, value


if __name__ == "__main__":
    raw_path, hash_expected, output_path = sys.argv[1:]
    original_bytes = Path(raw_path).read_bytes()
    raw = json.loads(original_bytes)
    result = audit(raw, hash_expected)
    result["raw_sha256"] = hashlib.sha256(original_bytes).hexdigest()
    result["mutation_controls"] = []
    for name, mutant in mutations(raw):
        effective = mutant != raw
        rejected = bool(audit(mutant, hash_expected)["errors"])
        result["mutation_controls"].append(dict(name=name, effective=effective, rejected=rejected))
    expected_counts = {"retained_timestamp_lt": {"wrong_admit": 48, "wrong_reject": 0}, "conservative_timestamp_le": {"wrong_admit": 0, "wrong_reject": 48}, "ordered": {"wrong_admit": 0, "wrong_reject": 0}}
    passed = not result["errors"] and result["counts"] == expected_counts and all(x["effective"] and x["rejected"] for x in result["mutation_controls"])
    result["disposition"] = "PASS_BOUNDARY_CHARACTERIZATION_SCOPED" if passed else "FAIL_AUDIT"
    with Path(output_path).open("x", encoding="utf-8", newline="\n") as output:
        json.dump(result, output, sort_keys=True, indent=2)
        output.write("\n")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if passed else 1)
