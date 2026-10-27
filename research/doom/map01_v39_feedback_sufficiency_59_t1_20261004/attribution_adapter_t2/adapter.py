"""Fail-closed adapter from current V15 producer rows to attribution T0."""
from __future__ import annotations
import hashlib
from collections import Counter, defaultdict
from pathlib import Path
import sys

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))
from scorer_feedback_attribution_v1 import (  # noqa: E402
    SAMPLE_SCHEMA, EVENT_SCHEMA, attribute_positive_events,
)


def _integer(value):
    return type(value) is int and value >= 0


def _sha256_hex(value):
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


def _identity(row):
    token, owner, identifier, step, key = (
        row.get("intent_token"), row.get("owner_id"), row.get("id"),
        row.get("step"), row.get("key"),
    )
    if (not isinstance(token, str) or not token or not isinstance(owner, str) or not owner
        or not isinstance(identifier, str) or not identifier or not _integer(step)
        or not isinstance(key, str) or not key):
        return None
    return owner, token, identifier, step, key


def _normalize_samples(rows):
    samples=[]
    for row in rows:
        if not isinstance(row, dict) or row.get("controller_visible") is not False:
            raise ValueError("scorer sample envelope must be controller-invisible")
        payload=row.get("payload")
        if not isinstance(payload, dict) or payload.get("schema") != SAMPLE_SCHEMA:
            raise ValueError("invalid V15 scorer sample payload")
        samples.append(dict(payload))
    return samples


def _verified_up(row, down, identity):
    receipt=row.get("owner_thread_keyup_receipt")
    if not isinstance(receipt, dict):
        return None, False
    sync_ns=receipt.get("owner_sync_returned_ns")
    caller_start=row.get("release_call_started_ns")
    caller_end=row.get("release_call_returned_ns")
    owner_start=receipt.get("owner_keyrelease_started_ns")
    complete=(
        row.get("event")=="input_release_transition"
        and row.get("operation")=="up"
        and row.get("release_batch_schema")=="input-release-batch-v3"
        and row.get("release_batch_complete") is True
        and row.get("owner_transition_verified") is True
        and row.get("owner_thread_keyup_verified") is True
        and row.get("owner_thread_keyup_verified_after_batch") is True
        and row.get("physical_verification_authoritative") is False
        and receipt.get("event")=="owner_explicit_keyup"
        and receipt.get("operation")=="up"
        and receipt.get("server_sync_completed") is True
        and receipt.get("physical_verification_authoritative") is False
        and receipt.get("key")==identity[4]
        and receipt.get("owner_id")==identity[0]
        and receipt.get("intent_token")==identity[1]
        and row.get("key")==identity[4]
        and row.get("owner_id")==identity[0]
        and row.get("intent_token")==identity[1]
        and row.get("id")==identity[2]
        and row.get("step")==identity[3]
        and type(caller_start) is int and type(caller_end) is int
        and type(owner_start) is int and type(sync_ns) is int
        and caller_start <= owner_start <= sync_ns <= caller_end
        and down.get("admitted_ns", -1) <= sync_ns
    )
    if row.get("release_batch_finalized_by_terminal_cleanup") is True:
        complete = complete and row.get("terminal_cleanup_verified") is True
    return (sync_ns if _integer(sync_ns) else None), bool(complete)


def _unresolved(rows, reason):
    output=[]
    for row in rows:
        if row.get("polarity") != "positive" or row.get("useful") is not True:
            continue
        output.append({
            "event_sequence": row.get("event_sequence"),
            "kind": row.get("kind"),
            "detection_interval_ns": None,
            "status": "UNRESOLVED",
            "reason": reason,
            "possible_intent_tokens": [],
            "intent_token": None,
            "causal_attribution": "NOT_ESTABLISHED",
        })
    return output


