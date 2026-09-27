"""Independent completeness audit for the retained adaptive repair model case."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def all_keys(value: object) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key).lower())
            found.update(all_keys(child))
    elif isinstance(value, list):
        for child in value:
            found.update(all_keys(child))
    return found


def main(case: Path, out: Path) -> int:
    report_path = case / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    actions = report.get("actions", [])
    releases = [a.get("terminal", {}).get("release", {}) for a in actions]
    actual = report.get("actual")
    keys = all_keys(report)
    required = {
        "required_evidence_role": any("role" in k for k in keys),
        "measured_observation_cost": any("observation_cost" in k for k in keys),
        "downstream_reserve": any("reserve" in k for k in keys),
        "typed_policy_decision": any("typed" in k for k in keys),
        "scalar_policy_decision": any("scalar" in k for k in keys),
        "final_task_disposition": isinstance(actual, dict) and bool(actual),
    }
    result = {
        "schema": "typed-admission-live-transfer-retained-case-audit-v1",
        "source_case": "research/live_control/results/adaptive-semantic-repair-live-02/case-02-model",
        "report_sha256": sha(report_path),
        "report_status": report.get("status"),
        "retry_count": report.get("retry_count"),
        "model_calls": report.get("metrics", {}).get("total_model_calls"),
        "input_tokens": report.get("metrics", {}).get("total_input_tokens"),
        "model_visible_images": report.get("metrics", {}).get("model_visible_images"),
        "model_wait_ms": report.get("metrics", {}).get("adaptive_model_wait_ms"),
        "caller_elapsed_ms": report.get("metrics", {}).get("mutation_capture_to_caller_return_ms"),
        "action_count": len(actions),
        "all_actions_completed": bool(actions) and all(
            a.get("terminal", {}).get("status") == "completed" for a in actions
        ),
        "all_releases_verified_empty": bool(releases) and all(
            r.get("verified") is True and not r.get("keys_down") and not r.get("buttons_down")
            for r in releases
        ),
        "final_task_value": actual,
        "required_fields_present": required,
        "decision": "HOLD_LIVE_EVIDENCE_INCOMPLETE" if not all(required.values()) else "RETAINED_CASE_COMPLETE",
        "formal_allocation_count": 0,
        "scope": "posthoc completeness audit only; no policy replay, model call, or task rerun",
    }
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] == "HOLD_LIVE_EVIDENCE_INCOMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2])))
