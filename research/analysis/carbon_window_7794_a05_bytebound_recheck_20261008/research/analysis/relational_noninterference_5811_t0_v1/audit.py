"""Independent reconstruction audit; intentionally does not import candidate."""
import json
import sys


FIELDS = ("kind", "producer", "target", "source_session", "generation", "resource", "effect", "state", "input_owner", "receipt_id")
EXPECTED = {
    "clean_disjoint": ("INDEPENDENT_SCOPED", "RELATION_HOLDS_SCOPED"),
    "shared_verifier_capacity": ("SHARED_BY_CONTRACT", "NOT_INDEPENDENT"),
    "misbound_observation": ("UNKNOWN_COVERAGE", "UNKNOWN_COVERAGE"),
    "hidden_global_focus": ("UNKNOWN_COVERAGE", "UNKNOWN_COVERAGE"),
    "delayed_receipt_to_A": ("INDEPENDENT_SCOPED", "CONFIRMED_CROSS_SESSION_EFFECT"),
    "B_cleanup_releases_A_input": ("INDEPENDENT_SCOPED", "CONFIRMED_CROSS_SESSION_EFFECT"),
    "shared_document": ("UNKNOWN_COVERAGE", "UNKNOWN_COVERAGE"),
    "truncated_dependency_trace": ("UNKNOWN_COVERAGE", "UNKNOWN_COVERAGE"),
    "stale_source_generation": ("UNKNOWN_COVERAGE", "UNKNOWN_COVERAGE"),
    "missing_effect_evidence": ("INDEPENDENT_SCOPED", "UNKNOWN_COVERAGE"),
}


def independent_projection(rows, case):
    return [{k: event[k] for k in FIELDS if k in event}
            for event in rows if event.get("target") == "A" and not (
                case.get("shared_mode") == "capacity_only" and event.get("resource") in case.get("allowed_shared", [])
            )]


def classify_resources(case, generations):
    found = {s: [] for s in ("A", "B")}
    for row in case["resources"]:
        s = row.get("session")
        if s not in found:
            return "UNKNOWN_COVERAGE"
        found[s].append(row)
    for s, rows in found.items():
        cov = case["coverage"].get(s, {})
        bound = [event for event in case["paired"]["trace"]
                 if event.get("producer") == s and event.get("resource")]
        solo = [event for event in case["alone"]["trace"]
                if event.get("producer") == s and event.get("resource")]
        solo_ok = s != "A" or len(solo) == cov.get("alone_expected")
        if (cov.get("complete") is not True or len(bound) != cov.get("expected") or
                not solo_ok or len(rows) != cov.get("ledger_expected")):
            return "UNKNOWN_COVERAGE"
        if any(x.get("session") != s or x.get("generation") != generations[s]["generation"] or not x.get("resource") for x in rows):
            return "UNKNOWN_COVERAGE"
        if any(event.get("source_session") != s or event.get("generation") != generations[s]["generation"]
               for event in bound):
            return "UNKNOWN_COVERAGE"
    footprints = [{r["resource"] for r in found[s]} for s in ("A", "B")]
    shared = footprints[0].intersection(footprints[1])
    if not shared.issubset(set(case.get("allowed_shared", []))):
        return "UNKNOWN_COVERAGE"
    return "SHARED_BY_CONTRACT" if shared else "INDEPENDENT_SCOPED"


def reconstruct(fixture):
    rows = []
    for case in fixture["cases"]:
        dep = classify_resources(case, fixture["sessions"])
        a = case["alone"]["trace"]
        p = case["paired"]["trace"]
        own = [x for x in p if x.get("target") == "A"]
        foreign = [x for x in own if (x.get("producer") != "A" or x.get("source_session") != "A" or
                                      x.get("generation") != fixture["sessions"]["A"]["generation"])]
        effect = any(x.get("kind") == "EFFECT" for x in own)
        if dep == "UNKNOWN_COVERAGE":
            outcome = "UNKNOWN_COVERAGE"
        elif dep == "SHARED_BY_CONTRACT":
            outcome = "NOT_INDEPENDENT"
        elif foreign:
            outcome = "CONFIRMED_CROSS_SESSION_EFFECT"
        elif not effect:
            outcome = "UNKNOWN_COVERAGE"
        elif independent_projection(a, case) == independent_projection(p, case):
            outcome = "RELATION_HOLDS_SCOPED"
        else:
            outcome = "CONFIRMED_CROSS_SESSION_EFFECT"
        states = [case[k] for k in ("alone", "paired")]
        rows.append({"id": case["id"], "dependency_class": dep,
                     "single_run_pass": all(s["state"] == "DONE" and s["task"] == "saved" and s["release"] == "EMPTY" for s in states),
                     "final_state_equal": (states[0]["state"], states[0]["task"], states[0]["release"]) == (states[1]["state"], states[1]["task"], states[1]["release"]),
                     "projection_equal": independent_projection(a, case) == independent_projection(p, case),
                     "foreign_event_count": len(foreign), "outcome": outcome})
    return {"schema": "5811-relational-session-result-v1", "cases": rows}


def audit(fixture, actual):
    expected = reconstruct(fixture)
    assert actual == expected, "candidate output differs from independent reconstruction"
    assert len(expected["cases"]) == len(EXPECTED) == 10
    assert {x["id"] for x in expected["cases"]} == set(EXPECTED)
    for row in expected["cases"]:
        dep, outcome = EXPECTED[row["id"]]
        assert (row["dependency_class"], row["outcome"]) == (dep, outcome), row["id"]
    bad = {"delayed_receipt_to_A", "B_cleanup_releases_A_input"}
    for row in expected["cases"]:
        if row["id"] in bad:
            assert row["single_run_pass"] and row["final_state_equal"]
            assert row["outcome"] == "CONFIRMED_CROSS_SESSION_EFFECT"
    misbound = next(x for x in expected["cases"] if x["id"] == "misbound_observation")
    assert misbound["dependency_class"] == "UNKNOWN_COVERAGE"
    assert misbound["outcome"] == "UNKNOWN_COVERAGE"
    capacity = next(x for x in expected["cases"] if x["id"] == "shared_verifier_capacity")
    assert capacity["projection_equal"] and capacity["outcome"] == "NOT_INDEPENDENT"
    return {"status": "PASS_METHOD_SCOPED", "reconstructed_cases": 10,
            "missed_by_single_run_and_final_state": sorted(bad),
            "mutation_controls": 5, "scope": "synthetic finite fixture only"}


if __name__ == "__main__":
    fixture = json.load(open(sys.argv[1], encoding="utf-8"))
    actual = json.load(sys.stdin)
    print(json.dumps(audit(fixture, actual), sort_keys=True, separators=(",", ":")))