def _measured_interval_outcomes(samples, events, input_rows, exact_intervals):
    """Use paired X-server sample brackets for conservative overlap checks.

    Edge intervals bound when a transition may have happened; they do not
    prove continuous key occupancy. They can expose possible competing intent
    overlap, but never establish full-span unique coverage.
    """
    rows = []
    for row in input_rows:
        if (not isinstance(row, dict)
            or row.get("status") not in {
                "adapter_edge_brackets_paired", "adapter_edge_receipt_incomplete"
            }
            or "down_edge_interval_ns" not in row
            or "up_edge_interval_ns" not in row):
            continue
        down, up = row.get("down_edge_interval_ns"), row.get("up_edge_interval_ns")
        valid = (
            row.get("status") == "adapter_edge_brackets_paired"
            and type(down) is list and len(down) == 2
            and type(up) is list and len(up) == 2
            and all(_integer(value) for value in down + up)
            and down[0] <= down[1] < up[0] <= up[1]
            and row.get("grants_input_authority") is False
            and row.get("application_consumption_observed") is False
            and _sha256_hex(row.get("program_id_sha256"))
            and _sha256_hex(row.get("intent_token_sha256"))
            and _sha256_hex(row.get("owner_id_sha256"))
            and isinstance(row.get("key"), str) and bool(row["key"])
        )
        if not valid:
            rows.append(None)
        else:
            rows.append({"token": row["intent_token_sha256"], "down": down,
                         "up": up, "key": row["key"]})

    sample_times = [row["sample_ns"] for row in samples]
    exact_outcomes = attribute_positive_events(samples, events, exact_intervals)
    exact_by_sequence = {row["event_sequence"]: row for row in exact_outcomes}
    outputs = []
    for event in events:
        if event.get("polarity") != "positive" or event.get("useful") is not True:
            continue
        observed = event.get("observed_ns")
        if observed not in sample_times or sample_times.index(observed) == 0:
            lower = None
        else:
            lower = sample_times[sample_times.index(observed) - 1]
        upper = observed
        possible = set()
        malformed = False
        if lower is None:
            malformed = True
        else:
            for row in rows:
                if row is None:
                    malformed = True
                    continue
                # A held key is possible any time after the DOWN interval starts
                # and until the UP transition is certainly complete.
                if row["down"][0] <= upper and row["up"][1] > lower:
                    possible.add(row["token"])
            exact = exact_by_sequence.get(event.get("event_sequence"), {})
            exact_tokens = exact.get("possible_intent_tokens", [])
            if exact.get("status") == "TEMPORALLY_UNIQUE" and exact.get("intent_token"):
                exact_tokens = [exact["intent_token"]]
            possible.update(hashlib.sha256(token.encode("utf-8")).hexdigest()
                            for token in exact_tokens)
        if len(possible) > 1:
            status, reason = "AMBIGUOUS", "multiple_measured_intent_envelopes_intersect"
        else:
            status = "UNRESOLVED"
            reason = ("measured_edge_envelope_not_exact_occupancy" if possible
                      else "no_measured_intent_envelope_intersects")
            if malformed:
                reason = "incomplete_measured_interval_evidence"
        outputs.append({
            "event_sequence": event.get("event_sequence"), "kind": event.get("kind"),
            "detection_interval_ns": [lower, upper] if lower is not None else None,
            "status": status, "reason": reason,
            "possible_intent_token_sha256": sorted(possible), "intent_token": None,
            "causal_attribution": "NOT_ESTABLISHED",
        })
    return outputs


