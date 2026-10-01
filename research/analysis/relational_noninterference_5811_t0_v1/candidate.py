"""Finite relational session non-interference checker for Issue #5811."""
import json
import sys


PROJECTION_FIELDS = (
    "kind", "producer", "target", "source_session", "generation",
    "resource", "effect", "state", "input_owner", "receipt_id",
)
KNOWN = {
    "RELATION_HOLDS_SCOPED", "CONFIRMED_CROSS_SESSION_EFFECT",
    "UNKNOWN_COVERAGE", "NOT_INDEPENDENT",
}


def projected(trace, case):
    return [
        {key: row[key] for key in PROJECTION_FIELDS if key in row}
        for row in trace if row.get("target") == "A" and not (
            case.get("shared_mode") == "capacity_only" and row.get("resource") in case.get("allowed_shared", [])
        )
    ]


def scope(case, sessions):
    resources = case.get("resources", [])
    coverage = case.get("coverage", {})
    names = ("A", "B")
    for name in names:
        c = coverage.get(name, {})
        rows = [r for r in resources if r.get("session") == name]
        if len(rows) != c.get("ledger_expected"):
            return "UNKNOWN_COVERAGE"
        bound = [event for event in case["paired"]["trace"]
                 if event.get("producer") == name and event.get("resource")]
        solo_bound = [event for event in case["alone"]["trace"]
                      if event.get("producer") == name and event.get("resource")]
        solo_ok = name != "A" or len(solo_bound) == c.get("alone_expected")
        if (not c.get("complete") or len(bound) != c.get("expected") or not solo_ok or
                len(rows) != c.get("ledger_expected")):
            return "UNKNOWN_COVERAGE"
        if any(r.get("generation") != sessions[name]["generation"] or not r.get("resource") for r in rows):
            return "UNKNOWN_COVERAGE"
        if any(event.get("source_session") != name or event.get("generation") != sessions[name]["generation"] for event in bound):
            return "UNKNOWN_COVERAGE"
    a = {r["resource"] for r in resources if r["session"] == "A"}
    b = {r["resource"] for r in resources if r["session"] == "B"}
    overlap = a & b
    if any(r.get("session") not in names for r in resources):
        return "UNKNOWN_COVERAGE"
    if overlap - set(case.get("allowed_shared", [])):
        return "UNKNOWN_COVERAGE"
    if overlap:
        return "SHARED_BY_CONTRACT"
    return "INDEPENDENT_SCOPED"


def run(fixture):
    output = []
    for case in fixture["cases"]:
        dep = scope(case, fixture["sessions"])
        alone, paired = case["alone"], case["paired"]
        a_trace = [e for e in paired["trace"] if e.get("target") == "A"]
        foreign = [e for e in a_trace if e.get("producer") != "A" or
                   e.get("source_session") != "A" or
                   e.get("generation") != fixture["sessions"]["A"]["generation"]]
        single_pass = all(x["state"] == "DONE" and x["task"] == "saved" and x["release"] == "EMPTY"
                          for x in (alone, paired))
        same_final = (alone["state"], alone["task"], alone["release"]) == (paired["state"], paired["task"], paired["release"])
        projection_equal = projected(alone["trace"], case) == projected(paired["trace"], case)
        has_effect = any(e.get("kind") == "EFFECT" for e in a_trace)
        if dep == "UNKNOWN_COVERAGE":
            outcome = "UNKNOWN_COVERAGE"
        elif dep == "SHARED_BY_CONTRACT":
            outcome = "NOT_INDEPENDENT"
        elif foreign:
            outcome = "CONFIRMED_CROSS_SESSION_EFFECT"
        elif not has_effect:
            outcome = "UNKNOWN_COVERAGE"
        elif projection_equal:
            outcome = "RELATION_HOLDS_SCOPED"
        else:
            outcome = "CONFIRMED_CROSS_SESSION_EFFECT"
        assert outcome in KNOWN
        output.append({"id": case["id"], "dependency_class": dep,
                       "single_run_pass": single_pass, "final_state_equal": same_final,
                       "projection_equal": projection_equal, "foreign_event_count": len(foreign),
                       "outcome": outcome})
    return {"schema": "5811-relational-session-result-v1", "cases": output}


if __name__ == "__main__":
    print(json.dumps(run(json.load(sys.stdin)), sort_keys=True, separators=(",", ":")))
