"""Finite claim-ladder candidate for Issue #6509 T0."""
import json
import sys
from pathlib import Path


MANDATORY = ("identity", "freshness", "effect")
POLICIES = ("ALL_OR_NOTHING_TIMEOUT", "UNSAFE_SCALAR_PROGRESS", "CLAIM_LADDER")


def trusted_events(trace, generation):
    result = []
    for event in trace["events"]:
        check, value, event_generation, source_bound, committed = event
        if source_bound and committed and event_generation == generation:
            result.append((check, value, event_generation))
    return result


def run_policy(trace, policy, contract):
    gen = contract["generation"]
    events = trusted_events(trace, gen)
    values = {}
    for check, value, event_gen in events:
        values.setdefault(check, []).append((value, event_gen))
    complete = all(check in values and values[check][-1][0] in ("PASS", "VIOLATION")
                   for check in MANDATORY)
    final_gen = trace.get("final_generation", gen)
    contradictory = any(len(items) > 1 and len({v for v, _ in items}) > 1
                        for items in values.values())
    decisive_negative = ("effect" in values
                         and values["effect"][-1][0] == "VIOLATION"
                         and len({v for v, _ in values["effect"]}) == 1)
    if policy == "UNSAFE_SCALAR_PROGRESS":
        disposition = "ALLOW" if trace.get("scalar_progress", 0.0) >= 0.5 else "UNKNOWN"
        return {"disposition": disposition, "completed": [e[0] for e in events],
                "missing": [c for c in MANDATORY if c not in values],
                "authority": disposition == "ALLOW"}
    if policy == "ALL_OR_NOTHING_TIMEOUT":
        if decisive_negative and final_gen == gen and not contradictory:
            disposition = "COUNTEREXAMPLE"
        elif complete and final_gen == gen and not contradictory and all(
                values[c][-1][0] == "PASS" for c in MANDATORY):
            disposition = "COMPLETE_ALLOW"
        else:
            disposition = "TIMEOUT_UNKNOWN"
        return {"disposition": disposition, "completed": [], "missing": list(MANDATORY),
                "authority": disposition in ("COUNTEREXAMPLE", "COMPLETE_ALLOW")}
    # Claim ladder: a decisive negative may reject early; positive claims require all gates.
    if decisive_negative and final_gen == gen and not contradictory:
        disposition = "COUNTEREXAMPLE"
    elif complete and final_gen == gen and not contradictory and all(
            values[c][-1][0] == "PASS" for c in MANDATORY):
        disposition = "COMPLETE_ALLOW"
    else:
        disposition = "PARTIAL_UNKNOWN"
    return {"disposition": disposition,
            "completed": sorted({e[0] for e in events}),
            "missing": [c for c in MANDATORY if c not in values],
            "authority": disposition in ("COUNTEREXAMPLE", "COMPLETE_ALLOW")}


def build_raw(fixture):
    rows = []
    for trace in fixture["traces"]:
        for policy in POLICIES:
            rows.append({"trace_id": trace["id"], "policy": policy,
                         "input": trace,
                         "result": run_policy(trace, policy, fixture)})
    return {"schema": "claim-ladder-raw-v1", "generation": fixture["generation"],
            "source": fixture["source"], "target": fixture["target"],
            "mandatory": list(MANDATORY), "policies": list(POLICIES), "rows": rows}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate.py FIXTURE_JSON OUTPUT_JSON")
    fixture = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    Path(sys.argv[2]).write_text(json.dumps(build_raw(fixture), sort_keys=True, indent=2) + "\n",
                                 encoding="utf-8")
