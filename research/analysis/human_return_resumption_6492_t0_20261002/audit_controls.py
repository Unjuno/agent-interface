"""One-shot independent auditor plus six fail-closed output corruptions."""
from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

import audit


TARGETS = {
    "swapped_task_or_window": "stable_cue_written::preserved_view",
    "stale_cue_after_external_edit": "changed_external_state::preserved_view",
    "forged_agent_authored_cue": "stable_cue_written::preserved_view_optional_cue",
    "duplicate_save": "duplicate_effect_guard::preserved_view",
    "cue_absent_when_offered_and_written": "stable_cue_written::preserved_view_optional_cue",
    "delayed_emergency_release": "urgent_release::timing_only",
}


def run_controls(fixture_path: Path, candidate_path: Path) -> dict[str, Any]:
    baseline = json.loads(candidate_path.read_bytes())
    clean = audit.audit(fixture_path, candidate_path)
    controls = {}
    for name, target in TARGETS.items():
        changed = copy.deepcopy(baseline)
        display = next(row for row in changed["displays"] if row["row_id"] == target)
        if name == "swapped_task_or_window":
            display["preserved_view"]["window_id"] = "other-window"
        elif name == "stale_cue_after_external_edit":
            display["state_change_warning"] = None
        elif name == "forged_agent_authored_cue":
            display["cue_display"]["author"] = "agent"
        elif name == "duplicate_save":
            display["automatic_effect"] = True
        elif name == "cue_absent_when_offered_and_written":
            display["cue_display"] = None
        elif name == "delayed_emergency_release":
            display["delivery"] = "defer_until_user_safe_boundary"
        with tempfile.TemporaryDirectory() as temporary:
            altered_path = Path(temporary) / "mutated-candidate.json"
            altered_path.write_bytes(audit.stable_bytes(changed) + b"\n")
            observed = audit.audit(fixture_path, altered_path)
        controls[name] = {
            "target_row_id": target,
            "audit_result": observed["result"],
            "rejected": observed["result"] == "FAIL_METHOD",
            "errors": observed["errors"],
        }
    passed = clean["result"] == "PASS_METHOD_SCOPED" and all(item["rejected"] for item in controls.values())
    return {
        "schema": "human-return-resumption-audit-controls-v1",
        "result": "PASS_METHOD_SCOPED" if passed else "FAIL_METHOD",
        "baseline": clean,
        "mutation_controls": controls,
        "control_count": len(controls),
        "rejected_controls": sum(item["rejected"] for item in controls.values()),
        "errors": [] if passed else [name for name, item in controls.items() if not item["rejected"]],
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_bytes(audit.stable_bytes(run_controls(args.fixture, args.candidate)) + b"\n")
