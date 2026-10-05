"""Independent finite-row oracle for the synthetic Issue #8024 construction."""
from math import ceil


def recompute(calibration, evaluation, alpha):
    expected_kinds = {**{f"e{i}": "recoverable" for i in range(9)},
                      "diverge-0": "diverging", "censored-0": "right_censored",
                      "hard-identity": "identity_loss", "hard-focus": "focus_loss",
                      "hard-lease": "lease_loss",
                      **{f"shift{i}": "recoverable" for i in range(5)}}
    ids = [row.episode_id for row in calibration + evaluation]
    if len(ids) != len(set(ids)):
        return {"accepted": False, "reason": "duplicate_or_leaked_episode_id"}
    if any(row.split != "calibration" for row in calibration):
        return {"accepted": False, "reason": "evaluation_outcome_leaked_into_calibration"}
    if any(row.split != "evaluation" for row in evaluation):
        return {"accepted": False, "reason": "non_evaluation_row_in_test_partition"}
    if {row.episode_id for row in evaluation} != set(expected_kinds):
        return {"accepted": False, "reason": "evaluation_partition_manifest_mismatch"}
    if any(row.kind != expected_kinds[row.episode_id] for row in evaluation):
        return {"accepted": False, "reason": "oracle_label_mutation"}
    if len({row.stratum for row in calibration}) != 1 or any(
           row.hard_event or row.kind != "recoverable" or row.duration is None or
           row.censor_at is not None for row in calibration):
        return {"accepted": False, "reason": "invalid_or_censored_calibration_label"}
    order = sorted(row.duration for row in calibration)
    rank = ceil((len(order) + 1) * (1 - alpha))
    if rank > len(order):
        return {"accepted": False, "reason": "finite_quantile_unavailable"}
    deadline = order[rank - 1]
    rows = []
    for row in evaluation:
        if row.hard_event or row.kind in {"identity_loss", "focus_loss", "lease_loss"}:
            decision = "immediate_yield"
        elif row.stratum != "nominal":
            decision = "uncertified_yield"
        elif row.kind == "recoverable" and row.duration is not None:
            decision = "recovered" if row.duration <= deadline else "deadline_yield"
        elif row.kind in {"diverging", "right_censored"}:
            elapsed = row.censor_at if row.censor_at is not None else deadline
            decision = "deadline_yield" if elapsed >= deadline else "pending"
        else:
            decision = "invalid_episode_yield"
        rows.append((row.episode_id, row.kind, decision))
    recoverable = [row for row in evaluation if row.kind == "recoverable" and
                   row.stratum == "nominal"]
    decisions = {episode_id: decision for episode_id, _, decision in rows}
    covered = sum(decisions[row.episode_id] == "recovered" for row in recoverable)
    hard_delayed = [episode_id for episode_id, kind, decision in rows
                    if kind in {"identity_loss", "focus_loss", "lease_loss"}
                    and decision != "immediate_yield"]
    return {
        "accepted": True,
        "deadline": deadline,
        "rank": rank,
        "calibration_n": len(order),
        "evaluation_n": len(evaluation),
        "right_censored_n": sum(row.kind == "right_censored" for row in evaluation),
        "recoverable_n": len(recoverable),
        "covered_n": covered,
        "coverage": covered / len(recoverable) if recoverable else None,
        "hard_delayed": hard_delayed,
        "shift_uncertified": [row.episode_id for row in evaluation
                              if row.stratum != "nominal"],
        "rows": rows,
    }
