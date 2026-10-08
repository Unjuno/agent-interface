"""Deterministic finite schedules for Issue #6664's T0 protocol experiment."""

from __future__ import annotations

import itertools
import json


STAGES = ("ADMISSION", "ENQUEUE", "START", "EFFECT", "COMPLETE_ACK")
BOUNDARY_CUTS = range(len(STAGES) + 1)


def _scenario(case_id: str, cut: int, resolution: str, ack: str,
              input_kind: str, release: str, observation: str,
              duplicate: bool = False) -> dict:
    events: list[dict] = []

    def add(t: int, kind: str, **fields: object) -> None:
        events.append({"t": t, "kind": kind, **fields})

    add(0, "TAKEOVER", epoch=2, backend_gen=1)
    op_id = f"{case_id}:op"
    timeline = [1, 2, 3, 4, 5]

    if cut > 0:
        add(0, "ADMISSION", epoch=1, op_id=op_id, decision="ACCEPTED",
            input_kind=input_kind, backend_gen=1)
        if input_kind == "held_key":
            add(0, "INPUT_DOWN", epoch=1, op_id=op_id, input="KEY_A",
                backend_gen=1)

    if resolution == "natural":
        for idx, stage in enumerate(STAGES[1:], start=1):
            if idx < cut:
                t = timeline[idx - 1]
                if stage == "COMPLETE_ACK" and ack != "normal":
                    continue
                add(t, stage, epoch=1, op_id=op_id, backend_gen=1)
        if cut > 0 and ack in ("delayed", "lost"):
            if ack == "delayed":
                add(9, "COMPLETE_ACK", epoch=1, op_id=op_id, backend_gen=1)
            # A lost acknowledgment deliberately has no synthetic terminal receipt.
    elif resolution in ("cancel_before_start", "cancel_before_effect"):
        threshold = 2 if resolution == "cancel_before_start" else 3
        # Prefix operations stop at the cancellation threshold. Future stages
        # are not executed; a receipt is explicit evidence, not a time guess.
        prefix_end = min(cut, threshold)
        for idx, stage in enumerate(STAGES[1:], start=1):
            if idx < prefix_end:
                add(timeline[idx - 1], stage, epoch=1, op_id=op_id,
                    backend_gen=1)
        if cut > 0:
            add(1, "CANCEL_ACK", epoch=1, op_id=op_id,
                outcome="CANCELLED_BEFORE_START" if resolution == "cancel_before_start"
                else "CANCELLED_BEFORE_EFFECT", backend_gen=1)
    else:
        raise ValueError(resolution)

    if input_kind == "held_key" and cut > 0:
        if release == "on_time":
            add(6, "INPUT_RELEASE_ACK", epoch=1, op_id=op_id,
                input="KEY_A", backend_gen=1)
        elif release == "delayed":
            add(9, "INPUT_RELEASE_ACK", epoch=1, op_id=op_id,
                input="KEY_A", backend_gen=1)
        # missing release has no receipt.

    # Every case has an explicit stale-epoch admission attempt after takeover.
    add(2, "ADMISSION", epoch=1, op_id=f"{case_id}:late",
        decision="REJECTED_STALE", input_kind="ordinary", backend_gen=1)
    if duplicate and cut > 0:
        add(0, "ADMISSION", epoch=1, op_id=op_id, decision="ACCEPTED",
            input_kind=input_kind, backend_gen=1)

    events.sort(key=lambda event: (event["t"], event["kind"],
                                   str(event.get("op_id", ""))))
    for seq, event in enumerate(events, start=1):
        event["seq"] = seq

    if observation == "fresh":
        obs_t = 10
        add(obs_t, "OBSERVATION", epoch=2, freshness="FRESH",
            covers_through_seq=max(event["seq"] for event in events),
            backend_gen=1)
    elif observation == "stale":
        add(10, "OBSERVATION", epoch=2, freshness="STALE",
            covers_through_seq=1, backend_gen=1)
    elif observation != "missing":
        raise ValueError(observation)

    events.sort(key=lambda event: (event["t"], event["kind"],
                                   str(event.get("op_id", ""))))
    for seq, event in enumerate(events, start=1):
        event["seq"] = seq
    obs = next((event for event in events if event["kind"] == "OBSERVATION"), None)
    if obs and observation == "fresh":
        obs["covers_through_seq"] = obs["seq"] - 1

    return {
        "case_id": case_id,
        "cut": cut,
        "resolution": resolution,
        "ack": ack,
        "input_kind": input_kind,
        "release": release,
        "observation": observation,
        "duplicate": duplicate,
        "events": events,
    }


