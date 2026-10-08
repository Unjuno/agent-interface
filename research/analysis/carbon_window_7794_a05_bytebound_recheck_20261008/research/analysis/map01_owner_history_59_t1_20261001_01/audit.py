"""Independent raw-only verifier; intentionally does not import candidate code."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


def verify(fixture: dict, candidate: dict) -> list[str]:
    errors = []
    expected_rows = [row for page in fixture["pages"] for row in page["workflow_runs"]]
    if candidate.get("history", {}).get("workflow_runs") != expected_rows:
        errors.append("visible rows differ from raw fixture (event omissions/order/duplicates)")
    history = candidate.get("history", {})
    if history.get("total_count") != len(expected_rows):
        errors.append("total_count differs from raw fixture row count")
    if history.get("pages_read") != len(fixture["pages"]):
        errors.append("pages_read differs from frozen page inventory")
    url = candidate.get("first_page_url", "")
    if "event=" in url or candidate.get("event_filter_present") is not False:
        errors.append("event filter present")
    scoped = [r for r in expected_rows if r.get("path") == fixture["workflow_path"]]
    ordered = sorted(scoped, key=lambda r: (int(r["run_number"]), int(r["id"])))
    current = next((r for r in scoped if int(r["id"]) == fixture["current_run_id"]), None)
    owner = candidate.get("owner", {})
    if current is None:
        errors.append("current run missing from fixture")
    elif owner.get("result_class") != "FAIL_ALLOCATION_ALREADY_OWNED" or owner.get("may_enter_formal_step") is not False:
        errors.append("owner decision did not deny later cross-event run")
    elif owner.get("owner_run_id") != int(ordered[0]["id"]):
        errors.append("owner id differs from independent earliest-row oracle")
    elif owner.get("matching_run_ids") != [int(r["id"]) for r in ordered]:
        errors.append("matching run inventory differs from independent oracle")
    return errors


def corruption_controls(fixture: dict, candidate: dict) -> dict:
    controls = {}
    corruptions = {}
    filtered = copy.deepcopy(candidate)
    filtered["history"]["workflow_runs"] = [r for r in filtered["history"]["workflow_runs"] if r["id"] != 91001]
    corruptions["event_filtered_prior_owner"] = filtered
    duplicate = copy.deepcopy(candidate)
    duplicate["history"]["workflow_runs"].append(copy.deepcopy(duplicate["history"]["workflow_runs"][0]))
    corruptions["duplicate_run_id"] = duplicate
    truncated = copy.deepcopy(candidate)
    truncated["history"]["workflow_runs"].pop()
    corruptions["truncated_history"] = truncated
    wrong_total = copy.deepcopy(candidate)
    wrong_total["history"]["total_count"] -= 1
    corruptions["false_total_count"] = wrong_total
    forged = copy.deepcopy(candidate)
    forged["owner"]["owner_run_id"] = fixture["current_run_id"]
    forged["owner"]["result_class"] = "PASS_CANONICAL_GLOBAL_OWNER"
    forged["owner"]["may_enter_formal_step"] = True
    corruptions["forged_admission"] = forged
    for name, raw in corruptions.items():
        controls[name] = {"rejected": bool(verify(fixture, raw)), "errors": verify(fixture, raw)}
    return controls


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    errors = verify(fixture, candidate)
    controls = corruption_controls(fixture, candidate)
    result = {
        "schema": "map01-owner-history-independent-audit-v1",
        "result_class": "PASS_METHOD_SCOPED" if not errors and all(v["rejected"] for v in controls.values()) else "HOLD_AUDIT",
        "candidate_errors": errors,
        "corruption_controls": controls,
        "corruption_rejected": sum(v["rejected"] for v in controls.values()),
        "corruption_total": len(controls),
        "scope": "offline synthetic source/method test only; no live API or Actions claim",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result_class": result["result_class"], "candidate_errors": len(errors), "corruption_rejected": result["corruption_rejected"]}, sort_keys=True))
    return 0 if result["result_class"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
