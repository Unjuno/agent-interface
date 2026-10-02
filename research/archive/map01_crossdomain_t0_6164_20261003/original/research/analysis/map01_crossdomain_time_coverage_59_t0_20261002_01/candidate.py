import json


def _integer(value):
    return type(value) is int and value >= 0


def _actuation_admissions(events):
    result = []
    for row in events:
        if not isinstance(row, dict):
            continue
        if row.get("event") == "input_admission":
            result.append(row)
        elif (row.get("event") == "pointer_admission"
              and row.get("operation") == "button_down"):
            result.append(row)
    return result


def classify_domain(domain, events, observer_rows, useful_effect_ids):
    """Classify whether one trace identifies physical interval and effect time.

    Program admission, terminal neutral receipts, and observer sequence indices
    are retained as separate evidence classes; none substitutes for an
    actuation's paired physical edges or a clock-linked independent effect.
    """
    admissions = _actuation_admissions(events)
    by_actuation = {}
    for row in events:
        if not isinstance(row, dict):
            continue
        identity = row.get("actuation_id")
        if identity is None:
            continue
        by_actuation.setdefault(identity, []).append(row)

    occupancy_ns = 0
    occupancy_complete = bool(admissions)
    effect_join_complete = bool(admissions)
    used_ids = set()
    for admission in admissions:
        identity = admission.get("actuation_id")
        if not isinstance(identity, str) or not identity or identity in used_ids:
            occupancy_complete = False
            effect_join_complete = False
            continue
        used_ids.add(identity)
        rows = by_actuation.get(identity, [])
        downs = [r for r in rows if r.get("event") == "physical_down"]
        ups = [r for r in rows if r.get("event") == "physical_up"]
        if (len(downs) != 1 or len(ups) != 1
                or not _integer(downs[0].get("host_ns"))
                or not _integer(ups[0].get("host_ns"))
                or downs[0]["host_ns"] > ups[0]["host_ns"]):
            occupancy_complete = False
        elif (not admission.get("clock_domain_id")
              or admission.get("clock_domain_id") != downs[0].get("clock_domain_id")
              or admission.get("clock_domain_id") != ups[0].get("clock_domain_id")):
            occupancy_complete = False
        else:
            occupancy_ns += ups[0]["host_ns"] - downs[0]["host_ns"]
        effects = [r for r in rows if r.get("event") == "independent_effect"
                   and r.get("verified") is True
                   and _integer(r.get("host_ns"))]
        if len(effects) != 1:
            effect_join_complete = False
        if len(downs) == 1 and len(ups) == 1 and len(effects) == 1:
            clock_ids = {admission.get("clock_domain_id"),
                         downs[0].get("clock_domain_id"),
                         ups[0].get("clock_domain_id"),
                         effects[0].get("clock_domain_id")}
            if None in clock_ids or len(clock_ids) != 1:
                effect_join_complete = False

    return {
        "domain": domain,
        "admitted_actuations": len(admissions),
        "independent_effect_observed": bool(useful_effect_ids) or any(
            isinstance(row, dict) and row.get("scoreable") is True
            for row in observer_rows),
        "observer_records": len(observer_rows),
        "observer_sequence_only": bool(observer_rows) and not any(
            _integer(row.get("host_ns")) and row.get("actuation_id")
            for row in observer_rows if isinstance(row, dict)),
        "per_actuation_occupancy_identified": occupancy_complete,
        "effect_clock_join_identified": effect_join_complete,
        "time_coverage_identified": occupancy_complete and effect_join_complete,
        "identified_occupancy_ns": occupancy_ns if occupancy_complete else None,
        "status": ("PASS_TIME_COVERAGE_SCOPED" if occupancy_complete and effect_join_complete
                   else "HOLD_TIME_COVERAGE_UNIDENTIFIED"),
    }


def parse_jsonl(text):
    rows = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"JSONL row {line_number} is not an object")
        rows.append(row)
    return rows


def parse_ait_records(text):
    records = []
    for line_number, line in enumerate(text.splitlines(), 1):
        marker = line.find("AIT {")
        if marker < 0:
            continue
        record = json.loads(line[marker + 4:])
        if isinstance(record, dict) and isinstance(record.get("tiles"), list):
            records.append(record)
    return records


def observer_transition_indices(records):
    states = [tuple((tile.get("id"), tile.get("road"), tile.get("owner"))
                    for tile in record["tiles"])
              for record in records]
    transitions = []
    unique = set(states)
    for index in range(1, len(states)):
        if states[index] != states[index - 1]:
            transitions.append(index)
    return transitions, len(unique)


