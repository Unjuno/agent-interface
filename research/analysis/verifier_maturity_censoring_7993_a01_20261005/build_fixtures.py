#!/usr/bin/env python3
"""Generate the deterministic, truth-separated Issue #7993 T0 fixtures."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parent
PROTOCOL = "issue-7993-t0-a01-v1"


def make_snapshot(case_id, checkpoint, losses, statuses, model, *, strata=None):
    strata = strata or {row_id: "all" for row_id in losses}
    rows = []
    for row_id, loss in losses.items():
        status = statuses[row_id]
        row = {"row_id": row_id, "stratum": strata[row_id], "status": status}
        if status == "resolved":
            row["loss"] = loss
        rows.append(row)
    return {
        "snapshot_id": f"{case_id}@{checkpoint}",
        "case_id": case_id,
        "checkpoint": checkpoint,
        "model": model,
        "rows": rows,
    }


def make_oracle(snapshot, losses, mechanism, *, enum_group=None, probability="1"):
    return {
        "snapshot_id": snapshot["snapshot_id"],
        "loss_by_row": losses,
        "full_cohort_risk": f"{sum(losses.values())}/{len(losses)}",
        "mechanism": mechanism,
        "mechanism_matches_declared_model": mechanism == "independent_bernoulli_followup",
        "enumeration_group": enum_group,
        "design_probability": probability,
    }


def main() -> None:
    snapshots = []
    oracles = []

    def add(case_id, checkpoint, losses, statuses, model, mechanism, *, strata=None,
            enum_group=None, probability="1"):
        snap = make_snapshot(case_id, checkpoint, losses, statuses, model, strata=strata)
        snapshots.append(snap)
        oracles.append(make_oracle(snap, losses, mechanism, enum_group=enum_group,
                                   probability=probability))

    add(
        "zero_risk_control", "complete",
        {"z1": 0, "z2": 0, "z3": 0, "z4": 0},
        {"z1": "resolved", "z2": "resolved", "z3": "resolved", "z4": "resolved"},
        {"known": True, "independence": "verified", "pi_by_stratum": {"all": "1"}},
        "independent_bernoulli_followup",
    )

    hidden_truth = {"e1": 1, "e2": 0, "e3": 0, "e4": 0}
    hidden_status = {"e1": "pending", "e2": "resolved", "e3": "resolved", "e4": "resolved"}
    add(
        "informative_delay_known_bad", "interim", hidden_truth, hidden_status,
        {"known": True, "independence": "known_violated", "pi_by_stratum": {"all": "1/2"}},
        "outcome_dependent_delay",
    )
    # Observationally identical to mask 1110 in the independent enumeration,
    # but its actual follow-up mechanism depends on the hidden loss label.
    add(
        "informative_delay_hidden_misspecification", "interim", hidden_truth,
        hidden_status,
        {"known": True, "independence": "verified", "pi_by_stratum": {"all": "1/2"}},
        "outcome_dependent_delay",
    )

    zero_support_losses = {"e1": 1, "e2": 0, "e3": 0, "e4": 0}
    zero_support_status = {"e1": "pending", "e2": "resolved", "e3": "resolved", "e4": "resolved"}
    zero_support_strata = {"e1": "rare", "e2": "common", "e3": "common", "e4": "common"}
    add(
        "zero_support_error_stratum", "interim", zero_support_losses,
        zero_support_status,
        {"known": True, "independence": "verified",
         "pi_by_stratum": {"rare": "0", "common": "1"}},
        "zero_probability_for_rare_stratum", strata=zero_support_strata,
    )

    delayed_losses = {"e1": 1, "e2": 0, "e3": 0, "e4": 0}
    add(
        "delayed_eventually_resolved", "early", delayed_losses,
        {"e1": "pending", "e2": "resolved", "e3": "resolved", "e4": "resolved"},
        {"known": True, "independence": "not_verified", "pi_by_stratum": {"all": "1/2"}},
        "delayed_then_resolved",
    )
    add(
        "delayed_eventually_resolved", "late", delayed_losses,
        {"e1": "resolved", "e2": "resolved", "e3": "resolved", "e4": "resolved"},
        {"known": True, "independence": "verified", "pi_by_stratum": {"all": "1"}},
        "delayed_then_resolved",
    )

    add(
        "pending_at_horizon", "horizon", delayed_losses,
        {"e1": "pending", "e2": "resolved", "e3": "resolved", "e4": "resolved"},
        {"known": True, "independence": "verified", "pi_by_stratum": {"all": "1/2"}},
        "independent_bernoulli_followup",
    )
    add(
        "safe_terminal_stop", "terminal", delayed_losses,
        {"e1": "safe_terminal_stop", "e2": "resolved", "e3": "resolved", "e4": "resolved"},
        {"known": False, "independence": "not_applicable", "pi_by_stratum": {}},
        "safe_terminal_stop",
    )
    add(
        "permanent_loss_unknown_cause", "horizon", delayed_losses,
        {"e1": "permanent_loss_unknown_cause", "e2": "resolved", "e3": "resolved", "e4": "resolved"},
        {"known": False, "independence": "not_verified", "pi_by_stratum": {}},
        "permanent_loss_unknown_cause",
    )

    # Exact enumeration of all 2^4 independent follow-up masks. The candidate
    # sees labels only for bits set in the mask; each mask has probability 1/16.
    enum_losses = {"e1": 1, "e2": 0, "e3": 0, "e4": 0}
    enum_group = "independent_masks_16"
    for mask in range(16):
        statuses = {
            row_id: ("resolved" if mask & (1 << bit) else "pending")
            for bit, row_id in enumerate(enum_losses)
        }
        add(
            f"independent_mask_{mask:02d}", "interim", enum_losses, statuses,
            {"known": True, "independence": "verified", "pi_by_stratum": {"all": "1/2"}},
            "independent_bernoulli_followup", enum_group=enum_group, probability="1/16",
        )

    candidate = {
        "protocol": PROTOCOL,
        "endpoint": "verifier_claim_contradicted_by_final_oracle",
        "alpha": "1/10",
        "snapshots": snapshots,
    }
    oracle = {"protocol": PROTOCOL, "snapshots": oracles}
    (ROOT / "candidate_input.json").write_text(
        json.dumps(candidate, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "oracle_input.json").write_text(
        json.dumps(oracle, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"candidate_snapshots": len(snapshots), "oracle_snapshots": len(oracles),
                      "independent_masks": 16, "protocol": PROTOCOL}, sort_keys=True))


if __name__ == "__main__":
    main()
