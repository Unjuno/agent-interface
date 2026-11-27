"""Run the frozen synthetic late-usage/native-owner composition once."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INTEGRATION_ROOT = ROOT.parent
REPO_ROOT = ROOT.parents[3]
if str(INTEGRATION_ROOT) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_ROOT))

from comparison_measurement_v1 import validate_measured_run
from provider_attempt_recorder import ProviderAttemptRecorder
from test_recorded_comparison_adapter_v1 import RecordedComparisonAdapterTests


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def run_case(name: str, available: bool) -> dict:
    case_root = ROOT / "runs" / name
    if case_root.exists() and any(case_root.iterdir()):
        raise FileExistsError(f"refusing to overwrite retained run: {case_root}")
    measured = RecordedComparisonAdapterTests.make_run(
        case_root, "A" if available else "B", 1 if available else 2,
        effect_observed_ns=None, late_usage_available=available)
    receipt = ProviderAttemptRecorder(case_root / "recorder").reconcile()
    retained = {(item["path"], item["sha256"]) for item in receipt["raw_refs"]}
    for item in measured["task_ledger"]["raw_refs"]:
        identity = (item["path"], item["sha256"])
        if identity not in retained:
            receipt["raw_refs"].append(item)
            retained.add(identity)
    summary = validate_measured_run(measured)
    result = {
        "condition": "late-usage" if available else "missing-usage",
        "model_attempt_count": summary["model_attempt_count"],
        "input_tokens": summary["input_tokens"],
        "output_tokens": summary["output_tokens"],
        "usage_status": summary["usage_status"],
        "task_success": summary["task_success"],
        "factual_task_success": summary["factual_task_success"],
        "effect_timing": summary["effect_attribution"]["effect_timing"],
        "tool_call_count": summary["tool_call_count"],
        "raw_ref_count": summary["raw_ref_count"],
        "native_owner_binding": measured["task_ledger"][
            "native_owner_binding"],
        "receipt_complete": receipt["complete"],
        "unresolved_attempt_ids": receipt["unresolved_attempt_ids"],
        "unresolved_tool_call_ids": receipt["unresolved_tool_call_ids"],
    }
    write_json(case_root / "receipt.json", receipt)
    write_json(case_root / "measured_run.json", measured)
    write_json(case_root / "summary.json", result)
    return result


def main() -> None:
    conditions = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8"))
    if conditions["source_revision"] != "b2d8933a2b510905eb5ffd6090aee8de186b5f26":
        raise SystemExit("frozen source revision changed")
    positive = run_case("positive", True)
    control = run_case("missing-usage", False)
    passed = (
        positive["model_attempt_count"] == control["model_attempt_count"] == 2
        and positive["usage_status"] == "complete"
        and positive["input_tokens"] == 28 and positive["output_tokens"] == 5
        and control["usage_status"] == "incomplete"
        and control["input_tokens"] is None and control["output_tokens"] is None
        and positive["task_success"] is control["task_success"] is None
        and positive["effect_timing"] == control["effect_timing"] == "unknown"
        and positive["receipt_complete"] is control["receipt_complete"] is True
        and all(not row["unresolved_attempt_ids"] and
                not row["unresolved_tool_call_ids"] for row in (positive, control))
    )
    result = {"status": "PASS_SCOPED_SYNTHETIC" if passed else "FAIL",
              "source_revision": conditions["source_revision"],
              "provider_calls": 0, "relay_calls": 0, "gui_input": 0,
              "conditions": [positive, control]}
    write_json(ROOT / "experiment-result.json", result)
    print(json.dumps(result, sort_keys=True))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