def classify_cross_domain(doom_v38_events, doom_v39_events, analysis,
                          openttd_events, observer_records):
    by_name = {run["run"]: run for run in analysis["runs"]}
    doom_outputs = []
    for name, events in (("v38", doom_v38_events), ("v39", doom_v39_events)):
        report = by_name[f"map01-{name}-" + (
            "integrated-threat-live-01" if name == "v38"
            else "coast-liveness-live-01")]
        useful = [row for row in report.get("first_exact_plan_feedback", [])
                  if row.get("semantic_task_feedback") == "verified"]
        result = classify_domain(f"doom_{name}", events, [],
                                 [row.get("id") for row in useful])
        counts = {}
        for row in events:
            counts[row["event"]] = counts.get(row["event"], 0) + 1
        totals = report["totals"]
        motor = totals["motor_capable_cover_envelope_ms"]
        wait = totals["model_wait_ms"]
        terminal_rows = [row for row in events if row.get("event") == "input_released"]
        scores = [row for row in events if row.get("event") == "post_control_score"]
        result.update({
            "event_counts": counts,
            "model_wait_ms": wait,
            "motor_capable_program_envelope_ms": motor,
            "motor_envelope_fraction_of_model_wait": motor / wait if wait else None,
            "input_released_program_records": len(terminal_rows),
            "first_useful_feedback_verified": bool(useful),
            "post_control_scores": scores,
            "map_exit": totals["independent_map_exit"],
            "source_scope": "program-envelope data and key admission brackets; not per-key physical occupancy",
        })
        doom_outputs.append(result)

    pointer_downs = [row for row in openttd_events
                     if row.get("event") == "pointer_admission"
                     and row.get("operation") == "button_down"]
    terminals = {row.get("id"): row for row in openttd_events
                 if row.get("event") == "terminal"}
    neutral_joins = [row for row in pointer_downs
                     if row.get("id") in terminals
                     and isinstance(terminals[row["id"]].get("release"), dict)
                     and terminals[row["id"]]["release"].get("verified") is True
                     and terminals[row["id"]]["release"].get("buttons_down") == []
                     and terminals[row["id"]]["release"].get("keys_down") == []]
    transitions, unique_states = observer_transition_indices(observer_records)
    observer_for_join = [{"record_index": index, "scoreable": True}
                         for index in transitions]
    openttd_result = classify_domain(
        "openttd", openttd_events, observer_for_join,
        [f"observer-transition:{index}" for index in transitions])
    counts = {}
    for row in openttd_events:
        counts[row["event"]] = counts.get(row["event"], 0) + 1
    openttd_result.update({
        "event_counts": counts,
        "pointer_button_down_admissions": len(pointer_downs),
        "same_program_verified_neutral_terminal_joins": len(neutral_joins),
        "per_button_up_admissions": sum(
            row.get("event") == "pointer_admission"
            and row.get("operation") == "button_up" for row in openttd_events),
        "observer_record_count": len(observer_records),
        "observer_unique_states": unique_states,
        "observer_transition_indices": transitions,
        "observer_top_level_clock_or_action_identity_fields": sorted({
            key for row in observer_records for key in row
            if key.endswith("_ns") or "clock" in key or "sequence" in key
            or key in {"actuation_id", "action_id"}}),
        "source_scope": "same-program neutral terminals and discrete observer transition; no observer host-time/action join",
    })

    all_time_eligible = all(row["time_coverage_identified"] for row in doom_outputs)
    shared_denominator = (
        all(row.get("model_wait_ms") is not None for row in doom_outputs)
        and openttd_result.get("model_wait_ms") is not None)
    cross_domain_time_eligible = (all_time_eligible
                                  and openttd_result["time_coverage_identified"]
                                  and shared_denominator)
    return {
        "schema": "map01-crossdomain-time-coverage-candidate-v1",
        "status": ("PASS_CROSSDOMAIN_TIME_COVERAGE_SCOPED" if cross_domain_time_eligible
                   else "HOLD_CROSSDOMAIN_TIME_COVERAGE_UNIDENTIFIED"),
        "domains": doom_outputs + [openttd_result],
        "interpretation": (
            "Program envelopes, physical occupancy, terminal neutral receipts, and useful-effect timing are separate evidence classes. A common time-weighted coverage value is withheld unless per-actuation down/up edges, clock-bound independent effects, and a shared denominator are identified in every domain."
        ),
        "cross_domain_time_coverage_identified": cross_domain_time_eligible,
        "shared_time_denominator_identified": shared_denominator,
        "candidate_invocations": 1,
        "retries": 0,
    }
