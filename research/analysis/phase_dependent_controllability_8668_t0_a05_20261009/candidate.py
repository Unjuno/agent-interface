"""Candidate reducers for visible-only emitted-frontier inputs."""

import json
from pathlib import Path

PRE_EMIT = {"PROPOSED", "QUEUED"}


def _matches(receipt, requests, active):
    expected_request = {"CANCEL_ACK": "CANCEL_REQUEST",
                        "EFFECT_ACK": "EFFECT_REQUEST"}.get(receipt.get("kind"))
    return expected_request is not None and any(
        request.get("request_id") == receipt.get("request_id") and
        request.get("kind") == expected_request and
        request.get("operation_id") == active.get("operation_id") == receipt.get("operation_id") and
        request.get("attempt") == active.get("attempt") == receipt.get("attempt")
        for request in requests
    )


def _classify(view, active, phase_refined):
    matches = [receipt for receipt in sorted(
        view.get("receipts", []), key=lambda item: item.get("arrival_order", 0))
        if _matches(receipt, view.get("requests", []), active)]
    kinds = {receipt.get("kind") for receipt in matches}
    phase = view.get("observed_phase")
    if len(kinds) > 1:
        status = "UNKNOWN"
    elif kinds == {"CANCEL_ACK"}:
        status = "CANCELLED_NO_EFFECT" if not phase_refined or phase in PRE_EMIT else "UNKNOWN"
    elif kinds == {"EFFECT_ACK"}:
        status = "EFFECT_CONFIRMED" if not phase_refined or phase == "CONSUMED" else "UNKNOWN"
    elif phase_refined and phase not in PRE_EMIT:
        status = "UNKNOWN"
    else:
        status = "PENDING"
    return {"status": status,
            "retry_eligible": bool(view.get("retry_requested") and
                                    status == "CANCELLED_NO_EFFECT")}


def run(design):
    """Run on a separate visible-only input file, without evaluator truth."""
    rows = []
    for case in design["cases"]:
        view = case["view"]
        rows.append({
            "case_id": case["id"],
            "view": view,
            "phase_refined": _classify(view, design["active"], True),
            "phase_blind_request_bound": _classify(view, design["active"], False),
        })
    return {"schema": "8668-a05-raw-v1", "allocation": design["allocation"],
            "base_commit": design["base_commit"], "row_count": len(rows), "rows": rows}


def main():
    root = Path(__file__).resolve().parent
    visible_input = json.loads((root / "candidate_input.json").read_text())
    print(json.dumps(run(visible_input), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
