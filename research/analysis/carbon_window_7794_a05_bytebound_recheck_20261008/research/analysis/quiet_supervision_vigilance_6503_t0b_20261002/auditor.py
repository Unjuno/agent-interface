"""Independent raw-only reconstruction. Deliberately does not import candidate/scorer."""
from __future__ import annotations

FORBIDDEN = {"oracle", "truth", "anomaly_present", "required_safe_action", "scorer_label", "expected_response"}
POLICIES = ("A_CONTINUOUS", "B_EVIDENCE", "C_PERIODIC", "D_HARD_ALERT")


def _reference_signal(truth: dict, response: dict) -> tuple[str, bool, int | None, bool | None]:
    time = response.get("response_ms")
    no_response = time is None
    delay = None if time is None or "onset_ms" not in truth or time < truth["onset_ms"] else time - truth["onset_ms"]
    in_window = time is not None and time >= truth.get("onset_ms", time) and time <= truth.get("expiry_ms", time)
    if truth["mandatory_stop"]:
        outcome = "prompted_hard_stop" if response.get("prompted_by_hard_alert") else "mandatory_stop_unprompted_channel"
    elif truth["anomaly_present"] and truth["visibility"] != "visible":
        outcome = "unobservable_anomaly"
    elif truth["anomaly_present"]:
        outcome = "hit" if response.get("reported_anomaly") and in_window else "miss"
    else:
        outcome = "false_alarm" if response.get("reported_anomaly") and in_window else "correct_rejection"
    safe = None if no_response else response.get("safe_action") == truth["required_safe_action"]
    return outcome, no_response, delay, safe


