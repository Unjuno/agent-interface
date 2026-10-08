"""Independent finite-contract audit; does not import candidate code."""
import itertools
import json
import sys
from pathlib import Path


def expected(lifetime):
    if lifetime == "FULL":
        return [[0, 0, 0], [1, 1, 1]]
    if lifetime == "ZERO":
        return [list(xs) for xs in itertools.product((0, 1), repeat=3)]
    if lifetime == "EVENT":
        # First two parameter assignments precede the event; the second is
        # fixed after that event for the last transition.
        return [[0, 0, 0], [0, 1, 1], [1, 0, 0], [1, 1, 1]]
    raise ValueError(lifetime)


def audit(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = []
    if data.get("schema") != "issue-6580-t0-candidate-v1":
        errors.append("schema")
    rows = data.get("rows", [])
    keys = [(r.get("lifetime"), r.get("order"), r.get("evidence")) for r in rows]
    wanted = list(itertools.product(("FULL", "ZERO", "EVENT"),
                                    ("NATURE_FIRST", "AGENT_FIRST"),
                                    ("VALID", "MISSING_OR_STALE")))
    if len(rows) != 12 or sorted(keys) != sorted(wanted):
        errors.append("row_denominator_or_keys")
    for i, row in enumerate(rows):
        life, order, evidence = keys[i]
        hs = expected(life) if life in ("FULL", "ZERO", "EVENT") else []
        if row.get("histories") != hs:
            errors.append(f"history_set:{i}")
        nature_info = "action+public-observation" if order == "AGENT_FIRST" else "public-observation"
        if row.get("nature_information") != nature_info:
            errors.append(f"nature_information:{i}")
        if row.get("agent_information") != "action+public-observation":
            errors.append(f"agent_information:{i}")
        if row.get("unsafe_admission") is not False:
            errors.append(f"unsafe_admission:{i}")
        if evidence == "MISSING_OR_STALE" and row.get("histories") != hs:
            errors.append(f"missing_receipt_narrowed:{i}")
    control = data.get("negative_control", [])
    if len(control) != 6 or any(c.get("effect_set") != ["SAFE"] for c in control):
        errors.append("negative_control")
    result = {"schema": "issue-6580-t0-audit-v1", "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
              "rows_expected": 12, "rows_seen": len(rows), "errors": errors,
              "histories_reconstructed": sum(len(expected(l)) for l in ("FULL", "ZERO", "EVENT"))*4,
              "negative_controls": len(control), "model_calls": 0, "effect_dispatches": 0,
              "claim": "finite semantic distinction only; no GUI/model or interface-lifetime claim"}
    return result


if __name__ == "__main__":
    result = audit(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(result, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)
