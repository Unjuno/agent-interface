from __future__ import annotations

import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = HERE / "cases.json"
OUT = HERE / "candidate.raw.json"


def graph_inventory(events: list[dict]) -> tuple[dict[str, dict], str | None]:
    by_id = {e["id"]: e for e in events}
    if len(by_id) != len(events):
        return by_id, "DUPLICATE_EVENT_ID"
    for event in events:
        for parent in event.get("parents", []):
            if parent not in by_id:
                return by_id, "MISSING_CAUSAL_PARENT"
    return by_id, None


def cut_status(events: list[dict], cut_ids: list[str]) -> tuple[bool, int, str | None]:
    by_id, error = graph_inventory(events)
    if error:
        return False, 0, error
    selected = set(cut_ids)
    if not selected <= by_id.keys():
        return False, 0, "UNKNOWN_EVENT_IN_CUT"
    for event in events:
        if event["id"] in selected:
            if any(parent not in selected for parent in event.get("parents", [])):
                return False, 0, "CUT_NOT_CAUSALLY_CLOSED"
            if any(other["stream"] == event["stream"] and other["seq"] < event["seq"] and other["id"] not in selected for other in events):
                return False, 0, "CUT_NOT_PREFIX_CLOSED"
    in_flight = sum(1 for event in events if event["id"] in selected and event["kind"].endswith("_send") or event["id"] in selected and event["kind"] == "send"
                    if not any(other.get("message") == event.get("message") and other["kind"] == "receive" and other["id"] in selected for other in events))
    return True, in_flight, None


def enumerate_cuts(events: list[dict]) -> int | None:
    by_id, error = graph_inventory(events)
    if error:
        return None
    ids = list(by_id)
    count = 0
    for bits in itertools.product((False, True), repeat=len(ids)):
        chosen = {event_id for event_id, include in zip(ids, bits) if include}
        valid = True
        for event in events:
            if event["id"] not in chosen:
                continue
            if any(parent not in chosen for parent in event.get("parents", [])):
                valid = False
                break
            if any(other["stream"] == event["stream"] and other["seq"] < event["seq"] and other["id"] not in chosen for other in events):
                valid = False
                break
        count += int(valid)
    return count


def decide(case: dict, required_epoch: str) -> dict:
    events = case["events"]
    by_id, error = graph_inventory(events)
    roles = case["roles"]
    graph_ready = all(role_id in by_id and by_id[role_id].get("fresh") is True for role_id in roles.values())
    if not graph_ready:
        return {"graph_only_ready": False, "cut_status": "UNKNOWN", "ready": False,
                "reason": "MISSING_OR_NOT_FRESH_REQUIRED_EVIDENCE", "legal_cut_count": enumerate_cuts(events)}
    if error:
        status, reason = "UNKNOWN", error
        in_flight = 0
    else:
        is_cut, in_flight, cut_error = cut_status(events, case["cut"])
        if not is_cut:
            status, reason = "UNKNOWN", cut_error
        elif in_flight:
            status, reason = "INCOMPLETE_IN_FLIGHT", "UNDELIVERED_INVALIDATION_OR_RELEASE"
        else:
            epochs = [by_id[event_id].get("epoch") for event_id in roles.values()]
            if any(epoch != required_epoch for epoch in epochs) or len(set(epochs)) != 1:
                status, reason = "CONTRADICTORY", "REQUIRED_EVIDENCE_EPOCH_MISMATCH"
            else:
                status, reason = "CONSISTENT", "SAME_EPOCH_CAUSALLY_CLOSED_CUT"
    return {"graph_only_ready": graph_ready, "cut_status": status, "ready": graph_ready and status == "CONSISTENT",
            "reason": reason, "in_flight_messages": in_flight, "legal_cut_count": enumerate_cuts(events)}


def main() -> None:
    if OUT.exists():
        raise SystemExit("STOP_OUTPUT_ALREADY_EXISTS")
    spec = json.loads(CASES.read_text(encoding="utf-8"))
    rows = []
    for case in spec["cases"]:
        rows.append({"case_id": case["case_id"], **decide(case, spec["required_epoch"])})
    result = {"schema": "blackstart-causal-cut-candidate-v1", "cases": rows,
              "graph_only_ready_count": sum(r["graph_only_ready"] for r in rows),
              "cut_aware_ready_ids": [r["case_id"] for r in rows if r["ready"]]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
