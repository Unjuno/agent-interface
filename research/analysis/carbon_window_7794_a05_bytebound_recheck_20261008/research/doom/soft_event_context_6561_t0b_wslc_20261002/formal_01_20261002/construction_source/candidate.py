"""Finite advisory context projector; it cannot authorize input."""
from __future__ import annotations
import copy
import json
import math
import sys
from pathlib import Path

CASE_KEYS={"case_id","history_state","current_sequence","binding","raw_events","invalidation_receipt"}
EVENT_KEYS={"sequence","signal","outcome"}
SIGNAL_KEYS={"status","signal_id","value","binding","capture_ns"}
OUTCOME_KEYS={"format","guard_id","signal_id","status","reason","source_value","current_value","hard_minimum","source_age_ms","max_source_age_ms","keep_existing_policy","requires_new_decision","grants_input_authority","may_only_preserve_or_reduce_existing_authority","semantic_change_identified","task_success_verified"}
RECEIPT_KEYS=OUTCOME_KEYS|{"sequence","binding"}
PROMPT_PREFIX="Latest observed soft evidence (advisory only): "


def _int(v): return type(v) is int
def _unknown(reason): return {"state":"UNKNOWN","reason":reason}


def _valid_common(case, fixture_binding):
    return (type(case) is dict and set(case)==CASE_KEYS
        and type(case.get("binding")) is dict and case["binding"]==fixture_binding
        and _int(case.get("current_sequence")) and case["current_sequence"]>=0
        and type(case.get("raw_events")) is list)


def _valid_soft_event(event, expected_binding, current_sequence, previous_sequence):
    if type(event) is not dict or set(event)!=EVENT_KEYS: return False
    seq=event.get("sequence"); signal=event.get("signal"); outcome=event.get("outcome")
    if not _int(seq) or seq<=previous_sequence or seq>=current_sequence: return False
    if type(signal) is not dict or set(signal)!=SIGNAL_KEYS or type(outcome) is not dict or set(outcome)!=OUTCOME_KEYS: return False
    age=outcome.get("source_age_ms"); maximum=outcome.get("max_source_age_ms")
    source=outcome.get("source_value"); current=signal.get("value"); floor=outcome.get("hard_minimum")
    return (signal.get("binding")==expected_binding and signal.get("status")=="observed"
        and signal.get("signal_id")=="health" and _int(signal.get("capture_ns")) and signal["capture_ns"]>0
        and outcome.get("format")=="observable-signal-guard-outcome-v1"
        and outcome.get("signal_id")=="health" and outcome.get("status")=="SOFT_CHANGED"
        and outcome.get("reason")=="within_validity_envelope"
        and type(outcome.get("guard_id")) is str and 1<=len(outcome["guard_id"])<=64
        and _int(source) and _int(current) and _int(floor) and floor<=current<=source<=1_000_000
        and outcome.get("current_value")==current and type(age) in (int,float) and not isinstance(age,bool)
        and math.isfinite(age) and _int(maximum) and 100<=maximum<=30000 and 0<=age<=maximum
        and outcome.get("keep_existing_policy") is True and outcome.get("requires_new_decision") is False
        and outcome.get("grants_input_authority") is False
        and outcome.get("may_only_preserve_or_reduce_existing_authority") is True
        and outcome.get("semantic_change_identified") is True
        and outcome.get("task_success_verified") is False)


