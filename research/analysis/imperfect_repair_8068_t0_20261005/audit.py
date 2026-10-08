"""Separate reference enumerator; deliberately does not import experiment.py."""

EXPECTED = {
    "p0": ("worker_fault", 0, 1, "perfect", ("save-01",), 0.05, 1, False),
    "p1": ("worker_fault", 2, 2, "perfect", ("save-02",), 0.25, 2, False),
    "m0": ("worker_fault", 0, 1, "minimal", ("save-03",), 0.05, 1, False),
    "m1": ("worker_fault", 2, 2, "minimal", ("save-04",), 0.55, 2, False),
    "i0": ("worker_fault", 0, 1, "imperfect", ("save-05",), 0.05, 1, False),
    "i1": ("worker_fault", 2, 2, "imperfect", ("save-06",), 0.25, 2, False),
    "c0": ("worker_fault", 2, 3, "imperfect", ("save-07",), None, None, True),
}
CALIBRATION_IDS = frozenset(("p0", "p1", "m0", "m1"))
EVALUATION_IDS = frozenset(("i0", "i1", "c0"))


def audit_split(calibration_ids, evaluation_ids):
    calibration_ids = tuple(calibration_ids)
    evaluation_ids = tuple(evaluation_ids)
    if len(set(calibration_ids)) != len(calibration_ids):
        return False, "duplicate_calibration_id"
    if len(set(evaluation_ids)) != len(evaluation_ids):
        return False, "duplicate_evaluation_id"
    if set(calibration_ids) & set(evaluation_ids):
        return False, "outcome_leaked_into_calibration"
    if set(calibration_ids) != CALIBRATION_IDS or set(evaluation_ids) != EVALUATION_IDS:
        return False, "frozen_split_mismatch"
    return True, "accepted"


def independent_post_age(pre_age, repair):
    if repair == "perfect":
        return 0
    if repair == "minimal":
        return pre_age
    if repair == "imperfect":
        return max(0, pre_age - 1)
    raise ValueError("unknown repair scope")


def independent_risk(age):
    return 0.1 + 0.2 * age


def audit(rows):
    by_id = {r.cycle_id: r for r in rows}
    if len(by_id) != len(rows):
        return False, "duplicate_cycle_id"
    if set(by_id) != set(EXPECTED):
        return False, "cycle_manifest_mismatch"
    for cid, expected in EXPECTED.items():
        r = by_id[cid]
        got = (r.fault_class, r.pre_age, r.exposure, r.repair,
               r.required_effects, r.recurrence_u, r.recurrence_exposure, r.censored)
        if got != expected:
            return False, "frozen_input_or_exposure_mismatch"
        post = independent_post_age(r.pre_age, r.repair)
        if r.observed_post_age != post:
            return False, "independent_health_probe_mismatch"
        if r.retained_effects != r.required_effects:
            return False, "required_effect_erased"
        if r.censored:
            if r.observed_recurrence is not None:
                return False, "censored_outcome_filled_in"
        else:
            expected_recurrence = r.recurrence_u < independent_risk(post)
            if r.observed_recurrence != expected_recurrence:
                return False, "recurrence_oracle_mismatch"
    return True, "accepted"
