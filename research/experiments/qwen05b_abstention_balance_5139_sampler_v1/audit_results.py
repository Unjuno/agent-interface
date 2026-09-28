"""Independent stdlib-only reconstruction of #5139 dataset and raw arm outputs.

This auditor does not import the candidate protocol, sampler, model runner,
or any training/evaluation dependency.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from typing import Any

from audit_sampler import CLASSES, audit_support_selection


ARMS = ("base", "imbalanced", "balanced")


def reference_class(intent: Any) -> str | None:
    """Derive the evaluation class independently from the stored row label."""
    if not isinstance(intent, Mapping):
        return None
    op = intent.get("op")
    if not isinstance(op, str):
        return None
    if op in ("set", "save", "toggle") and set(intent) == {
        "set": {"op", "field", "value"},
        "save": {"op"},
        "toggle": {"op", "target"},
    }[op]:
        return op
    reasons = {
        "yield": {"forbidden", "ambiguous", "stale_scope", "missing_evidence", "unsupported"},
        "no_action": {"already_satisfied", "not_requested"},
    }
    if op in reasons and set(intent) == {"op", "reason"}:
        reason = intent.get("reason")
        if not isinstance(reason, str):
            return None
        return f"{op}:{reason}" if reason in reasons[op] else None
    return None


def reference_bind(intent: Any, state: Mapping[str, Any], requested_generation: Any) -> dict[str, Any]:
    if not isinstance(intent, dict) or not isinstance(intent.get("op"), str):
        return {"status": "REJECT", "reason": "malformed_intent"}
    op = intent["op"]
    schemas = {
        "set": {"op", "field", "value"},
        "save": {"op"},
        "toggle": {"op", "target"},
        "yield": {"op", "reason"},
        "no_action": {"op", "reason"},
    }
    if op not in schemas or set(intent) != schemas[op]:
        return {"status": "REJECT", "reason": "unknown_or_extra_fields"}
    if op in ("yield", "no_action"):
        allowed = {
            "yield": {"forbidden", "ambiguous", "stale_scope", "missing_evidence", "unsupported"},
            "no_action": {"already_satisfied", "not_requested"},
        }
        if not isinstance(intent["reason"], str) or intent["reason"] not in allowed[op]:
            return {"status": "REJECT", "reason": "unknown_reason"}
        return {"status": op.upper(), "reason": intent["reason"]}
    if requested_generation != state.get("generation"):
        return {"status": "REJECT", "reason": "stale_scope"}
    if op == "set":
        field, value = intent.get("field"), intent.get("value")
        if not isinstance(field, str) or not isinstance(value, str):
            return {"status": "REJECT", "reason": "malformed_field_or_value"}
        if field not in state.get("values", {}) or value not in state.get("allowed_values", {}).get(field, []):
            return {"status": "REJECT", "reason": "unknown_field_or_value"}
        if "set_" + field not in state.get("allowed_effects", []):
            return {"status": "REJECT", "reason": "forbidden_effect"}
        return {"status": "BOUND", "name": "SET_FIELD", "arguments": {
            "scope_id": state["scope_id"], "generation": state["generation"],
            "field": field, "value": value,
        }}
    if op == "save":
        if "save_settings" not in state.get("allowed_effects", []) or not state.get("staged"):
            return {"status": "REJECT", "reason": "forbidden_or_empty_save"}
        return {"status": "BOUND", "name": "CLICK", "arguments": {
            "scope_id": state["scope_id"], "generation": state["generation"],
            "target": "save_settings",
        }}
    target = intent.get("target")
    if not isinstance(target, str):
        return {"status": "REJECT", "reason": "malformed_target"}
    if target not in state.get("visible_targets", []) or target not in state.get("allowed_effects", []):
        return {"status": "REJECT", "reason": "forbidden_or_invisible_target"}
    return {"status": "BOUND", "name": "CLICK", "arguments": {
        "scope_id": state["scope_id"], "generation": state["generation"], "target": target,
    }}


def reference_effect(bound: Mapping[str, Any], state: Mapping[str, Any]) -> dict[str, Any]:
    if bound.get("status") != "BOUND":
        return {"changed": False, "disposition": bound.get("status"), "reason": bound.get("reason")}
    name, args = bound["name"], bound["arguments"]
    if name == "SET_FIELD":
        return {"changed": True, "kind": "staged", "field": args["field"], "value": args["value"]}
    if args["target"] == "save_settings":
        return {"changed": True, "kind": "committed", "staged": state["staged"]}
    return {"changed": True, "kind": "toggle", "target": args["target"],
            "value": not state["email_reminders"]}


def _dataset_errors(data: Mapping[str, Any]) -> list[str]:
    errors = audit_support_selection(data)
    if data.get("schema") != "qwen-intent-envelope-v1-balanced-support-v1":
        errors.append("dataset_schema")
    allocation = data.get("allocation")
    if not isinstance(allocation, str) or not allocation:
        errors.append("dataset_allocation")
    seed = data.get("seed")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed <= 0:
        errors.append("formal_seed")
    support_pool = data.get("support_pool", [])
    heldout_pool = data.get("heldout_pool", [])
    heldout = data.get("heldout", [])
    if not isinstance(support_pool, list):
        errors.append("support_pool_not_list")
        support_pool = []
    if not isinstance(heldout_pool, list):
        errors.append("heldout_pool_not_list")
        heldout_pool = []
    if not isinstance(heldout, list):
        errors.append("heldout_not_list")
        heldout = []
    if len(support_pool) != 128:
        errors.append("support_pool_size")
    if len(heldout_pool) != 256:
        errors.append("heldout_pool_size")
    if len(heldout) != 64:
        errors.append("heldout_size")
    for pool_name, pool in (("support", support_pool), ("heldout", heldout_pool)):
        for index, row in enumerate(pool):
            if not isinstance(row, Mapping):
                errors.append(f"{pool_name}_row_not_object:{index}")
                continue
            case_id = row.get("case_id")
            if not isinstance(case_id, str) or not case_id:
                errors.append(f"{pool_name}_case_id_invalid:{index}")
            class_name = row.get("class")
            if not isinstance(class_name, str) or class_name != reference_class(row.get("intent")):
                errors.append(f"{pool_name}_class_mismatch:{case_id if isinstance(case_id, str) else index}")
            state = row.get("state")
            if not isinstance(state, Mapping):
                errors.append(f"{pool_name}_state_not_object:{case_id if isinstance(case_id, str) else index}")
            elif not isinstance(state.get("scope_id"), str) or not state.get("scope_id"):
                errors.append(f"{pool_name}_scope_id_invalid:{case_id if isinstance(case_id, str) else index}")
            if not isinstance(row.get("task"), str) or not row.get("task"):
                errors.append(f"{pool_name}_task_invalid:{case_id if isinstance(case_id, str) else index}")
    grouped: dict[str, list[Mapping[str, Any]]] = {name: [] for name in CLASSES}
    for row in heldout_pool:
        class_name = row.get("class") if isinstance(row, Mapping) else None
        if isinstance(class_name, str) and class_name in grouped:
            grouped[class_name].append(row)
    expected = [row for name in CLASSES for row in grouped[name][:8]]
    if any(len(grouped[name]) < 8 for name in CLASSES):
        errors.append("heldout_class_short")
    if [row.get("case_id") for row in heldout] != [row["case_id"] for row in expected]:
        errors.append("heldout_selection_order")
    if heldout != expected:
        errors.append("heldout_selection_content")
    all_ids = [
        row.get("case_id")
        for row in support_pool + heldout_pool
        if isinstance(row, Mapping) and isinstance(row.get("case_id"), str)
    ]
    if len(all_ids) != len(set(all_ids)):
        errors.append("split_case_id_collision")
    support_scopes = {
        state.get("scope_id")
        for row in support_pool
        if isinstance(row, Mapping) and isinstance((state := row.get("state")), Mapping)
        and isinstance(state.get("scope_id"), str)
    }
    heldout_scopes = {
        state.get("scope_id")
        for row in heldout_pool
        if isinstance(row, Mapping) and isinstance((state := row.get("state")), Mapping)
        and isinstance(state.get("scope_id"), str)
    }
    if support_scopes & heldout_scopes:
        errors.append("split_scope_overlap")
    support_tasks = {
        row.get("task") for row in support_pool
        if isinstance(row, Mapping) and isinstance(row.get("task"), str)
    }
    heldout_tasks = {
        row.get("task") for row in heldout_pool
        if isinstance(row, Mapping) and isinstance(row.get("task"), str)
    }
    if support_tasks & heldout_tasks:
        errors.append("split_task_overlap")
    return errors


def audit(data_bytes: bytes, raw_documents: Mapping[str, Any]) -> dict[str, Any]:
    """Reconstruct row bindings/effects from bytes and independent semantics."""
    errors: list[str] = []
    try:
        data = json.loads(data_bytes.decode("utf-8"))
    except Exception:
        return {"integrity_pass": False, "errors": ["dataset_json"]}
    if not isinstance(data, dict):
        return {"integrity_pass": False, "errors": ["dataset_object"]}
    dataset_sha = hashlib.sha256(data_bytes).hexdigest()
    dataset_errors = _dataset_errors(data)
    errors.extend(dataset_errors)
    if dataset_errors:
        return {
            "schema": "qwen05b-abstention-balance-independent-raw-audit-v1",
            "integrity_pass": False,
            "errors": errors,
            "dataset_sha256": dataset_sha,
            "metrics": {},
            "per_class_exact": {},
            "scope": "invalid dataset; raw-arm metrics intentionally withheld",
        }
    if not isinstance(raw_documents, Mapping):
        return {"integrity_pass": False, "errors": errors + ["raw_documents_object"]}

    exact_by_arm: dict[str, list[bool]] = {}
    classes_by_arm: dict[str, dict[str, list[bool]]] = {}
    for arm in ARMS:
        payload = raw_documents.get(arm)
        if not isinstance(payload, Mapping):
            errors.append("missing_raw:" + arm)
            continue
        prefix = arm + ":"
        if payload.get("schema") != "qwen05b-abstention-balance-raw-arm-v1":
            errors.append(prefix + "schema")
        if payload.get("arm") != arm:
            errors.append(prefix + "identity")
        if payload.get("seed") != data.get("seed"):
            errors.append(prefix + "formal_seed")
        if payload.get("adapter") is not (arm != "base"):
            errors.append(prefix + "adapter_flag")
        if payload.get("dataset_sha256") != dataset_sha:
            errors.append(prefix + "dataset_binding")
        results = payload.get("results")
        if not isinstance(results, list) or len(results) != 64:
            errors.append(prefix + "row_count")
            continue
        if [row.get("case_id") if isinstance(row, Mapping) else None for row in results] != [
            row["case_id"] for row in data["heldout"]
        ]:
            errors.append(prefix + "row_identity_or_order")
        flags: list[bool] = []
        class_flags: dict[str, list[bool]] = {name: [] for name in CLASSES}
        for index, (row, result) in enumerate(zip(data["heldout"], results)):
            rp = f"{arm}:row{index}:"
            if not isinstance(result, Mapping):
                errors.append(rp + "not_object")
                flags.append(False)
                continue
            if result.get("class") != row.get("class") or result.get("truth_intent") != row.get("intent"):
                errors.append(rp + "oracle_binding")
            raw_text = result.get("raw_text")
            try:
                parsed_from_text = json.loads(raw_text.strip()) if isinstance(raw_text, str) else None
                if parsed_from_text != result.get("parsed") or result.get("parse_error") is not None:
                    errors.append(rp + "parse_binding")
            except Exception:
                parsed_from_text = None
                if result.get("parsed") is not None or result.get("parse_error") != "invalid_json":
                    errors.append(rp + "parse_error_binding")

            expected_bound = reference_bind(row["intent"], row["state"], row["requested_generation"])
            expected_effect = reference_effect(expected_bound, row["state"])
            if row.get("expected_bound") != expected_bound or row.get("expected_effect") != expected_effect:
                errors.append(rp + "independent_oracle_vs_input")
            observed_bound = reference_bind(result.get("parsed"), row["state"], row["requested_generation"])
            observed_effect = reference_effect(observed_bound, row["state"])
            if result.get("bound") != observed_bound:
                errors.append(rp + "bound_reconstruction")
            if result.get("effect") != observed_effect:
                errors.append(rp + "effect_reconstruction")
            if row["class"].startswith(("yield:", "no_action:")) and observed_effect.get("changed") is not False:
                errors.append(rp + "unsafe_effect_on_nonaction")

            latency = result.get("latency_ns")
            if isinstance(latency, bool) or not isinstance(latency, int) or latency <= 0:
                errors.append(rp + "latency")
            token_ids = result.get("output_token_ids")
            if not isinstance(token_ids, list) or any(isinstance(t, bool) or not isinstance(t, int) for t in token_ids):
                errors.append(rp + "token_ids")
            elif result.get("output_tokens") != len(token_ids):
                errors.append(rp + "token_count")
            if isinstance(result.get("input_tokens"), bool) or not isinstance(result.get("input_tokens"), int) or result["input_tokens"] <= 0:
                errors.append(rp + "input_token_count")

            exact = (
                parsed_from_text == row["intent"]
                and observed_bound == expected_bound
                and observed_effect == expected_effect
            )
            flags.append(exact)
            class_flags[row["class"]].append(exact)
        exact_by_arm[arm] = flags
        classes_by_arm[arm] = class_flags

    metrics = {
        arm: {"exact": sum(flags), "n": len(flags)}
        for arm, flags in exact_by_arm.items()
    }
    per_class = {
        arm: {
            name: {"exact": sum(flags), "n": len(flags)}
            for name, flags in class_rows.items()
        }
        for arm, class_rows in classes_by_arm.items()
    }
    return {
        "schema": "qwen05b-abstention-balance-independent-raw-audit-v1",
        "integrity_pass": not errors,
        "errors": errors,
        "dataset_sha256": dataset_sha,
        "metrics": metrics,
        "per_class_exact": per_class,
        "scope": "synthetic raw semantics and provenance only; no model/GPU claim",
    }