def _valid_invalidation(case, fixture_binding):
    receipt=case.get("invalidation_receipt"); state=case.get("history_state")
    if type(receipt) is not dict or set(receipt)!=RECEIPT_KEYS: return False
    seq=receipt.get("sequence"); current_seq=case["current_sequence"]
    age=receipt.get("source_age_ms"); maximum=receipt.get("max_source_age_ms")
    src=receipt.get("source_value"); current=receipt.get("current_value"); floor=receipt.get("hard_minimum")
    common=(receipt.get("binding")==fixture_binding and _int(seq) and 0<=seq<current_seq
        and type(receipt.get("guard_id")) is str and 1<=len(receipt["guard_id"])<=64
        and receipt.get("format")=="observable-signal-guard-outcome-v1"
        and receipt.get("signal_id")=="health" and _int(src) and _int(floor) and floor<=src<=1_000_000
        and _int(maximum) and 100<=maximum<=30000
        and receipt.get("keep_existing_policy") is False and receipt.get("requires_new_decision") is True
        and receipt.get("grants_input_authority") is False
        and receipt.get("may_only_preserve_or_reduce_existing_authority") is True
        and receipt.get("task_success_verified") is False)
    if not common: return False
    if state=="invalidated":
        return (receipt.get("status")=="HARD_INVALIDATED" and receipt.get("reason")=="below_hard_minimum"
            and _int(current) and 0<=current<floor and type(age) in (int,float)
            and not isinstance(age,bool) and math.isfinite(age) and 0<=age<=maximum
            and receipt.get("semantic_change_identified") is True)
    if state=="unknown":
        return (receipt.get("status")=="UNKNOWN" and receipt.get("reason")=="signal_unavailable"
            and current is None and age is None and receipt.get("semantic_change_identified") is False)
    if state=="expired":
        return (receipt.get("status")=="UNKNOWN" and receipt.get("reason")=="source_expired"
            and _int(current) and floor<=current<=src and type(age) in (int,float)
            and not isinstance(age,bool) and math.isfinite(age) and age>maximum
            and receipt.get("semantic_change_identified") is False)
    return False


def project_case(case, fixture_binding):
    if not _valid_common(case,fixture_binding): return _unknown("invalid_case_source")
    state=case["history_state"]; events=case["raw_events"]
    if state=="none":
        return {"state":"NONE"} if not events and case["invalidation_receipt"] is None else _unknown("none_with_history")
    if state=="observed":
        if case["invalidation_receipt"] is not None or not events or len(events)>128: return _unknown("invalid_soft_history")
        prev=-1
        for event in events:
            if not _valid_soft_event(event,fixture_binding,case["current_sequence"],prev): return _unknown("invalid_soft_receipt")
            prev=event["sequence"]
        latest=events[-1]; sig=latest["signal"]; out=latest["outcome"]
        return {"state":"OBSERVED","sequence":latest["sequence"],"signal_id":"health",
            "source_value":out["source_value"],"current_value":sig["value"],"source_age_ms":out["source_age_ms"],
            "guard_id":out["guard_id"],"outcome":"SOFT_CHANGED","soft_event_count":len(events),
            "grants_input_authority":False,"task_success_verified":False}
    if state in {"invalidated","unknown","expired"} and not events and _valid_invalidation(case,fixture_binding):
        return _unknown(state)
    return _unknown("invalid_receipt")


def build_packet(fixture):
    binding=fixture["fixture_binding"]; rows=[]
    for case in fixture["cases"]:
        context=project_case(case,binding)
        rows.append({**copy.deepcopy(case),"context":context,
            "prompt":PROMPT_PREFIX+json.dumps(context,sort_keys=True,separators=(",",":"))+"\n"})
    return {"schema":"soft-event-context-6561-t0b-packet-v1","cases":rows}


def main(argv):
    if len(argv)!=3: print("usage: candidate.py CASES.json NEW_PACKET.json",file=sys.stderr); return 2
    out=Path(argv[2])
    if out.exists(): print("STOP_OUTPUT_ALREADY_EXISTS",file=sys.stderr); return 2
    try:
        fixture=json.loads(Path(argv[1]).read_text(encoding="utf-8")); packet=build_packet(fixture)
        out.write_text(json.dumps(packet,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    except (OSError,json.JSONDecodeError,ValueError,TypeError) as exc:
        print(f"FAIL_CANDIDATE: {exc}",file=sys.stderr); return 1
    print("CANDIDATE_COMPLETE cases=6"); return 0


if __name__=="__main__": raise SystemExit(main(sys.argv))
