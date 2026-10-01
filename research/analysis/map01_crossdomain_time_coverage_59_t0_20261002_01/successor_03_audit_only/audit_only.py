"""Raw-only audit successor; intentionally imports no candidate implementation."""
import hashlib
import json


def event_count(rows, kind):
    """A missing sparse event kind is zero, not None."""
    return sum(row.get("event") == kind for row in rows)


def event_counts(rows):
    return {kind: event_count(rows, kind)
            for kind in sorted({row.get("event") for row in rows})}


def parse_jsonl(text):
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def parse_ait(text):
    records = []
    for line in text.splitlines():
        marker = line.find("AIT {")
        if marker >= 0:
            row = json.loads(line[marker + 4:])
            if isinstance(row, dict) and isinstance(row.get("tiles"), list):
                records.append(row)
    return records


def ait_transitions(records):
    states = [tuple((tile.get("id"), tile.get("road"), tile.get("owner"))
                    for tile in record["tiles"]) for record in records]
    return ([index for index in range(1, len(states))
             if states[index] != states[index - 1]], len(set(states)))


def candidate_summary_errors(candidate, raw_counts, observer_count,
                             transitions, unique_states, pointer_counts=None,
                             actuation_counts=None):
    errors = []
    domains = {row.get("domain"): row for row in candidate.get("domains", [])}
    if candidate.get("status") != "HOLD_CROSSDOMAIN_TIME_COVERAGE_UNIDENTIFIED":
        errors.append("cross-domain coverage overclaim")
    if candidate.get("cross_domain_time_coverage_identified") is not False:
        errors.append("cross-domain coverage boolean overclaim")
    if candidate.get("shared_time_denominator_identified") is not False:
        errors.append("shared denominator overclaim")
    for name, counts in raw_counts.items():
        row = domains.get(name, {})
        if row.get("event_counts") != counts:
            errors.append(f"{name} event_counts differ from raw")
        for field, expected in (("time_coverage_identified", False),
                                ("per_actuation_occupancy_identified", False),
                                ("effect_clock_join_identified", False)):
            if row.get(field) is not expected:
                errors.append(f"{name} {field} overclaim")
        if name.startswith("doom_") and row.get("first_useful_feedback_verified") is not False:
            errors.append(f"{name} promotes unverified useful feedback")
        if actuation_counts is not None and row.get("admitted_actuations") != actuation_counts[name]:
            errors.append(f"{name} actuation admission count differs from raw")
    observer = domains.get("openttd", {})
    if observer.get("observer_records") != observer_count or observer.get("observer_record_count") != observer_count:
        errors.append("OpenTTD observer record count mismatch")
    if observer.get("observer_transition_witness_count") != len(transitions):
        errors.append("OpenTTD transition-witness count mismatch")
    if observer.get("observer_transition_indices") != transitions:
        errors.append("OpenTTD transition indices differ from raw")
    if observer.get("observer_unique_states") != unique_states:
        errors.append("OpenTTD unique-state count differs from raw")
    if pointer_counts is not None:
        for field, expected in pointer_counts.items():
            if observer.get(field) != expected:
                errors.append(f"OpenTTD {field} differs from raw")
    return errors


