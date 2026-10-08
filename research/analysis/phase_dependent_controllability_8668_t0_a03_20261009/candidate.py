#!/usr/bin/env python3
"""One-shot finite candidate for Issue #8668 T0 A03."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN_ID = "PHASE-CONTROL-DELAYS-8668-T0-A03-20261009"
BASE = "ffe5292b3164a3eb7e2b5d18eaadcbafdcd2b385"
PHASES = ("PROPOSED", "ADMITTED", "QUEUED", "EMITTED", "CONSUMED")
POST_EMIT = {"EMITTED", "CONSUMED"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_design() -> dict:
    freeze = json.loads((ROOT / "FREEZE.json").read_text())
    if freeze["allocation"] != RUN_ID or freeze["base_commit"] != BASE:
        raise SystemExit("STOP_FREEZE_ID_OR_BASE_MISMATCH")
    for name, expected in freeze["source_sha256"].items():
        if sha(ROOT / name) != expected:
            raise SystemExit(f"STOP_FREEZE_SOURCE_MISMATCH:{name}")
    return json.loads((ROOT / "design.json").read_text())


def schedules(design: dict) -> list[dict]:
    prior = design["prior_operation_id"]
    active = design["active_operation_id"]
    raw: list[dict] = []
    for phase in design["phases"]:
        effect_states = design["post_emit_effect_states"] if phase in POST_EMIT else [False]
        for committed, timeline_name, timeline, retry, release in itertools.product(
            effect_states,
            design["receipt_timelines"].items(),
            [None],
            design["retry_requested"],
            design["neutral_release_observed"],
        ):
            # The named timeline is the second product component; the third is
            # a one-element placeholder keeping the axes explicit.
            name, events = timeline_name
            if not valid_timeline(phase, committed, events):
                continue
            receipts = []
            next_sequence: dict[tuple[str, int], int] = {}
            for position, (owner, kind) in enumerate(events, start=1):
                if owner == "prior":
                    op_id, attempt = prior, 1
                elif owner == "prior_reused":
                    op_id, attempt = active, design["active_attempt"] - 1
                else:
                    op_id, attempt = active, design["active_attempt"]
                identity = (op_id, attempt)
                sequence = 1 if name.endswith("_replayed") else next_sequence.get(identity, 0) + 1
                next_sequence[identity] = sequence
                receipts.append({
                    "ack_id": f"ack-{op_id}-attempt-{attempt}-{kind}-{sequence}",
                    "operation_id": op_id,
                    "logical_action_id": design["active_logical_action"],
                    "attempt": attempt,
                    "kind": kind,
                    "asserted_phase": "CONSUMED" if kind == "EFFECT_CONFIRMED" else "QUEUED",
                    "sequence": sequence,
                    "arrival_order": position,
                })
            raw.append({
                "phase": phase,
                "effect_committed": committed,
                "retry_requested": retry,
                "neutral_release_observed": release,
                "receipts": receipts,
                "timeline": name,
            })
    raw.append({
        "phase": None,
        "effect_committed": False,
        "retry_requested": False,
        "neutral_release_observed": False,
        "receipts": [],
        "timeline": "no_input_control",
    })
    return raw


def valid_timeline(phase: str, committed: bool, events: list[list[str]]) -> bool:
    for owner, kind in events:
        if owner == "active" and kind == "EFFECT_CONFIRMED":
            if phase not in POST_EMIT or not committed:
                return False
        if owner == "active" and kind == "CANCEL_CONFIRMED":
            if phase not in POST_EMIT and committed:
                return False
    return True


def decide(schedule: dict, design: dict, bind_identity: bool) -> dict:
    if schedule["phase"] is None:
        return {"status": "NO_ACTION", "retry_admitted": False, "accepted_ack_ids": [], "ignored_stale": 0}
    active_id = design["active_operation_id"]
    active_attempt = design["active_attempt"]
    status = "UNKNOWN" if schedule["phase"] in POST_EMIT else "PENDING"
    accepted: list[str] = []
    ignored_stale = 0
    seen: set[tuple[str, int, int]] = set()
    active_kinds: set[str] = set()
    for receipt in schedule["receipts"]:
        if bind_identity and (receipt["operation_id"] != active_id or receipt["attempt"] != active_attempt):
            ignored_stale += 1
            continue
        key = (receipt["operation_id"], receipt["attempt"], receipt["sequence"])
        if key in seen:
            continue
        seen.add(key)
        matches_active = receipt["operation_id"] == active_id and receipt["attempt"] == active_attempt
        if matches_active:
            active_kinds.add(receipt["kind"])
            if len(active_kinds) > 1:
                status = "CONFLICT_UNKNOWN"
                accepted.clear()
                continue
        if status == "CONFLICT_UNKNOWN":
            continue
        if receipt["kind"] == "EFFECT_CONFIRMED":
            if schedule["phase"] in POST_EMIT:
                status = "COMPLETED"
                accepted.append(receipt["ack_id"])
            elif matches_active:
                status = "CONFLICT_UNKNOWN"
        elif receipt["kind"] == "CANCEL_CONFIRMED":
            if schedule["phase"] not in POST_EMIT:
                status = "CANCELLED_BEFORE_EMIT"
                accepted.append(receipt["ack_id"])
            elif matches_active:
                # This may be a delayed receipt from before emission, but it
                # cannot authorize a post-frontier cancellation or retry.
                status = "UNKNOWN"
    retry_admitted = bool(
        schedule["retry_requested"] and status == "CANCELLED_BEFORE_EMIT"
    )
    return {
        "status": status,
        "retry_admitted": retry_admitted,
        "accepted_ack_ids": accepted,
        "ignored_stale": ignored_stale,
    }


def safe_retry(schedule: dict, design: dict) -> bool:
    if not schedule["retry_requested"] or schedule["phase"] in POST_EMIT or schedule["phase"] is None:
        return False
    return any(
        receipt["operation_id"] == design["active_operation_id"]
        and receipt["attempt"] == design["active_attempt"]
        and receipt["kind"] == "CANCEL_CONFIRMED"
        for receipt in schedule["receipts"]
    )


def main() -> None:
    design = load_design()
    rows = []
    for index, schedule in enumerate(schedules(design)):
        strict = decide(schedule, design, bind_identity=True)
        latest = decide(schedule, design, bind_identity=False)
        rows.append({
            "schedule_id": f"a03-{index:04d}",
            "exogenous": schedule,
            "strict": strict,
            "latest_receipt_comparator": latest,
            "derived": {
                "strict_false_completion": strict["status"] == "COMPLETED" and not schedule["effect_committed"],
                "strict_unsafe_retry": strict["retry_admitted"] and not safe_retry(schedule, design),
                "latest_false_completion": latest["status"] == "COMPLETED" and not schedule["effect_committed"],
                "latest_unsafe_retry": latest["retry_admitted"] and not safe_retry(schedule, design),
            },
        })
    out = {
        "schema": "8668-a03-raw-v1",
        "allocation": RUN_ID,
        "base_commit": BASE,
        "row_count": len(rows),
        "rows": rows,
    }
    print(json.dumps(out, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
