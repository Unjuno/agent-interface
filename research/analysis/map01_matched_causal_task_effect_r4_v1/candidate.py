"""Candidate classifier for the Issue #3885 finite causal contract."""

GATES = (
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
    "baseline_same_effect_present",
    "candidate_effect_inside_window",
    "scorer_independent",
)


def classify(row):
    """Return the causal label and non-authority marker for one row."""
    if row.get("polarity") not in ("useful", "harmful"):
        raise ValueError("invalid polarity")
    if any(type(row.get(gate)) is not bool for gate in GATES):
        raise ValueError("every gate must be Boolean")
    accepted = all(row[g] for g in GATES if g != "baseline_same_effect_present")
    accepted = accepted and not row["baseline_same_effect_present"]
    if not accepted:
        label = "UNRESOLVED"
    elif row["polarity"] == "useful":
        label = "CAUSAL_USEFUL_TASK_EFFECT"
    else:
        label = "CAUSAL_HARMFUL_TASK_EFFECT"
    return {"disposition": label, "authority_granted": False}
