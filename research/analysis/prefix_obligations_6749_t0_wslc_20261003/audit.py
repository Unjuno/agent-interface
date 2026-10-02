"""Independent raw-only contract reconstruction for successor #6749."""
import copy
import itertools
import json
import sys
from collections import Counter
from pathlib import Path

CHECK_RESULTS = ("PASS", "FAIL")
GENERATION_RESULTS = ("CURRENT", "INVALID")
OPTIONAL_TAIL = {"COMPLETE": "optional_complete", "CONFLICT": "optional_conflict",
                 "TIMEOUT": "optional_timeout"}


def contract_worlds():
    for a, b, g, optional in itertools.product(
        CHECK_RESULTS, CHECK_RESULTS, GENERATION_RESULTS, OPTIONAL_TAIL
    ):
        yield ("check_a_" + a.lower(), "check_b_" + b.lower(),
               "generation_" + g.lower(), "optional_clear", OPTIONAL_TAIL[optional])


def legal_orders(events):
    optional = events[3:]
    for candidate in itertools.permutations(events):
        if tuple(token for token in candidate if token.startswith("optional_")) == optional:
            yield candidate


def reconstruct_state(prefix):
    out = {"check_a": None, "check_b": None, "generation": None, "optional": "OPEN"}
    for token in prefix:
        if token in ("check_a_pass", "check_a_fail"):
            out["check_a"] = token[8:].upper()
        elif token in ("check_b_pass", "check_b_fail"):
            out["check_b"] = token[8:].upper()
        elif token in ("generation_current", "generation_invalid"):
            out["generation"] = token[11:].upper()
        elif token == "optional_clear":
            out["optional"] = "CLEARED"
        elif token in ("optional_complete", "optional_conflict", "optional_timeout"):
            out["optional"] = token[9:].upper()
        else:
            raise ValueError("unknown event")
    return out


def independent_label(s):
    if s["generation"] == "INVALID":
        return "INVALID"
    if s["generation"] == "CURRENT" and (s["check_a"] == "FAIL" or s["check_b"] == "FAIL"):
        return "STABLE_FAIL"
    if all(s[key] == "PASS" for key in ("check_a", "check_b")) and s["generation"] == "CURRENT" and s["optional"] == "COMPLETE":
        return "PASS"
    return "PROVISIONAL"


def independent_pending(s):
    outstanding = []
    if s["check_a"] is None:
        outstanding.append("check_a")
    if s["check_b"] is None:
        outstanding.append("check_b")
    if s["generation"] is None:
        outstanding.append("source_frontier:generation")
    if s["optional"] not in ("COMPLETE", "CONFLICT", "TIMEOUT"):
        outstanding.append("source_frontier:optional")
    return outstanding


def reference_rows():
    result = []
    for index, events in enumerate(contract_worlds()):
        for order in legal_orders(events):
            for stop in range(len(order) + 1):
                prefix = list(order[:stop])
                state = reconstruct_state(prefix)
                result.append({"world_id": f"w{index:02d}", "prefix": prefix,
                               "state": state, "disposition": independent_label(state),
                               "pending_obligations": independent_pending(state)})
    return result


def validate(raw):
    if not isinstance(raw, dict) or raw.get("schema") != "prefix-obligations-6749-raw-v1":
        return False
    expected = reference_rows()
    rows = raw.get("rows")
    if not isinstance(rows, list) or rows != expected:
        return False
    actual_counts = Counter(row["disposition"] for row in rows)
    actual_early = Counter()
    for row in rows:
        if row["disposition"] in ("STABLE_FAIL", "PASS"):
            actual_early[row["disposition"].lower() + "_prefixes"] += 1
    return (raw.get("disposition_counts") == dict(sorted(actual_counts.items()))
            and raw.get("early_finalization_metrics") == dict(sorted(actual_early.items())))


def mutation_cases(raw):
    cases = {}
    def target(predicate):
        return next(i for i, row in enumerate(raw["rows"]) if predicate(row))

    changed = copy.deepcopy(raw)
    i = target(lambda r: r["disposition"] == "STABLE_FAIL" and r["state"]["check_a"] is None)
    changed["rows"][i]["pending_obligations"].remove("check_a")
    cases["drop_pending_mandatory"] = changed

    changed = copy.deepcopy(raw)
    key, value = next(iter(changed["early_finalization_metrics"].items()))
    changed["disposition_counts"][key] = value
    cases["mix_metric_into_disposition_counts"] = changed

    changed = copy.deepcopy(raw)
    i = target(lambda r: r["state"]["optional"] == "CLEARED")
    changed["rows"][i]["state"]["optional"] = "COMPLETE"
    cases["forge_optional_completion"] = changed

    changed = copy.deepcopy(raw)
    i = target(lambda r: r["state"]["generation"] == "INVALID")
    changed["rows"][i]["state"]["generation"] = "CURRENT"
    cases["relabel_invalid_as_current"] = changed

    changed = copy.deepcopy(raw)
    i = target(lambda r: r["state"]["optional"] == "TIMEOUT")
    changed["rows"][i]["state"]["optional"] = "COMPLETE"
    cases["treat_timeout_as_complete"] = changed
    return cases


def audit(raw):
    if not validate(raw):
        return {"status": "FAIL_METHOD", "errors": ["independent_reconstruction_mismatch"]}
    controls = {label: not validate(mutated) for label, mutated in mutation_cases(raw).items()}
    if not all(controls.values()):
        return {"status": "FAIL_METHOD", "errors": ["mutation_survived"],
                "mutation_controls_rejected": controls}
    counts = Counter(row["disposition"] for row in raw["rows"])
    return {"status": "PASS_METHOD_SCOPED", "errors": [], "prefix_rows": len(raw["rows"]),
            "disposition_counts": dict(sorted(counts.items())),
            "mutation_controls_rejected": controls,
            "authority_or_external_effects": 0}


def main():
    source, destination = map(Path, sys.argv[1:3])
    if destination.exists():
        raise SystemExit("refusing to overwrite audit output")
    result = audit(json.loads(source.read_text(encoding="utf-8")))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__":
    main()
