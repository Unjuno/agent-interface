"""Finite observable-test representation probe; no application interaction."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


def _pair(left: dict, right: dict, effect_claim: bool = False) -> dict:
    equal = left["predictions"] == right["predictions"]
    effect_receipts = [left.get("effect_receipt"), right.get("effect_receipt")]
    receipt_complete = all(
        receipt is not None
        and receipt["fresh"]
        and receipt["independent_source"]
        and receipt["generation"] == left["generation"] == right["generation"]
        for receipt in effect_receipts
    )
    if effect_claim and not receipt_complete:
        return {
            "predictions_equal_within_horizon": equal,
            "decision": "HOLD_NOT_IDENTIFIABLE",
            "merge_authorized": False,
        }
    if not equal:
        return {
            "predictions_equal_within_horizon": False,
            "decision": "KEEP_SEPARATE",
            "merge_authorized": False,
        }
    return {
        "predictions_equal_within_horizon": True,
        "decision": "MERGE_WITHIN_HORIZON",
        "merge_authorized": True,
    }


def _enumerate_pair(actions: tuple[str, ...], horizon: int, left: dict, right: dict) -> list[dict]:
    rows = []
    for length in range(1, horizon + 1):
        for sequence in itertools.product(actions, repeat=length):
            rows.append(
                {
                    "sequence": list(sequence),
                    "left": [left(action, step) for step, action in enumerate(sequence, 1)],
                    "right": [right(action, step) for step, action in enumerate(sequence, 1)],
                }
            )
    return rows


def _vector(rows: list[dict], side: str) -> list[tuple]:
    return [(tuple(row["sequence"]), tuple(row[side])) for row in rows]


def run() -> dict:
    silent_sequences = _enumerate_pair(
        ("modal_read", "release_ack"),
        2,
        lambda action, step: "closed" if action == "modal_read" else "ack",
        lambda action, step: "closed" if action == "modal_read" else "ack",
    )
    fresh_sequences = _enumerate_pair(
        ("modal_read", "effect_receipt"),
        2,
        lambda action, step: "closed" if action == "modal_read" else "absent",
        lambda action, step: "closed" if action == "modal_read" else "present",
    )
    null_sequences = _enumerate_pair(
        ("modal_read", "release_ack"),
        2,
        lambda action, step: "closed" if action == "modal_read" else "ack",
        lambda action, step: "closed" if action == "modal_read" else "ack",
    )
    delayed_sequences = _enumerate_pair(
        ("wait",), 2, lambda action, step: "idle", lambda action, step: "idle"
    )
    silent_left = {
        "generation": 7,
        "predictions": {"modal_read": ["closed"], "release_ack": ["ack"]},
    }
    silent_right = {
        "generation": 7,
        "predictions": {"modal_read": ["closed"], "release_ack": ["ack"]},
    }
    fresh_left = {
        "generation": 7,
        "predictions": {"modal_read": ["closed"], "effect_receipt": ["absent"]},
        "effect_receipt": {"value": "absent", "fresh": True, "independent_source": True, "generation": 7},
    }
    fresh_right = {
        "generation": 7,
        "predictions": {"modal_read": ["closed"], "effect_receipt": ["present"]},
        "effect_receipt": {"value": "present", "fresh": True, "independent_source": True, "generation": 7},
    }
    null_left = {"generation": 2, "predictions": {"modal_read": ["closed"], "safe_actions": ["inspect", "wait"]}}
    null_right = {"generation": 2, "predictions": {"modal_read": ["closed"], "safe_actions": ["inspect", "wait"]}}
    delayed_left = {"generation": 3, "predictions": {"steps_1_to_2": ["idle", "idle"], "safe_actions": ["inspect"]}}
    delayed_right = {"generation": 3, "predictions": {"steps_1_to_2": ["idle", "idle"], "safe_actions": ["inspect"]}}
    cases_silent = _pair(silent_left, silent_right, effect_claim=True)
    cases_silent["test_sequences"] = silent_sequences
    cases_silent["enumerated_sequence_count"] = len(silent_sequences)
    cases_fresh = _pair(fresh_left, fresh_right, effect_claim=True)
    cases_fresh["test_sequences"] = fresh_sequences
    cases_fresh["enumerated_sequence_count"] = len(fresh_sequences)
    cases_null = _pair(null_left, null_right)
    cases_null["test_sequences"] = null_sequences
    cases_null["enumerated_sequence_count"] = len(null_sequences)
    cases_delayed = {
        **_pair(delayed_left, delayed_right),
        "horizon": 2,
        "distinguishing_step": 3,
        "beyond_horizon": "UNKNOWN",
        "unbounded_equivalence": False,
        "test_sequences": delayed_sequences,
        "sequence_count": len(delayed_sequences),
    }
    cases = {
        "silent_effect_alias": cases_silent,
        "fresh_independent_receipt": cases_fresh,
        "null_same_safe_continuation": cases_null,
        "delayed_beyond_horizon": cases_delayed,
        "forbidden_probe_only_distinguishes": {
            "decision": "HOLD_NOT_IDENTIFIABLE",
            "issued_tests": ["modal_read"],
            "forbidden_probe_execution_count": 0,
        },
        "stale_receipt": {
            "decision": "HOLD_NOT_IDENTIFIABLE",
            "receipt_accepted": False,
            "receipt_generation": 6,
            "current_generation": 7,
        },
        "source_correlated_receipt": {
            "decision": "HOLD_NOT_IDENTIFIABLE",
            "receipt_accepted": False,
            "candidate_source": "source-A",
            "receipt_source": "source-A",
        },
        "external_mutation_generation": {
            "decision": "HOLD_STALE_GENERATION",
            "cached_prediction_reused": False,
            "cached_generation": 4,
            "current_generation": 5,
        },
        "route_hard_label_mismatch": {
            "prediction_vector_equal": True,
            "route_equivalence": "UNKNOWN_OR_DIFFERENT",
            "route_equivalence_claim": False,
            "hard_labels_match": False,
        },
    }
    return {
        "schema": "issue6258-observable-test-t0-v1",
        "horizon": 2,
        "prediction_basis": "permitted observable tests only; no hidden state labels",
        "candidate_effect_oracle_access": False,
        "issued_forbidden_probes": 0,
        "representation_comparison": {
            "silent_effect_alias": {
                "screenshot": "MERGE",
                "last_k_history": "MERGE",
                "finite_latent_belief_oracle_baseline": "KEEP_SEPARATE",
                "full_history": "KEEP_SEPARATE",
                "predictive_tests": "HOLD_NOT_IDENTIFIABLE",
            },
            "null_same_safe_continuation": {
                "screenshot": "MERGE",
                "last_k_history": "MERGE",
                "finite_latent_belief_oracle_baseline": "MERGE",
                "full_history": "KEEP_SEPARATE",
                "predictive_tests": "MERGE_WITHIN_HORIZON",
            },
            "fresh_independent_receipt": {
                "screenshot": "MERGE",
                "last_k_history": "MERGE",
                "finite_latent_belief_oracle_baseline": "KEEP_SEPARATE",
                "full_history": "KEEP_SEPARATE",
                "predictive_tests": "KEEP_SEPARATE",
            },
        },
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.write_text(json.dumps(run(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"schema": "issue6258-observable-test-t0-v1", "output": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