def build_scenarios() -> list[dict]:
    cases = []
    for values in itertools.product(
        BOUNDARY_CUTS,
        ("natural", "cancel_before_start", "cancel_before_effect"),
        ("normal", "delayed", "lost"),
        ("ordinary", "held_key"),
        ("on_time", "delayed", "missing"),
        ("fresh", "stale", "missing"),
        (False, True),
    ):
        cut, resolution, ack, input_kind, release, observation, duplicate = values
        if resolution == "cancel_before_start" and cut > 2:
            continue
        if resolution == "cancel_before_effect" and cut > 3:
            continue
        if cut == 0 and resolution != "natural":
            continue
        case_id = "q-" + "-".join(map(str, values)).replace(" ", "")
        cases.append(_scenario(case_id, cut, resolution, ack, input_kind,
                               release, observation, duplicate))

    cases.extend([
        _restart_case("restart_unreconciled", "none"),
        _restart_case("restart_reconciled_cancel", "cancel"),
        _restart_case("restart_reconciled_complete", "complete"),
    ])
    return cases


def _restart_case(case_id: str, reconciliation: str) -> dict:
    events = []

    def add(t: int, kind: str, **fields: object) -> None:
        events.append({"t": t, "kind": kind, **fields})

    op_id = f"{case_id}:op"
    add(0, "ADMISSION", epoch=1, op_id=op_id, decision="ACCEPTED",
        input_kind="ordinary", backend_gen=1)
    add(1, "START", epoch=1, op_id=op_id, backend_gen=1)
    if reconciliation == "none":
        add(3, "BACKEND_RESTART", backend_gen=2)
        add(4, "TAKEOVER", epoch=2, backend_gen=2)
        add(5, "ADMISSION", epoch=1, op_id=f"{case_id}:late",
            decision="REJECTED_STALE", input_kind="ordinary", backend_gen=2)
        add(6, "EFFECT", epoch=1, op_id=op_id, backend_gen=1)
        add(7, "COMPLETE_ACK", epoch=1, op_id=op_id, backend_gen=1)
    elif reconciliation == "cancel":
        add(3, "BACKEND_RESTART", backend_gen=2)
        add(4, "TAKEOVER", epoch=2, backend_gen=2)
        add(5, "ADMISSION", epoch=1, op_id=f"{case_id}:late",
            decision="REJECTED_STALE", input_kind="ordinary", backend_gen=2)
        add(6, "RECONCILIATION_ACK", epoch=1, op_id=op_id,
            outcome="CANCELLED_BEFORE_EFFECT", backend_gen=2)
    elif reconciliation == "complete":
        add(2, "EFFECT", epoch=1, op_id=op_id, backend_gen=1)
        add(3, "BACKEND_RESTART", backend_gen=2)
        add(4, "TAKEOVER", epoch=2, backend_gen=2)
        add(5, "ADMISSION", epoch=1, op_id=f"{case_id}:late",
            decision="REJECTED_STALE", input_kind="ordinary", backend_gen=2)
        add(6, "RECONCILIATION_ACK", epoch=1, op_id=op_id,
            outcome="COMPLETED", backend_gen=2)
    events.sort(key=lambda event: (event["t"], event["kind"],
                                   str(event.get("op_id", ""))))
    for seq, event in enumerate(events, start=1):
        event["seq"] = seq
    events.append({"t": 8, "seq": len(events) + 1, "kind": "OBSERVATION",
                   "epoch": 2, "freshness": "FRESH",
                   "covers_through_seq": len(events), "backend_gen": 2})
    return {"case_id": case_id, "cut": -1, "resolution": reconciliation,
            "ack": "restart", "input_kind": "ordinary", "release": "n/a",
            "observation": "fresh", "duplicate": False, "events": events}


def canonical_bytes() -> bytes:
    return (json.dumps(build_scenarios(), sort_keys=True, separators=(",", ":"))
            + "\n").encode()


if __name__ == "__main__":
    print(json.dumps(build_scenarios(), sort_keys=True, indent=2))
