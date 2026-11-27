"""Offline audit of P09 raw outcomes, amendments, and paired estimates."""
import hashlib
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(REPO / "research" / "integration" / "standard_mcp_task_ledger_57_v1"))
from provider_attempt_recorder import ProviderAttemptRecorder
ARMS = ("direct_public_input", "compiled_public_caller")
PAIRS = ("p01", "p02", "p03")

def sha(data):
    return hashlib.sha256(data).hexdigest()

def audit():
    cells = {}
    for pair in PAIRS:
        for arm in ARMS:
            key = f"{pair}-{arm}"
            run = ROOT / "run" / key
            result = json.loads((run / "RESULT.json").read_text(encoding="utf-8"))
            supplemental = json.loads((run / "SUPPLEMENTAL-SCORE.json").read_text(encoding="utf-8"))
            provider = json.loads((run / "provider-call" / "result.json").read_text(encoding="utf-8"))
            ledger_path = run / "LEDGER-RECONCILED.json"
            ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.is_file() else None
            try:
                ProviderAttemptRecorder(run / "ledger").reconcile()
                raw_ledger_error = None
            except Exception as error:
                raw_ledger_error = f"{type(error).__name__}: {error}"
            redactions = json.loads((run / "REDACTIONS.json").read_text(encoding="utf-8"))
            manifest_ok = True
            manifest_rows = []
            for line in (run / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
                digest, rel = line.split("  ", 1)
                actual = sha((run / Path(rel)).read_bytes())
                manifest_rows.append(actual == digest)
                manifest_ok = manifest_ok and actual == digest
            provider_usage = provider.get("usage", {})
            result_usage = result.get("provider_usage")
            usage_match = result_usage is None or all(
                result_usage.get(field) == provider_usage.get(field)
                for field in ("input_tokens", "output_tokens", "reasoning_output_tokens"))
            cells[key] = {
                "independent_effect_and_release_pass": supplemental.get("independent_task_success_from_retained_evidence") is True,
                "supplemental_checks": supplemental.get("checks"),
                "original_result_classification": result.get("classification"),
                "original_result_independent_score": result.get("independent_task_success"),
                "runner_result_classified_pass": result.get("classification") == "PASS_MODEL_GROUNDED_PUBLIC_MCP_FAKE_X_ONLY",
                "provider_usage_reported": provider.get("turn_status") == "completed" and all(type(provider_usage.get(k)) is int for k in ("input_tokens", "output_tokens", "reasoning_output_tokens")),
                "provider_result_matches_terminal_usage_when_present": usage_match,
                "ledger_reconciled": ledger is not None and ledger.get("complete") is True,
                "provider_attempt_raw_hash_reconciliation_error": raw_ledger_error,
                "stored_manifest_matches_redacted_files": bool(manifest_rows) and manifest_ok,
                "redactions_have_before_after_hashes": all(row.get("original_sha256") and row.get("redacted_sha256") for row in redactions.get("redactions", [])),
                "usage": provider_usage,
                "provider_turn_ms": supplemental.get("provider_turn_ms"),
                "observation_to_action_return_ms": supplemental.get("observation_to_action_return_ms"),
                "total_trial_ms": supplemental.get("total_trial_ms"),
                "tool_call_count": result.get("public_tool_call_count"),
                "compiled_transition_count": result.get("compiled_transition_count"),
            }
    paired = {}
    metric_fields = ("provider_turn_ms", "observation_to_action_return_ms", "total_trial_ms")
    usage_fields = ("input_tokens", "output_tokens", "reasoning_output_tokens")
    for pair in PAIRS:
        direct = cells[f"{pair}-direct_public_input"]
        compiled = cells[f"{pair}-compiled_public_caller"]
        paired[pair] = {}
        for metric in metric_fields:
            a, b = direct[metric], compiled[metric]
            paired[pair][metric + "_direct_minus_compiled"] = (a-b) if a is not None and b is not None else None
        for metric in usage_fields:
            a, b = direct["usage"].get(metric), compiled["usage"].get(metric)
            paired[pair][metric + "_direct_minus_compiled"] = (a-b) if type(a) is int and type(b) is int else None
    delta_fields = sorted({field for row in paired.values() for field in row})
    medians = {field: statistics.median(values) if values else None for field in delta_fields
               for values in [[row[field] for row in paired.values() if row[field] is not None]]}
    amendment_files = sorted(ROOT.glob("AMENDMENT-*.json"))
    amendments = [json.loads(path.read_text(encoding="utf-8")) for path in amendment_files]
    sanitization = json.loads((ROOT / "SANITIZATION-POSTHOC.json").read_text(encoding="utf-8"))
    sanitization_matches = all(
        row.get("after_sha256") == sha((ROOT / row["path"]).read_bytes())
        for row in sanitization.get("replacements", []))
    effect_passes = sum(row["independent_effect_and_release_pass"] for row in cells.values())
    ledger_passes = sum(row["provider_attempt_raw_hash_reconciliation_error"] is None for row in cells.values())
    audit = {
        "schema": "agent-interface/appserver-matched-efficiency-p09-audit-v2",
        "classification": "FAIL_PREREGISTERED_RAW_CUSTODY_REQUIREMENT" if effect_passes == 6 and all(row["provider_usage_reported"] for row in cells.values()) else "FAIL_OR_HOLD",
        "cells": cells,
        "paired_differences_direct_minus_compiled": paired,
        "paired_medians_direct_minus_compiled": medians,
        "counts": {"trial_cells":6,"independent_effect_and_verified_release":effect_passes,"provider_usage_reported":sum(row["provider_usage_reported"] for row in cells.values()),"runner_result_pass":sum(row["runner_result_classified_pass"] for row in cells.values()),"complete_ledgers_at_run_end":sum(row["ledger_reconciled"] for row in cells.values()),"provider_attempt_raw_hash_reconciliation_pass":ledger_passes},
        "amendments": amendments,
        "posthoc_path_sanitization_hashes_match_current_files": sanitization_matches,
        "scope": "three counterbalanced paired samples on synthetic Fake X; descriptive only; no live GUI, blocked-I/O, MAP01, or WSLc claim",
        "privacy_and_integrity_limit": "SHA256SUMS validates stored post-redaction files, and REDACTIONS records pre/post digests. ProviderAttemptRecorder reconciliation finds raw-response digest mismatches after the redactor rewrote JSON-like .bin files. Original unredacted raw bytes cannot be reconstructed from hashes. Treat full raw-ledger custody and token-to-ledger reconciliation as unverified.",
        "wslc_used":False,"docker_used":False,"physical_input":False,
    }
    (ROOT / "AUDIT.json").write_text(json.dumps(audit,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    return audit

if __name__ == "__main__":
    result=audit();print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result["classification"].startswith("PASS_SCOPED") else 1)
