"""Independent enumerator and safety auditor; deliberately does not import candidate."""
import itertools
import json
import sys
from pathlib import Path

LIFETIMES = ("FULL", "ZERO", "EVENT")
PHASES = ("PRE_EVENT", "POST_EVENT")
EVIDENCE = ("VALID_0", "VALID_1", "MISSING", "STALE")
ORDERS = ("NATURE_FIRST_PUBLIC", "AGENT_FIRST_REACTIVE")


def expected_support(life, phase, evidence):
    if life == "FULL" and evidence == "VALID_0": return [0]
    if life == "FULL" and evidence == "VALID_1": return [1]
    if life == "EVENT" and phase == "POST_EVENT" and evidence == "VALID_0": return [0]
    if life == "EVENT" and phase == "POST_EVENT" and evidence == "VALID_1": return [1]
    return [0, 1]


def action(theta): return "A" if theta == 0 else "B"


def expected_row(life, phase, evidence, order):
    support = expected_support(life, phase, evidence)
    if order == "NATURE_FIRST_PUBLIC":
        actual = support[0]
        decision, chosen, reachable = "CONTINUE", action(actual), [actual]
    elif len(support) == 1:
        actual = support[0]
        decision, chosen, reachable = "CONTINUE", action(actual), [actual]
    else:
        decision, chosen, reachable = "YIELD", None, []
    point = int(evidence[-1]) if evidence in ("VALID_0", "VALID_1") else 0
    return {"prior_support": support, "decision": decision, "action": chosen,
            "reachable_theta": reachable, "unsafe_dispatch": False,
            "unspecified_decision": "CONTINUE" if order == "NATURE_FIRST_PUBLIC" else "YIELD",
            "point_action": action(point),
            "point_unsafe_possible": any(point != value for value in support)}


def audit(path):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = []
    if obj.get("schema") != "issue-6580-t0b-candidate-v1": errors.append("schema")
    rows = obj.get("rows", [])
    keys = [(r.get("lifetime"), r.get("phase"), r.get("evidence"), r.get("order")) for r in rows]
    wanted = list(itertools.product(LIFETIMES, PHASES, EVIDENCE, ORDERS))
    if len(rows) != 48 or sorted(keys) != sorted(wanted): errors.append("denominator_or_keys")
    for idx, row in enumerate(rows):
        key = keys[idx]
        exp = expected_row(*key)
        for field, value in exp.items():
            if row.get(field) != value: errors.append(f"{field}:{idx}")
        if row.get("decision") == "CONTINUE":
            reached = row.get("reachable_theta", [])
            if not reached or any(row.get("action") != action(theta) for theta in reached):
                errors.append(f"unsafe_prefix:{idx}")
        if row.get("unsafe_dispatch") is not False: errors.append(f"dispatch:{idx}")
    controls = obj.get("negative_controls", [])
    if len(controls) != 6: errors.append("control_denominator")
    for control in controls:
        if control.get("decision") != "CONTINUE" or control.get("unsafe_dispatch") is not False:
            errors.append("negative_control")
    # The decision-level discriminators were frozen as required witnesses.
    explicit_gain = sum(r.get("decision") == "CONTINUE" and r.get("unspecified_decision") == "YIELD" for r in rows)
    point_risk = sum(r.get("point_unsafe_possible") is True for r in rows)
    if explicit_gain == 0: errors.append("no_explicit_vs_unspecified_discriminator")
    if point_risk == 0: errors.append("no_point_comparator_risk")
    return {"schema":"issue-6580-t0b-audit-v1", "status":"PASS_METHOD_SCOPED" if not errors else "FAIL_METHOD",
            "rows_expected":48,"rows_seen":len(rows),"negative_controls_expected":6,
            "negative_controls_seen":len(controls),"errors":errors,
            "explicit_safe_continuation_over_unspecified":explicit_gain,
            "point_comparator_unsafe_possible_rows":point_risk,
            "unsafe_gate_dispatches":sum(r.get("unsafe_dispatch") is not False for r in rows),
            "model_calls":0,"external_effects":0}


if __name__ == "__main__":
    result = audit(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(result, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)
