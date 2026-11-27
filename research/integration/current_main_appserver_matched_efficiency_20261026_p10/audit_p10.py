"""Offline private-raw audit and paired descriptive summaries for P10."""

import argparse
import hashlib
import json
import statistics
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(REPO / "research" / "integration" / "standard_mcp_task_ledger_57_v1"))
from provider_attempt_recorder import ProviderAttemptRecorder

ARMS = ("direct_public_input", "compiled_public_caller")
PAIRS = ("p01", "p02", "p03")
USAGE_FIELDS = ("input_tokens", "output_tokens", "reasoning_output_tokens")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def protocol_usage(path, thread_id, turn_id):
    updates = []
    completed = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        message = row.get("message", {})
        params = message.get("params", {}) if isinstance(message, dict) else {}
        if (row.get("direction") == "received" and
                message.get("method") == "thread/tokenUsage/updated" and
                params.get("threadId") == thread_id and params.get("turnId") == turn_id):
            updates.append(params.get("tokenUsage", {}).get("last", {}))
        if (row.get("direction") == "received" and
                message.get("method") == "turn/completed" and
                params.get("threadId") == thread_id and
                params.get("turn", {}).get("id") == turn_id):
            completed.append(params.get("turn", {}).get("status"))
    mapping = {
        "input_tokens": "inputTokens",
        "output_tokens": "outputTokens",
        "reasoning_output_tokens": "reasoningOutputTokens",
    }
    usage = None if not updates else {
        field: updates[-1].get(protocol_field)
        for field, protocol_field in mapping.items()
    }
    return usage, completed


