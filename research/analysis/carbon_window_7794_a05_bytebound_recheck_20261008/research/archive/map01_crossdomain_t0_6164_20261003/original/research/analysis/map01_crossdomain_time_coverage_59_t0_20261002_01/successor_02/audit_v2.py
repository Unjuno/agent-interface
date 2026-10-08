"""Independent source-count, observer and candidate-surface audit for T0-02."""
import hashlib


def candidate_consistency_errors(candidate, raw_counts, observer_count,
                                 transition_indices, unique_states=None, actuation_counts=None,
                                 pointer_counts=None):
    errors = []
    domains = {row.get("domain"): row for row in candidate.get("domains", [])}
    if candidate.get("status") != "HOLD_CROSSDOMAIN_TIME_COVERAGE_UNIDENTIFIED":
        errors.append("cross-domain coverage status overclaim")
    if candidate.get("cross_domain_time_coverage_identified") is not False:
        errors.append("cross-domain coverage boolean overclaim")
    if candidate.get("shared_time_denominator_identified") is not False:
        errors.append("shared denominator overclaim")
    if candidate.get("candidate_invocations") != 1 or candidate.get("retries") != 0:
        errors.append("candidate invocation/retry accounting mismatch")
    for name, counts in raw_counts.items():
        row = domains.get(name, {})
        if row.get("event_counts") != counts:
            errors.append(f"{name} event_counts differ from raw")
        if row.get("time_coverage_identified") is not False:
            errors.append(f"{name} time coverage overclaim")
        if row.get("per_actuation_occupancy_identified") is not False:
            errors.append(f"{name} physical occupancy overclaim")
        if row.get("effect_clock_join_identified") is not False:
            errors.append(f"{name} effect-clock join overclaim")
        if name in {"doom_v38", "doom_v39"} and row.get("first_useful_feedback_verified") is not False:
            errors.append(f"{name} promotes unverified feedback")
        if actuation_counts is not None and row.get("admitted_actuations") != actuation_counts[name]:
            errors.append(f"{name} admitted actuation count differs from raw")
    observer = domains.get("openttd", {})
    if (observer.get("observer_records") != observer_count
            or observer.get("observer_record_count") != observer_count):
        errors.append("OpenTTD observer record count mismatch")
    if observer.get("observer_transition_witness_count") != len(transition_indices):
        errors.append("OpenTTD observer transition-witness count mismatch")
    if observer.get("observer_transition_indices") != transition_indices:
        errors.append("OpenTTD observer transition indices differ from raw")
    if unique_states is not None and observer.get("observer_unique_states") != unique_states:
        errors.append("OpenTTD observer unique-state count mismatch")
    if pointer_counts is not None:
        for key, expected in pointer_counts.items():
            if observer.get(key) != expected:
                errors.append(f"OpenTTD {key} differs from raw")
    return errors