def adapt_session_records(sample_rows, event_rows, input_rows):
    """Normalize V15 sink/backend rows and apply the frozen temporal gate.

    Joins down/up receipts only by exact (owner, intent, program, step, key).
    Incomplete key-up receipts remain possible overlaps, never verified ends.
    Any unbound admission or orphan release suppresses unique labels globally.
    """
    if not isinstance(sample_rows, list) or not isinstance(event_rows, list) or not isinstance(input_rows, list):
        raise ValueError("producer streams must be lists")
    samples=_normalize_samples(sample_rows)
    for event in event_rows:
        if not isinstance(event,dict) or event.get("schema")!=EVENT_SCHEMA or event.get("controller_visible") is not False:
            raise ValueError("scorer event must use the controller-invisible T0 schema")

    downs={}
    ups={}
    integrity=[]
    admission_count=0
    release_count=0
    for row in input_rows:
        if not isinstance(row,dict):
            integrity.append("malformed_input_row")
            continue
        kind=row.get("event")
        if kind=="input_admission":
            admission_count+=1
            identity=_identity(row)
            admitted=row.get("admitted_ns")
            ack=row.get("input_ack_ns")
            if identity is None or not _integer(admitted) or not _integer(ack) or ack < admitted:
                integrity.append("unbound_input_admission")
                continue
            if identity in downs:
                integrity.append("duplicate_input_admission")
                continue
            downs[identity]=row
        elif kind=="input_release_transition":
            release_count+=1
            identity=_identity(row)
            if identity is None:
                integrity.append("unbound_key_release")
                continue
            if identity in ups:
                integrity.append("duplicate_key_release")
                continue
            ups[identity]=row

    release_batches=defaultdict(list)
    for identity,row in ups.items():
        batch_id=row.get("release_batch_identifier")
        batch_step=row.get("release_batch_step")
        size=row.get("release_batch_size")
        position=row.get("release_batch_position")
        if (not isinstance(batch_id,str) or not batch_id or batch_step!=identity[3]
            or not _integer(size) or size<1 or not _integer(position) or position>=size
            or row.get("release_batch_complete") is not True):
            integrity.append("incomplete_release_batch")
            continue
        release_batches[(identity[0],identity[1],identity[2],batch_id)].append((size,position))
    for members in release_batches.values():
        sizes={size for size,_ in members}
        positions=[position for _,position in members]
        expected=next(iter(sizes)) if len(sizes)==1 else None
        if (expected is None or len(members)!=expected
            or len(set(positions))!=expected or set(positions)!=set(range(expected))):
            integrity.append("incomplete_release_batch")

    orphan=set(ups)-set(downs)
    if orphan:
        integrity.append("orphan_key_release")
    horizon=max((row.get("sample_ns",0) for row in samples),default=0)
    intervals=[]
    unverified=0
    for identity,down in downs.items():
        up=ups.get(identity)
        if up is None:
            release_ns=max(down["admitted_ns"],horizon)
            verified=False
        else:
            release_ns,verified=_verified_up(up,down,identity)
            if release_ns is None:
                release_ns=max(down["admitted_ns"],horizon)
                verified=False
        if not verified:
            unverified+=1
        intervals.append({
            "intent_token":identity[1], "key":identity[4],
            "admitted_ns":down["admitted_ns"], "release_sync_ns":release_ns,
            "release_verified":verified,
        })

    measured_rows = []
    for row in input_rows:
        if (isinstance(row, dict)
            and row.get("status") in {
                "adapter_edge_brackets_paired", "adapter_edge_receipt_incomplete"
            }
            and "down_edge_interval_ns" in row
            and "up_edge_interval_ns" in row):
            measured_rows.append(row)

    if integrity:
        if "unbound_input_admission" in integrity or "unbound_key_release" in integrity:
            trace_integrity="HOLD_UNBOUND_INPUT_IDENTITY"
        elif "incomplete_release_batch" in integrity:
            trace_integrity="HOLD_INCOMPLETE_RELEASE_BATCH"
        elif "orphan_key_release" in integrity:
            trace_integrity="HOLD_UNMATCHED_RELEASE_IDENTITY"
        else:
            trace_integrity="HOLD_DUPLICATE_OR_MALFORMED_INPUT_RECORD"
        attributions=_unresolved(event_rows,"input_trace_identity_or_completeness_hold")
    elif measured_rows:
        trace_integrity = "MEASURED_INTERVALS_ONLY"
        attributions = _measured_interval_outcomes(
            samples, event_rows, measured_rows, intervals)
    else:
        trace_integrity="SOURCE_ROWS_JOINED"
        attributions=attribute_positive_events(samples,event_rows,intervals)

    return {
        "schema":"v15-scorer-input-attribution-adapter-v1",
        "trace_integrity":trace_integrity,
        "counts":{
            "scorer_samples":len(samples),
            "scorer_events":len(event_rows),
            "input_admissions":admission_count,
            "key_release_receipts":release_count,
            "candidate_key_intervals":len(intervals),
            "unverified_or_censored_key_intervals":unverified,
            "integrity_flags":sorted(set(integrity)),
        },
        "attributions":attributions,
    }