def audit(stimuli: dict, truth: dict, material: dict, scored: list[dict]) -> dict:
    errors = []
    source = {event["id"]: event for event in stimuli["events"]}
    rows = material.get("rows", [])
    expected_n = len(source) * len(POLICIES)
    if len(rows) != expected_n or material.get("opportunities_per_policy") != len(source):
        errors.append("assigned_opportunity_denominator_mismatch")
    indexed = {(r.get("opportunity_id"), r.get("policy")): r for r in rows}
    if len(indexed) != len(rows):
        errors.append("duplicate_opportunity_policy")
    if set(indexed) != {(oid, policy) for oid in source for policy in POLICIES}:
        errors.append("opportunity_policy_factor_mismatch")

    visible_fields_b = []
    visible_fields_c = []
    checkpoint_counts = {p: 0 for p in POLICIES}
    hard_alert_counts = {p: 0 for p in POLICIES}
    tokens = {}
    for (oid, policy), row in indexed.items():
        event = source.get(oid)
        if event is None:
            errors.append("unknown_opportunity")
            continue
        token = row.get("opportunity_token")
        tokens.setdefault(oid, set()).add(token)
        if row.get("block") != event["block"] or row.get("position") != event["position"] or row.get("timestamp_ms") != event["time_ms"]:
            errors.append("opportunity_identity_or_time_mismatch")
        if row.get("machine_gate") != event.get("machine_gate", {"state":"CLEAR","release_allowed":True}):
            errors.append("machine_gate_changed")
        mandatory = row["machine_gate"].get("state") == "STOP_LATCHED"
        if row.get("hard_alert_visible") != mandatory:
            errors.append("mandatory_hard_alert_suppressed_or_invented")
        if mandatory and row.get("hard_alert_visible"):
            hard_alert_counts[policy] += 1
        if row.get("human_response") is not None:
            errors.append("human_response_fabricated_in_material")
        payload = row.get("payload", {})
        if any(any(word in key.lower() for word in FORBIDDEN) for key in _all_keys(payload)):
            errors.append("oracle_only_field_leaked")
        if row.get("review_visible"):
            if payload.get("source_ref") != event["source_ref"] or payload.get("evidence") != event["evidence"]:
                errors.append("display_not_source_bound")
            if policy in ("B_EVIDENCE", "C_PERIODIC"):
                fields = tuple(sorted(payload.keys()))
                (visible_fields_b if policy == "B_EVIDENCE" else visible_fields_c).append(fields)
                if not mandatory:
                    checkpoint_counts[policy] += 1
        elif payload.get("evidence") is not None:
            errors.append("hidden_evidence_exposed")
        elif payload.get("source_ref") is not None:
            errors.append("hidden_source_reference_exposed")
        if policy == "B_EVIDENCE" and row.get("review_visible") and not mandatory:
            if oid not in stimuli["review_predicates"] or row.get("review_predicate") != stimuli["review_predicates"][oid]:
                errors.append("evidence_review_not_derived_from_public_predicate")
        if policy == "C_PERIODIC":
            should_show = event["position"] in stimuli["fixed_checkpoint_positions"] or mandatory
            if row.get("review_visible") != should_show:
                errors.append("fixed_schedule_deviation")
        if policy == "D_HARD_ALERT" and row.get("review_visible") != mandatory:
            errors.append("hard_alert_only_control_deviation")

    if len(tokens) != len(source) or any(len(v) != 1 for v in tokens.values()):
        errors.append("cross_policy_opportunity_token_mismatch")
    if checkpoint_counts["B_EVIDENCE"] != 6 or checkpoint_counts["C_PERIODIC"] != 6:
        errors.append("checkpoint_count_not_matched")
    if any(hard_alert_counts[p] != 1 for p in POLICIES):
        errors.append("hard_alert_opportunity_not_invariant")
    if visible_fields_b != visible_fields_c:
        errors.append("B_C_factual_field_schema_mismatch")

    oracle = truth["default"]
    truth_by_id = {}
    for oid, event in source.items():
        item = {**oracle, **truth["overrides"].get(oid, {})}
        item.setdefault("onset_ms", event["time_ms"])
        item.setdefault("expiry_ms", event["time_ms"] + stimuli["response_window_ms"])
        truth_by_id[oid] = item
        if item["expiry_ms"] != item["onset_ms"] + stimuli["response_window_ms"]:
            errors.append("opportunity_window_not_exact")
        if item["mandatory_stop"] != (event.get("machine_gate", {}).get("state") == "STOP_LATCHED"):
            errors.append("oracle_machine_gate_state_mismatch")
        unavailable = not bool(event.get("evidence")) or event.get("evidence", {}).get("capture") == "unavailable"
        if unavailable != (item["visibility"] == "not_captured"):
            errors.append("oracle_visibility_source_mismatch")
    if len(scored) != expected_n:
        errors.append("scored_opportunity_denominator_mismatch")
    expected_scores = {}
    vector_overrides = truth["scoring_vectors"]["overrides"]
    for oid in source:
        for policy in POLICIES:
            key = (oid, policy)
            vector_key = f"{oid}/{policy[0]}"
            response = dict(truth["scoring_vectors"]["default"])
            response.update(vector_overrides.get(vector_key, {}))
            response.update({"opportunity_id": oid, "policy": policy})
            expected_scores[key] = _reference_signal(truth_by_id[oid], response)
    observed_scores = {}
    for score in scored:
        key = (score.get("opportunity_id"), score.get("policy"))
        if key in observed_scores:
            errors.append("duplicate_scored_opportunity")
        observed_scores[key] = score
        if key not in expected_scores:
            errors.append("unknown_scored_opportunity")
            continue
        expected = expected_scores[key]
        observed = (score.get("signal_outcome"), score.get("no_response"), score.get("response_delay_ms"), score.get("correct_safe_next_step"))
        if observed != expected:
            errors.append("scripted_scorer_outcome_mismatch")
    if set(observed_scores) != set(expected_scores):
        errors.append("scored_factor_mismatch")
    counts = {}
    for score in scored:
        outcome = score.get("signal_outcome")
        counts[outcome] = counts.get(outcome, 0) + 1
    no_response_rows = sum(bool(score.get("no_response")) for score in scored)
    late_response_rows = sum(bool(score.get("late_response")) for score in scored)
    safe_step = {
        "correct": sum(score.get("correct_safe_next_step") is True for score in scored),
        "incorrect": sum(score.get("correct_safe_next_step") is False for score in scored),
        "not_observed": sum(score.get("correct_safe_next_step") is None for score in scored),
    }
    anomaly_counts = {
        "observable_unprompted": sum(1 for row in scored if truth_by_id[row["opportunity_id"]]["anomaly_present"] and truth_by_id[row["opportunity_id"]]["visibility"] == "visible" and not truth_by_id[row["opportunity_id"]]["mandatory_stop"]),
        "unobservable": sum(1 for row in scored if truth_by_id[row["opportunity_id"]]["anomaly_present"] and truth_by_id[row["opportunity_id"]]["visibility"] == "not_captured"),
        "prompted_hard_stop": sum(1 for row in scored if truth_by_id[row["opportunity_id"]]["mandatory_stop"]),
    }
    expected_controls = {
        "A_hit": any(s.get("opportunity_id") == "early-04" and s.get("policy") == "A_CONTINUOUS" and s.get("signal_outcome") == "hit" for s in scored),
        "A_late_miss": any(s.get("opportunity_id") == "middle-03" and s.get("policy") == "A_CONTINUOUS" and s.get("signal_outcome") == "miss" and s.get("late_response") for s in scored),
        "A_false_alarm": any(s.get("opportunity_id") == "early-05" and s.get("policy") == "A_CONTINUOUS" and s.get("signal_outcome") == "false_alarm" for s in scored),
        "invisible_excluded": all(s.get("signal_outcome") == "unobservable_anomaly" for s in scored if s.get("opportunity_id") == "late-03"),
        "hard_stop_prompted": any(s.get("opportunity_id") == "late-09" and s.get("policy") == "A_CONTINUOUS" and s.get("signal_outcome") == "prompted_hard_stop" for s in scored),
    }
    if not all(expected_controls.values()):
        errors.append("planted_scorer_controls_not_reproduced")
    source_truth_checks = {
        "wrong_target_evidence": source["early-04"]["evidence"].get("planned_target") != source["early-04"]["evidence"].get("observed_target") and truth_by_id["early-04"]["source_state"] == "target_mismatch",
        "ambiguous_effect_evidence": source["middle-03"]["evidence"].get("effect") == "pending" and truth_by_id["middle-03"]["effect_state"] == "ambiguous_pending",
        "uncaptured_visibility": source["late-03"]["evidence"] == {} and truth_by_id["late-03"]["visibility"] == "not_captured",
        "hard_stop_truth": source["late-09"].get("machine_gate", {}).get("state") == "STOP_LATCHED" and truth_by_id["late-09"]["mandatory_stop"],
        "verified_success_evidence": source["late-05"]["evidence"].get("effect") == "saved" and truth_by_id["late-05"]["effect_state"] == "verified_saved",
        "benign_visual_control": source["early-05"]["evidence"].get("visual_delta") == "theme-color-only" and not truth_by_id["early-05"]["anomaly_present"],
    }
    for oid, event in source.items():
        ev = event["evidence"]
        oracle_row = truth_by_id[oid]
        observed_effect = ev.get("effect")
        expected_effect = {
            "not_due": "no_effect_due",
            "saved": "verified_saved",
            "pending": "ambiguous_pending",
            "receipt-pending": "receipt_pending",
        }.get(observed_effect)
        if expected_effect is not None and oracle_row["effect_state"] != expected_effect:
            source_truth_checks[f"effect_{oid}"] = False
        version = ev.get("source_version")
        expected_source = {
            "v1": "current",
            "v2": "version_advanced",
            "current": "current",
            "changed": "changed_since_last_review",
        }.get(version)
        if expected_source is not None and oracle_row["source_state"] != expected_source:
            source_truth_checks[f"source_{oid}"] = False
    if not all(source_truth_checks.values()):
        errors.append("source_effect_truth_not_reconciled")
    if any(score.get("response_provenance") != "synthetic-script" for score in scored):
        errors.append("non_synthetic_response_provenance")
    return {
        "status": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "assigned_rows": len(rows),
        "scored_rows": len(scored),
        "unique_opportunities": len(source),
        "checkpoint_counts": checkpoint_counts,
        "hard_alert_counts": hard_alert_counts,
        "scored_outcomes": dict(sorted(counts.items())),
        "no_response_rows": no_response_rows,
        "late_response_rows": late_response_rows,
        "safe_next_step_counts": safe_step,
        "anomaly_opportunity_denominators": anomaly_counts,
        "scripted_controls": expected_controls,
        "source_truth_checks": source_truth_checks,
        "human_responses": 0,
        "errors": sorted(set(errors)),
    }


def _all_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _all_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _all_keys(item)