def audit_raw(candidate, sources, freeze, jsonl_rows, ait_rows, ait_transitions):
    errors = []
    expected_hashes = {name: spec["sha256"] for name, spec in freeze["inputs"].items()}
    for name, text in sources.items():
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != expected_hashes[name]:
            errors.append(f"{name} source SHA mismatch")

    v38 = jsonl_rows(sources["doom-v38-events.jsonl"])
    v39 = jsonl_rows(sources["doom-v39-events.jsonl"])
    ottd = jsonl_rows(sources["openttd-events.jsonl"])
    observer_records = ait_rows(sources["openttd-observer.txt"])
    raw_counts = {
        "doom_v38": {key: sum(row.get("event") == key for row in v38)
                      for key in sorted({row.get("event") for row in v38})},
        "doom_v39": {key: sum(row.get("event") == key for row in v39)
                      for key in sorted({row.get("event") for row in v39})},
        "openttd": {key: sum(row.get("event") == key for row in ottd)
                    for key in sorted({row.get("event") for row in ottd})},
    }
    if (raw_counts["doom_v38"].get("input_admission"),
        raw_counts["doom_v38"].get("keys_held"),
        raw_counts["doom_v38"].get("input_released"),
        raw_counts["doom_v38"].get("post_control_score")) != (11, 11, 0, 1):
        errors.append("v38 raw source counts differ from frozen known totals")
    if (raw_counts["doom_v39"].get("input_admission"),
        raw_counts["doom_v39"].get("keys_held"),
        raw_counts["doom_v39"].get("input_released"),
        raw_counts["doom_v39"].get("post_control_score")) != (39, 28, 1, 1):
        errors.append("v39 raw source counts differ from frozen known totals")
    analysis = __import__("json").loads(sources["doom-analysis.json"])
    for version in ("v38", "v39"):
        expected_run = f"map01-{version}-" + (
            "integrated-threat-live-01" if version == "v38" else "coast-liveness-live-01")
        run = next((row for row in analysis.get("runs", [])
                    if row.get("run") == expected_run), {})
        recorded_event_hash = run.get("source_sha256", {}).get("runtime/events.jsonl")
        observed_event_hash = hashlib.sha256(
            sources[f"doom-{version}-events.jsonl"].encode("utf-8")).hexdigest()
        if recorded_event_hash != observed_event_hash:
            errors.append(f"{version} analysis/raw event hash join mismatch")

    downs = [row for row in ottd if row.get("event") == "pointer_admission"
             and row.get("operation") == "button_down"]
    ups = [row for row in ottd if row.get("event") == "pointer_admission"
           and row.get("operation") == "button_up"]
    terminals = {row.get("id"): row for row in ottd if row.get("event") == "terminal"}
    neutral = sum(row.get("id") in terminals
                  and terminals[row["id"]].get("release", {}).get("verified") is True
                  and terminals[row["id"]].get("release", {}).get("buttons_down") == []
                  and terminals[row["id"]].get("release", {}).get("keys_down") == []
                  for row in downs)
    transitions, unique_states = ait_transitions(observer_records)
    if (len(downs), len(ups), neutral) != (7, 0, 7):
        errors.append("OpenTTD button-down/up/neutral-terminal source counts differ")
    if (len(observer_records), unique_states, transitions) != (263, 2, [91]):
        errors.append("OpenTTD observer-state source counts differ")
    actuation_counts = {
        "doom_v38": raw_counts["doom_v38"].get("input_admission", 0),
        "doom_v39": raw_counts["doom_v39"].get("input_admission", 0),
        "openttd": raw_counts["openttd"].get("input_admission", 0) + len(downs),
    }
    errors.extend(candidate_consistency_errors(
        candidate, raw_counts, len(observer_records), transitions,
        unique_states=unique_states,
        actuation_counts=actuation_counts,
        pointer_counts={"pointer_button_down_admissions": len(downs),
                        "per_button_up_admissions": len(ups),
                        "same_program_verified_neutral_terminal_joins": neutral},
    ))
    observer_candidate = next((row for row in candidate.get("domains", [])
                               if row.get("domain") == "openttd"), {})
    if observer_candidate.get("observer_unique_states") != unique_states:
        errors.append("OpenTTD observer unique-state count differs from raw")
    link_fields = {key for row in observer_records for key in row
                   if key.endswith("_ns") or "clock" in key or "sequence" in key
                   or key in {"actuation_id", "action_id"}}
    if link_fields:
        errors.append("OpenTTD observer contains an unaccounted time/action link field")
    task_audit = __import__("json").loads(sources["openttd-audit.json"])
    task_outcome = task_audit.get("continuous_independent_observer_outcome", {})
    if (task_outcome.get("status") != "partial_A_to_B_only"
            or task_outcome.get("records") != len(observer_records)
            or task_outcome.get("unique_states") != unique_states
            or task_outcome.get("transition_indices") != transitions
            or task_audit.get("hard_success") is not False):
        errors.append("OpenTTD independent audit outcome differs from raw observer")
    candidate_outcome = candidate.get("openttd_task_outcome", {})
    if (candidate_outcome.get("status") != task_outcome.get("status")
            or candidate_outcome.get("records") != task_outcome.get("records")
            or candidate_outcome.get("unique_states") != task_outcome.get("unique_states")
            or candidate_outcome.get("transition_indices") != task_outcome.get("transition_indices")
            or candidate_outcome.get("hard_success") is not False):
        errors.append("candidate OpenTTD task-outcome summary differs from raw audit")
    return {
        "status": "PASS_AUDIT_CROSSDOMAIN_HOLD_REPRODUCED" if not errors else "FAIL_AUDIT",
        "errors": errors,
        "independently_reconstructed": {
            "doom_v38": {"event_counts": raw_counts["doom_v38"],
                         "admitted_actuations": actuation_counts["doom_v38"]},
            "doom_v39": {"event_counts": raw_counts["doom_v39"],
                         "admitted_actuations": actuation_counts["doom_v39"]},
            "openttd": {"event_counts": raw_counts["openttd"],
                        "admitted_actuations": actuation_counts["openttd"],
                        "pointer_button_down": len(downs), "pointer_button_up": len(ups),
                        "neutral_terminal_joins": neutral,
                        "observer_records": len(observer_records),
                        "unique_states": unique_states,
                        "transition_indices": transitions},
        },
        "candidate_and_auditor_separate": True,
        "candidate_invocations": candidate.get("candidate_invocations"),
        "auditor_invocations": 1,
        "retries": 0,
    }
