"""Independent oracle; intentionally does not import candidate.py."""


def expected(row):
    required = (
        "pair_identity_match",
        "initial_state_match",
        "seed_match",
        "exogenous_schedule_match",
        "scorer_identity_match",
        "measurement_window_match",
        "deterministic_fixture_attested",
        "sole_actuation_difference",
        "baseline_task_input_zero",
        "candidate_ledger_valid",
        "clock_comparable",
        "candidate_effect_present",
        "candidate_effect_inside_window",
        "scorer_independent",
    )
    if not all(row.get(k) is True for k in required):
        return "UNRESOLVED"
    if row.get("baseline_same_effect_present") is not False:
        return "UNRESOLVED"
    if row.get("polarity") == "useful":
        return "CAUSAL_USEFUL_TASK_EFFECT"
    if row.get("polarity") == "harmful":
        return "CAUSAL_HARMFUL_TASK_EFFECT"
    return "UNRESOLVED"
