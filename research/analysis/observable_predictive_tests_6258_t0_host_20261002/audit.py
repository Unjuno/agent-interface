"""Independent finite-deck checker. Deliberately does not import candidate.py."""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path


EXPECTED = {
    "silent_effect_alias": {
        "predictions_equal_within_horizon": True,
        "decision": "HOLD_NOT_IDENTIFIABLE",
        "merge_authorized": False,
    },
    "fresh_independent_receipt": {
        "predictions_equal_within_horizon": False,
        "decision": "KEEP_SEPARATE",
        "merge_authorized": False,
    },
    "null_same_safe_continuation": {
        "predictions_equal_within_horizon": True,
        "decision": "MERGE_WITHIN_HORIZON",
        "merge_authorized": True,
    },
    "delayed_beyond_horizon": {
        "predictions_equal_within_horizon": True,
        "decision": "MERGE_WITHIN_HORIZON",
        "horizon": 2,
        "distinguishing_step": 3,
        "beyond_horizon": "UNKNOWN",
        "unbounded_equivalence": False,
    },
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


ORACLE_SAFE_ACTIONS = {
    "silent_effect_alias": ({"inspect", "save"}, {"inspect"}),
    "fresh_independent_receipt": ({"inspect", "save"}, {"inspect"}),
    "null_same_safe_continuation": ({"inspect", "wait"}, {"inspect", "wait"}),
    "delayed_beyond_horizon": ({"inspect"}, {"inspect"}),
}


def _oracle_outputs(case_name: str, side: str, sequence: tuple[str, ...]) -> list[str]:
    outputs = []
    for step, action in enumerate(sequence, 1):
        if case_name in {"silent_effect_alias", "null_same_safe_continuation"}:
            outputs.append("closed" if action == "modal_read" else "ack")
        elif case_name == "fresh_independent_receipt":
            if action == "modal_read":
                outputs.append("closed")
            else:
                outputs.append("absent" if side == "left" else "present")
        elif case_name == "delayed_beyond_horizon":
            outputs.append("idle" if step <= 2 else ("no_modal" if side == "left" else "modal"))
    return outputs


def _oracle_sequences(case_name: str) -> list[dict]:
    actions = {
        "silent_effect_alias": ("modal_read", "release_ack"),
        "fresh_independent_receipt": ("modal_read", "effect_receipt"),
        "null_same_safe_continuation": ("modal_read", "release_ack"),
        "delayed_beyond_horizon": ("wait",),
    }[case_name]
    max_length = 2
    rows = []
    for length in range(1, max_length + 1):
        for sequence in itertools.product(actions, repeat=length):
            rows.append(
                {
                    "sequence": list(sequence),
                    "left": _oracle_outputs(case_name, "left", sequence),
                    "right": _oracle_outputs(case_name, "right", sequence),
                }
            )
    return rows


def audit(raw: dict) -> dict:
    errors = []
    if raw.get("schema") != "issue6258-observable-test-t0-v1":
        errors.append("schema_mismatch")
    if raw.get("horizon") != 2:
        errors.append("horizon_mismatch")
    if raw.get("candidate_effect_oracle_access") is not False:
        errors.append("candidate_oracle_leakage")
    if raw.get("issued_forbidden_probes") != 0:
        errors.append("forbidden_probe_was_issued")
    rows = raw.get("cases")
    if not isinstance(rows, dict) or set(rows) != set(EXPECTED):
        errors.append("case_set_mismatch")
    if isinstance(rows, dict):
        for case_name, expected_fields in EXPECTED.items():
            row = rows.get(case_name)
            if not isinstance(row, dict):
                continue
            for key, expected in expected_fields.items():
                if row.get(key) != expected:
                    errors.append(f"{case_name}:{key}:expected_{expected!r}_got_{row.get(key)!r}")
    replayed = 0
    if isinstance(rows, dict):
        for case_name in ORACLE_SAFE_ACTIONS:
            row = rows.get(case_name)
            if not isinstance(row, dict):
                continue
            expected_sequences = _oracle_sequences(case_name)
            replayed += sum(len(item["sequence"]) * 2 for item in expected_sequences)
            if row.get("test_sequences") != expected_sequences:
                errors.append(f"{case_name}:oracle_sequence_replay_mismatch")
            if case_name != "delayed_beyond_horizon" and row.get("enumerated_sequence_count") != len(expected_sequences):
                errors.append(f"{case_name}:sequence_count_mismatch")
            if case_name == "delayed_beyond_horizon" and row.get("sequence_count") != len(expected_sequences):
                errors.append("delayed_beyond_horizon:sequence_count_mismatch")
            left_safe, right_safe = ORACLE_SAFE_ACTIONS[case_name]
            same_safe_set = left_safe == right_safe
            merge = row.get("merge_authorized") is True
            if merge and not same_safe_set:
                errors.append(f"{case_name}:unsafe_merge_against_independent_safe_action_oracle")
            if case_name == "null_same_safe_continuation" and (not same_safe_set or not merge):
                errors.append("null_case_safe_merge_not_preserved")
            if case_name == "silent_effect_alias" and (same_safe_set or merge):
                errors.append("silent_effect_alias_not_conservatively_held")
            if case_name == "delayed_beyond_horizon" and row.get("unbounded_equivalence") is not False:
                errors.append("delayed_case_overclaims_beyond_horizon")
    return {
        "schema": "issue6258-independent-audit-v1",
        "disposition": "PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT",
        "checked_cases": len(EXPECTED),
        "oracle_transitions_replayed": replayed,
        "oracle_mismatches": [error for error in errors if "oracle_" in error or "sequence" in error],
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = audit(json.loads(Path(args.raw_json).read_text(encoding="utf-8")))
    Path(args.output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"schema": result["schema"], "disposition": result["disposition"], "errors": result["errors"]}))
    return 0 if result["disposition"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