def audit(candidate, sources, predecessor_freeze):
    errors = []
    inputs = predecessor_freeze["inputs"]
    for name, spec in inputs.items():
        if hashlib.sha256(sources[name].encode("utf-8")).hexdigest() != spec["sha256"]:
            errors.append(f"{name} input hash mismatch")

    v38 = parse_jsonl(sources["doom-v38-events.jsonl"])
    v39 = parse_jsonl(sources["doom-v39-events.jsonl"])
    openttd = parse_jsonl(sources["openttd-events.jsonl"])
    counts = {"doom_v38": event_counts(v38), "doom_v39": event_counts(v39),
              "openttd": event_counts(openttd)}
    # Explicitly exercise zero-default semantics for sparse event maps.
    if (event_count(v38, "input_admission"), event_count(v38, "keys_held"),
            event_count(v38, "input_released"), event_count(v38, "post_control_score")) != (11, 11, 0, 1):
        errors.append("v38 raw source count gate mismatch")
    if (event_count(v39, "input_admission"), event_count(v39, "keys_held"),
            event_count(v39, "input_released"), event_count(v39, "post_control_score")) != (39, 28, 1, 1):
        errors.append("v39 raw source count gate mismatch")
    if any(row.get("event") in {"physical_up", "key_up_admission"}
           or (row.get("event") == "input_released" and row.get("key") is not None)
           for row in v38 + v39):
        errors.append("unexpected per-press physical-up record present")

    analysis = json.loads(sources["doom-analysis.json"])
    for version, rows in (("v38", v38), ("v39", v39)):
        run_name = "map01-v38-integrated-threat-live-01" if version == "v38" \
            else "map01-v39-coast-liveness-live-01"
        run = next((item for item in analysis.get("runs", [])
                    if item.get("run") == run_name), {})
        recorded = run.get("source_sha256", {}).get("runtime/events.jsonl")
        observed = hashlib.sha256(sources[f"doom-{version}-events.jsonl"].encode("utf-8")).hexdigest()
        if recorded != observed:
            errors.append(f"{version} analysis-to-raw SHA join mismatch")

    downs = [row for row in openttd if row.get("event") == "pointer_admission"
             and row.get("operation") == "button_down"]
    ups = [row for row in openttd if row.get("event") == "pointer_admission"
           and row.get("operation") == "button_up"]
    terminals = {row.get("id"): row for row in openttd if row.get("event") == "terminal"}
    neutral = sum(row.get("id") in terminals
                  and terminals[row["id"]].get("release", {}).get("verified") is True
                  and terminals[row["id"]].get("release", {}).get("buttons_down") == []
                  and terminals[row["id"]].get("release", {}).get("keys_down") == []
                  for row in downs)
    observer = parse_ait(sources["openttd-observer.txt"])
    transitions, unique_states = ait_transitions(observer)
    if (len(downs), len(ups), neutral) != (7, 0, 7):
        errors.append("OpenTTD down/up/neutral-terminal source counts differ")
    if (len(observer), unique_states, transitions) != (263, 2, [91]):
        errors.append("OpenTTD observer records/states/transitions differ")
    link_fields = {key for row in observer for key in row
                   if key.endswith("_ns") or "clock" in key or "sequence" in key
                   or key in {"actuation_id", "action_id"}}
    if link_fields:
        errors.append("OpenTTD observer has a time/action link field")

    actuation_counts = {"doom_v38": event_count(v38, "input_admission"),
                        "doom_v39": event_count(v39, "input_admission"),
                        "openttd": event_count(openttd, "input_admission") + len(downs)}
    candidate_errors = candidate_summary_errors(
        candidate, counts, len(observer), transitions, unique_states,
        pointer_counts={"pointer_button_down_admissions": len(downs),
                        "per_button_up_admissions": len(ups),
                        "same_program_verified_neutral_terminal_joins": neutral},
        actuation_counts=actuation_counts)
    errors.extend(candidate_errors)

    source_audit = json.loads(sources["openttd-audit.json"])
    outcome = source_audit.get("continuous_independent_observer_outcome", {})
    if (outcome.get("status") != "partial_A_to_B_only"
            or outcome.get("records") != len(observer)
            or outcome.get("unique_states") != unique_states
            or outcome.get("transition_indices") != transitions
            or source_audit.get("hard_success") is not False):
        errors.append("OpenTTD independent task-audit outcome mismatch")
    candidate_outcome = candidate.get("openttd_task_outcome", {})
    if (candidate_outcome.get("status") != outcome.get("status")
            or candidate_outcome.get("records") != outcome.get("records")
            or candidate_outcome.get("unique_states") != outcome.get("unique_states")
            or candidate_outcome.get("transition_indices") != outcome.get("transition_indices")
            or candidate_outcome.get("hard_success") is not False):
        errors.append("candidate OpenTTD outcome summary mismatch")
    return {"status": "PASS_AUDIT_CROSSDOMAIN_HOLD_REPRODUCED" if not errors else "FAIL_AUDIT",
            "errors": errors,
            "independently_reconstructed": {
                "v38": {"counts": counts["doom_v38"], "per_press_up": False},
                "v39": {"counts": counts["doom_v39"], "per_press_up": False},
                "openttd": {"counts": counts["openttd"], "button_down": len(downs),
                            "button_up": len(ups), "neutral_terminal_joins": neutral,
                            "observer_records": len(observer), "unique_states": unique_states,
                            "transition_indices": transitions,
                            "time_action_link_fields": sorted(link_fields)},
            },
            "candidate_summary_consistent": not candidate_errors,
            "audit_only_candidate_invocations": 0,
            "predecessor_candidate_invocations": 1,
            "auditor_invocations": 1,
            "retries": 0}
