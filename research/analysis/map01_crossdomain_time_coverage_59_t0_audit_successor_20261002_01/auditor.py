import collections
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def jsonl(text):
    return [json.loads(line) for line in text.splitlines() if line.strip()]

def ait_rows(text):
    rows = []
    for line in text.splitlines():
        marker = line.find("AIT {")
        if marker >= 0:
            row = json.loads(line[marker + 4:])
            if isinstance(row, dict) and isinstance(row.get("tiles"), list):
                rows.append(row)
    return rows

def observer_summary(rows):
    states = [tuple((t.get("id"), t.get("road"), t.get("owner"))
                    for t in r["tiles"]) for r in rows]
    transitions = [i for i in range(1, len(states)) if states[i] != states[i-1]]
    fields = sorted({k for r in rows for k in r if k.endswith("_ns")
                     or "clock" in k or "sequence" in k
                     or k in {"actuation_id", "action_id"}})
    return {"raw_total_records": len(rows), "unique_states": len(set(states)),
            "transition_indices": transitions, "transition_witness_records": len(transitions),
            "top_level_clock_or_action_fields": fields}

def event_counts(rows):
    return dict(sorted(collections.Counter(r.get("event") for r in rows).items()))

def counts_match_report(candidate, raw_counts):
    by_domain = {d.get("domain"): d for d in candidate.get("domains", [])}
    return all(by_domain.get(name, {}).get("event_counts") == counts
               for name, counts in raw_counts.items())

def observer_report_matches(candidate_domain, summary):
    return (candidate_domain.get("observer_records") == summary["transition_witness_records"]
            and candidate_domain.get("observer_record_count") == summary["raw_total_records"]
            and candidate_domain.get("observer_transition_indices") == summary["transition_indices"])

def raw_audit(freeze, candidate, contents):
    errors = []
    for name, spec in freeze["inputs"].items():
        data = contents[name].encode("utf-8")
        sha = hashlib.sha256(data).hexdigest()
        git_blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if sha != spec["sha256"] or git_blob != spec["git_blob_sha"]:
            errors.append("source hash mismatch: " + name)
    if candidate.get("status") != "HOLD_CROSSDOMAIN_TIME_COVERAGE_UNIDENTIFIED":
        errors.append("candidate HOLD missing")
    if candidate.get("cross_domain_time_coverage_identified") is not False:
        errors.append("cross-domain coverage overstated")
    domains = {d.get("domain"): d for d in candidate.get("domains", [])}
    for name in ("doom_v38", "doom_v39", "openttd"):
        if domains.get(name, {}).get("time_coverage_identified") is not False:
            errors.append(name + " coverage not held")
    v38 = jsonl(contents["doom-v38-events.jsonl"])
    v39 = jsonl(contents["doom-v39-events.jsonl"])
    tt = jsonl(contents["openttd-events.jsonl"])
    raw_counts = {"doom_v38": event_counts(v38), "doom_v39": event_counts(v39),
                  "openttd": event_counts(tt)}
    if not counts_match_report(candidate, raw_counts):
        errors.append("candidate/raw event-count mismatch")
    for name, rows in (("doom_v38", v38), ("doom_v39", v39)):
        d = domains[name]
        admissions = [r for r in rows if r.get("event") == "input_admission"]
        releases = [r for r in rows if r.get("event") == "input_released"]
        if not all(type(r.get("admitted_ns")) is int and type(r.get("input_ack_ns")) is int
                   for r in admissions):
            errors.append(name + " admission bracket missing")
        if any(r.get("event") in {"physical_up", "key_up_admission"}
               or (r.get("event") == "input_released" and r.get("key") is not None)
               for r in rows):
            errors.append(name + " unexpected per-press up")
        if d.get("per_actuation_occupancy_identified") is not False:
            errors.append(name + " occupancy overstated")
        if d.get("first_useful_feedback_verified") is not False:
            errors.append(name + " useful feedback overstated")
        if releases and any(r.get("owner_release", {}).get("verified") is not True
                            for r in releases):
            errors.append(name + " malformed terminal release")
    obs = ait_rows(contents["openttd-observer.txt"])
    summary = observer_summary(obs)
    tt_domain = domains["openttd"]
    if (summary["raw_total_records"], summary["unique_states"],
        summary["transition_indices"]) != (263, 2, [91]):
        errors.append("raw observer cardinality/transition mismatch")
    if not observer_report_matches(tt_domain, summary):
        errors.append("candidate observer cardinalities mismatch")
    downs = [r for r in tt if r.get("event") == "pointer_admission"
             and r.get("operation") == "button_down"]
    ups = [r for r in tt if r.get("event") == "pointer_admission"
           and r.get("operation") == "button_up"]
    terminals = {r.get("id"): r for r in tt if r.get("event") == "terminal"}
    joins = sum(r.get("id") in terminals
                and terminals[r["id"]].get("release", {}).get("verified") is True
                and terminals[r["id"]]["release"].get("buttons_down") == []
                and terminals[r["id"]]["release"].get("keys_down") == []
                for r in downs)
    if (len(downs), len(ups), joins) != (7, 0, 7):
        errors.append("OpenTTD terminal/input counts mismatch")
    if tt_domain.get("effect_clock_join_identified") is not False:
        errors.append("observer effect-clock join overstated")
    task_audit = json.loads(contents["openttd-audit.json"])
    outcome = task_audit.get("continuous_independent_observer_outcome", {})
    if outcome.get("status") != "partial_A_to_B_only" or task_audit.get("hard_success") is not False:
        errors.append("OpenTTD independent task outcome mismatch")
    return {"status": "PASS_AUDIT_SUCCESSOR_SCOPED" if not errors else "FAIL_AUDIT_SUCCESSOR",
            "errors": errors, "raw_event_counts": raw_counts,
            "openttd_observer": summary,
            "openttd_input": {"button_down": len(downs), "button_up": len(ups),
                              "same_program_verified_neutral_terminals": joins}}

def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    candidate = json.loads((HERE / "inputs" / "candidate_result.json").read_text(encoding="utf-8"))
    contents = {name: (HERE / "inputs" / name).read_text(encoding="utf-8")
                for name in freeze["inputs"]}
    result = raw_audit(freeze, candidate, contents)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_AUDIT_SUCCESSOR_SCOPED" else 1)

if __name__ == "__main__":
    main()
