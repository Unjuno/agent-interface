"""Independent auditor for Issue #869 frozen block."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "freeze.json").read_text())
RESULT = HERE / "results" / "release-edge-live-x11-01"
EXPECTED_SOURCE = {
    "live_control/input_owner_v10.py": "341b3c01649943ddaad5f28431a792c4889cc36e",
    "live_control/input_owner_v11.py": "842071284156d3ccc647f47135ee62a9e512cb56",
    "doom/doom_typed_release_backend_v2.py": "cf13d630ae22a50272a766c86d7f325f352a89d7",
}


def main() -> None:
    errors: list[str] = []
    manifest = json.loads((RESULT / "manifest.json").read_text())
    if manifest.get("formal_invocations") != 1:
        errors.append("formal_invocations")
    if manifest.get("reruns") != 0:
        errors.append("reruns")
    if manifest.get("case_runner") != "run_case_v2.py":
        errors.append("case_runner")
    if manifest.get("schedule") != FREEZE["schedule"]:
        errors.append("schedule")
    if len(manifest.get("cases", [])) != 12:
        errors.append("manifest_case_count")

    arm_counts = {"baseline_v10": 0, "candidate_v11": 0}
    candidate_rpc_width_ns: list[int] = []
    candidate_app_release_after_return_ns: list[int] = []

    for case_id, arm in FREEZE["schedule"]:
        path = RESULT / case_id / "result.json"
        if not path.exists():
            errors.append(f"{case_id}:missing_result")
            continue
        row = json.loads(path.read_text())
        if row.get("status") != "completed" or row.get("case_id") != case_id or row.get("arm") != arm:
            errors.append(f"{case_id}:identity_or_status")
            continue
        arm_counts[arm] += 1
        if row.get("source_blobs") != EXPECTED_SOURCE:
            errors.append(f"{case_id}:source_blobs")
        events = row.get("app_events", [])
        if [item.get("event") for item in events] != ["press", "release"]:
            errors.append(f"{case_id}:app_events")
        else:
            if events[0].get("press_count") != 1 or events[1].get("release_count") != 1:
                errors.append(f"{case_id}:app_counts")
        if row.get("terminal_f8_down") is not False:
            errors.append(f"{case_id}:terminal_key")
        state = row.get("owner_state", {})
        if state.get("owned_keycodes") != []:
            errors.append(f"{case_id}:owned_keycodes")
        if state.get("physical_pointer_mask") != 0:
            errors.append(f"{case_id}:pointer_mask")

        receipt = row.get("release_receipt")
        if arm == "baseline_v10":
            if receipt is not None:
                errors.append(f"{case_id}:baseline_receipt")
        else:
            if not isinstance(receipt, dict):
                errors.append(f"{case_id}:missing_candidate_receipt")
                continue
            required = {
                "event": "input_release_rpc",
                "operation": "up",
                "payload": "F8",
                "id": case_id,
                "step": 1,
                "grants_input_authority": False,
                "x11_release_and_sync_completed_before_return": True,
                "continuous_physical_state_sampled": False,
                "application_consumption_observed": False,
            }
            for key, value in required.items():
                if receipt.get(key) != value:
                    errors.append(f"{case_id}:receipt_{key}")
            if receipt.get("intent_token") != f"release-edge-{case_id}":
                errors.append(f"{case_id}:intent_lineage")
            start = receipt.get("call_started_ns")
            end = receipt.get("call_returned_ns")
            interval = receipt.get("release_transition_interval_ns")
            width = receipt.get("interval_width_ns")
            if not (isinstance(start, int) and isinstance(end, int) and interval == [start, end] and width == end - start and width > 0):
                errors.append(f"{case_id}:receipt_interval")
            else:
                candidate_rpc_width_ns.append(width)
                if len(events) == 2:
                    candidate_app_release_after_return_ns.append(events[1]["time_ns"] - end)

    if arm_counts != {"baseline_v10": 6, "candidate_v11": 6}:
        errors.append("arm_counts")

    decision = "PASS_RELEASE_EDGE_LIVE_X11_SCOPED" if not errors else "FAIL_RELEASE_EDGE_LIVE_X11"
    report = {
        "decision": decision,
        "errors": errors,
        "arm_counts": arm_counts,
        "candidate_rpc_width_ns": candidate_rpc_width_ns,
        "candidate_app_release_after_return_ns": candidate_app_release_after_return_ns,
        "formal_invocations": manifest.get("formal_invocations"),
        "reruns": manifest.get("reruns"),
        "case_runner": manifest.get("case_runner"),
    }
    (RESULT / "audit.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(bool(errors))


if __name__ == "__main__":
    main()