def audit(raw_root):
    raw_root = Path(raw_root).resolve()
    cells = {}
    for pair in PAIRS:
        for arm in ARMS:
            key = f"{pair}-{arm}"
            run = raw_root / key
            result = read_json(run / "RESULT.json")
            manifest = read_json(run / "RAW-SHA256.json")
            manifest_rows = manifest.get("files", [])
            listed = {row["path"]: row for row in manifest_rows}
            actual_paths = {
                path.relative_to(run).as_posix(): path
                for path in run.rglob("*")
                if path.is_file() and path.name != "RAW-SHA256.json"
            }
            manifest_ok = set(listed) == set(actual_paths)
            if manifest_ok:
                manifest_ok = all(
                    actual_paths[rel].stat().st_size == row["bytes"] and
                    sha(actual_paths[rel].read_bytes()) == row["sha256"]
                    for rel, row in listed.items())

            reconcile_error = None
            ledger = None
            try:
                ledger = ProviderAttemptRecorder(run / "ledger").reconcile()
            except Exception as error:
                reconcile_error = f"{type(error).__name__}: {error}"

            provider = read_json(run / "provider-call" / "result.json")
            provider_usage = provider.get("usage", {})
            terminal_usage = result.get("provider_usage") or {}
            terminal_match = all(
                terminal_usage.get(field) == provider_usage.get(field)
                for field in USAGE_FIELDS)
            ledger_events = (ledger or {}).get("events", [])
            model_events = [row for row in ledger_events if row.get("kind") == "model_attempt"]
            ledger_usage = model_events[0].get("usage", {}) if len(model_events) == 1 else {}
            ledger_match = all(
                ledger_usage.get(field) == provider_usage.get(field)
                for field in USAGE_FIELDS)
            journal_usage, completions = protocol_usage(
                run / "app-server" / "protocol.jsonl",
                provider.get("thread_id"), provider.get("turn_id"))
            protocol_usage_match = (
                journal_usage is not None and len(completions) == 1 and
                completions[0] == "completed" and all(
                    journal_usage.get(field) == provider_usage.get(field)
                    for field in USAGE_FIELDS))
            effect_pass = bool(
                result.get("classification") == "PASS_MODEL_GROUNDED_PUBLIC_MCP_FAKE_X_ONLY" and
                result.get("independent_task_success") is True and
                result.get("release_verified") is True and
                result.get("selected_point_inside_green") is True and
                result.get("owner_click_matches_model_point") is True and
                result.get("owner_button_press_count") == 1 and
                result.get("independent_final_pixel") == [255, 0, 0])
            provider_reported = bool(
                provider.get("turn_status") == "completed" and
                all(type(provider_usage.get(field)) is int for field in USAGE_FIELDS))
            cells[key] = {
                "effect_and_release_pass": effect_pass,
                "original_classification": result.get("classification"),
                "provider_usage_reported": provider_reported,
                "terminal_usage_matches_provider": terminal_match,
                "ledger_usage_matches_provider": ledger_match,
                "protocol_journal_contains_usage_counts": protocol_usage_match,
                "provider_attempt_raw_reconciliation_pass": reconcile_error is None,
                "provider_attempt_raw_reconciliation_error": reconcile_error,
                "ledger_complete": bool(ledger and ledger.get("complete")),
                "private_raw_manifest_pass": manifest_ok,
                "private_raw_manifest_sha256": sha((run / "RAW-SHA256.json").read_bytes()),
                "provider_usage": {field: provider_usage.get(field) for field in USAGE_FIELDS},
                "provider_turn_ms": result.get("provider_turn_ms"),
                "observation_to_action_return_ms": result.get("observation_to_action_return_ms"),
                "total_trial_ms": result.get("total_trial_ms"),
                "public_tool_call_count": result.get("public_tool_call_count"),
                "compiled_transition_count": result.get("compiled_transition_count"),
            }

    paired = {}
    metric_fields = ("provider_turn_ms", "observation_to_action_return_ms", "total_trial_ms")
    for pair in PAIRS:
        direct = cells[f"{pair}-direct_public_input"]
        compiled = cells[f"{pair}-compiled_public_caller"]
        deltas = {}
        for field in metric_fields:
            a, b = direct[field], compiled[field]
            deltas[field + "_direct_minus_compiled"] = (
                a - b if type(a) in (int, float) and type(b) in (int, float) else None)
        for field in USAGE_FIELDS:
            a = direct["provider_usage"].get(field)
            b = compiled["provider_usage"].get(field)
            deltas[field + "_direct_minus_compiled"] = (
                a - b if type(a) is int and type(b) is int else None)
        paired[pair] = deltas
    all_deltas = {key: [row[key] for row in paired.values() if row[key] is not None]
                  for key in next(iter(paired.values()))}
    medians = {key: statistics.median(values) if values else None
               for key, values in all_deltas.items()}
    all_integrity = all(
        row["provider_usage_reported"] and row["terminal_usage_matches_provider"] and
        row["ledger_usage_matches_provider"] and row["protocol_journal_contains_usage_counts"] and
        row["provider_attempt_raw_reconciliation_pass"] and row["ledger_complete"] and
        row["private_raw_manifest_pass"] for row in cells.values())
    all_effects = all(row["effect_and_release_pass"] for row in cells.values())
    result = {
        "schema": "agent-interface/appserver-matched-efficiency-p10-audit-v1",
        "classification": ("PASS_SCOPED_ALL_EFFECTS" if all_integrity and all_effects else
                            "VALID_EVIDENCE_WITH_FIRST_OUTCOME_FAILURES" if all_integrity else
                            "FAIL_OR_HOLD_INTEGRITY"),
        "integrity_pass": all_integrity,
        "all_effect_and_release_trials_pass": all_effects,
        "cells": cells,
        "paired_differences_direct_minus_compiled": paired,
        "paired_medians_direct_minus_compiled": medians,
        "counts": {
            "trial_cells": len(cells),
            "independent_effect_and_verified_release": sum(row["effect_and_release_pass"] for row in cells.values()),
            "provider_usage_reported": sum(row["provider_usage_reported"] for row in cells.values()),
            "raw_attempt_reconciliation": sum(row["provider_attempt_raw_reconciliation_pass"] for row in cells.values()),
            "private_raw_manifest_integrity": sum(row["private_raw_manifest_pass"] for row in cells.values()),
        },
        "scope": "three counterbalanced paired samples on synthetic Fake X; descriptive only; no live GUI, MAP01, WSLc, Docker, physical input, or reliability claim",
        "accounting_limit": "App Server result, protocol journal, and private attempt ledger are reconciled; independent upstream billing/account-level usage is unavailable and not claimed",
        "private_raw_root_used": True,
    }
    (ROOT / "AUDIT-PRIVATE-VALIDATION.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", required=True)
    args = parser.parse_args()
    audited = audit(args.raw_root)
    print(json.dumps(audited, indent=2, sort_keys=True))
    raise SystemExit(0 if audited["integrity_pass"] else 1)
