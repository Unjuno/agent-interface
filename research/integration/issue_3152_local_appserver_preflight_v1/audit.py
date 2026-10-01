#!/usr/bin/env python3
"""Independent integrity/scope audit for the retained local app-server probe."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("result", type=Path)
    p.add_argument("codex_exe", type=Path)
    p.add_argument("client_source", type=Path)
    p.add_argument("planner_source", type=Path)
    a = p.parse_args()
    r = json.loads(a.result.read_text(encoding="utf-8"))
    errors: list[str] = []
    if r.get("schema") != "issue3152-local-appserver-preflight-v1":
        errors.append("schema mismatch")
    if r.get("decision") != "RETAINED_LOCAL_APPSERVER_PREFLIGHT_SUMMARY":
        errors.append("decision mismatch")
    if r.get("formal_allocation_count") != 0 or r.get("prospectively_frozen") is not False:
        errors.append("construction/formal scope misreported")
    if digest(a.codex_exe) != r["host_app_server"].get("sha256"):
        errors.append("host executable SHA-256 mismatch")
    for name, path in (("codex_app_server_client_v2.py", a.client_source),
                       ("persistent_planner_adapter_v2.py", a.planner_source)):
        if digest(path) != r["source"].get(name, {}).get("sha256"):
            errors.append(f"{name} SHA-256 mismatch")
    turn = r.get("model_turn", {})
    if not (turn.get("turn_status") == "completed" and
            turn.get("answer_eligible") is True and
            turn.get("answer") == {"probe": True}):
        errors.append("model turn receipt fields disagree")
    usage = turn.get("usage", {})
    if usage.get("input_tokens", 0) + usage.get("output_tokens", 0) != usage.get("total_tokens"):
        errors.append("token totals do not reconcile")
    if any(turn.get(key) != 0 for key in
           ("gui_input_events", "file_or_network_tools", "recovery_cases")):
        errors.append("scope-excluded activity was recorded")
    if r.get("failed_launcher_attempt", {}).get("model_calls") != 0:
        errors.append("failed construction attempt incorrectly counted a model call")
    out = {
        "audit": "PASS_PREFLIGHT_SUMMARY_SHAPE_ONLY" if not errors else "HOLD_PREFLIGHT_SUMMARY_SHAPE",
        "checks": 11,
        "errors": errors,
        "source_hashes_recomputed": True,
        "protocol_transcript_present": False,
        "model_call_replayed": False,
        "scientific_acceptance": False,
    }
    print(json.dumps(out, sort_keys=True, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
