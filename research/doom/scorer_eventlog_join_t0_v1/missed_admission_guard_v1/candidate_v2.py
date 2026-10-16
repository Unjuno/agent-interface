"""Corrected admission-boundary policy; historical candidate.py is retained."""
from __future__ import annotations


def classify_intent(events, samples, intent_id, *, max_gap_ns):
    """Return a fail-closed admission-bracket classification for intent_id.

    Times are expected to share the guest runtime's monotonic nanosecond domain.
    A positive result is an observed interval association, not causal attribution.
    """
    if not isinstance(intent_id, str) or not intent_id:
        return _reject("invalid_intent_id")
    if type(max_gap_ns) is not int or max_gap_ns <= 0:
        return _reject("invalid_max_gap")

    accepted = [row for row in events if row.get("event") == "accepted" and row.get("id") == intent_id]
    if len(accepted) != 1:
        return _reject("missing_or_ambiguous_acceptance")
    accepted_ns = accepted[0].get("accepted_ns")
    if type(accepted_ns) is not int:
        return _reject("invalid_acceptance_timestamp")

    admissions = [row for row in events if row.get("event") == "input_admission" and row.get("id") == intent_id]
    if not admissions:
        return _reject("missing_first_input_admission")
    if any(type(row.get("admitted_ns")) is not int for row in admissions):
        return _reject("invalid_input_admission_timestamp")
    first_input = min(admissions, key=lambda row: row["admitted_ns"])
    first_input_ns = first_input["admitted_ns"]
    if accepted_ns >= first_input_ns:
        return _reject("invalid_admission_bracket")

    parsed = []
    for row in samples:
        payload = row.get("payload")
        if not isinstance(payload, dict):
            return _reject("invalid_scorer_payload")
        sample_ns = payload.get("sample_ns")
        started = row.get("sample_started_ns")
        finished = row.get("sample_finished_ns")
        missed = row.get("missed_periods_before")
        kills = payload.get("kill_count")
        deaths = payload.get("death_count")
        map_exit = payload.get("map_exit")
        if (type(sample_ns) is not int or type(started) is not int or type(finished) is not int
                or started > sample_ns or sample_ns > finished):
            return _reject("invalid_scorer_clock_bracket")
        if (type(missed) is not int or missed < 0 or type(kills) is not int or kills < 0
                or type(deaths) is not int or deaths < 0 or type(map_exit) is not bool):
            return _reject("invalid_scorer_state_or_scheduler")
        parsed.append((sample_ns, missed, kills, deaths, map_exit))
    if not parsed:
        return _reject("missing_scorer_samples")
    if any(b[0] <= a[0] for a, b in zip(parsed, parsed[1:])):
        return _reject("scorer_clock_not_strictly_increasing")

    baseline_indices = [i for i, sample in enumerate(parsed)
                        if accepted_ns < sample[0] < first_input_ns]
    if not baseline_indices:
        return _reject("no_post_acceptance_pre_input_baseline")
    # Use the freshest state before the first input. An earlier baseline can
    # make progress already observed before input look like a later recovery
    # improvement when the score remains elevated.
    baseline_index = baseline_indices[-1]
    baseline = parsed[baseline_index]

    for sample in parsed[baseline_index + 1:]:
        sample_ns, missed, kills, deaths, map_exit = sample
        if sample_ns <= first_input_ns:
            # An admission-time observation is not progress after input, but
            # its missed period still lies after the selected baseline.
            if missed:
                return _reject("missed_scorer_period")
            continue
        if sample_ns - baseline[0] > max_gap_ns:
            return _reject("positive_sample_gap_exceeded")
        if missed:
            return _reject("missed_scorer_period")
        if kills > baseline[2] or map_exit and not baseline[4]:
            return {
                "decision": "ADMISSION_BRACKETED_PROGRESS",
                "reason": "bounded_independent_progress_observed_after_first_input",
                "intent_id": intent_id,
                "accepted_ns": accepted_ns,
                "first_input_ns": first_input_ns,
                "baseline_ns": baseline[0],
                "positive_sample_ns": sample_ns,
                "gap_ns": sample_ns - baseline[0],
                "progress": {"kill_count": kills, "death_count": deaths, "map_exit": map_exit},
                "causal_attribution": False,
            }
    return _reject("no_bounded_post_input_progress")


def _reject(reason):
    return {"decision": "POST_CANCELLATION_COOCCURRENCE", "reason": reason,
            "causal_attribution": False}
