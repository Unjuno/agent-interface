#!/usr/bin/env python3
"""Audit existing Calc continuation summaries without rewriting their evidence."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
drain = json.loads((ROOT / "runtime/results/calc-final-drain-01/SUMMARY.json").read_text())
settle = json.loads((ROOT / "runtime/results/calc-settle-self-use-01/SUMMARY.json").read_text())

checks = {
    "drain_independent_success": drain.get("independent_success") is True,
    "drain_same_response_final_read": drain.get("extra_model_tool_turn_for_final_read") is False,
    "drain_cleanup": drain.get("server_exit_code") == 0,
    "settle_independent_success": settle.get("independent_success") is True,
    "settle_cleanup": settle.get("server_exit_code") == 0,
    "settle_semantic_completion_not_claimed": all(
        x.get("semantic_completion") == "unknown"
        for x in settle.get("settle_results", [])
    ),
    "settle_has_independent_effect": settle.get("saved_cells_xml") == {"A1": "766", "A2": "761"},
}
out = {
    "checks": checks,
    "passed": sum(checks.values()),
    "total": len(checks),
    "disposition": "PASS_EXISTING_CONTINUATION_EVIDENCE_AUDIT_SCOPED"
        if all(checks.values()) else "HOLD_CONTINUATION_EVIDENCE_AUDIT",
    "integration_boundary": {
        "no_runtime_changes": True,
        "no_model_calls": True,
        "no_new_gui_calls": True,
        "no_token_or_matched_latency_claim": True,
    },
}
print(json.dumps(out, sort_keys=True, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
