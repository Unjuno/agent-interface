"""Independent raw-only auditor; fixture truth is a separate read-only input."""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path

PROMPT_PREFIX="Latest observed soft evidence (advisory only): "
PACKET_KEYS={"schema","cases"}
ROW_KEYS={"case_id","history_state","current_sequence","binding","raw_events","invalidation_receipt","context","prompt"}


def _unknown(reason): return {"state":"UNKNOWN","reason":reason}
def _int(v): return type(v) is int


def derive(case, expected_binding):
    state=case["history_state"]; seq_now=case["current_sequence"]; events=case["raw_events"]; receipt=case["invalidation_receipt"]
    if not _int(seq_now) or seq_now<0 or case["binding"]!=expected_binding: return _unknown("invalid_case_source")
    if state=="none": return {"state":"NONE"} if events==[] and receipt is None else _unknown("none_with_history")
    if state=="observed":
        if receipt is not None or type(events) is not list or not 1<=len(events)<=128: return _unknown("invalid_soft_history")
        prior=-1
        for e in events:
            if type(e) is not dict or set(e)!={"sequence","signal","outcome"}: return _unknown("invalid_soft_receipt")
            n=e["sequence"]; s=e["signal"]; o=e["outcome"]
            if not _int(n) or not prior<n<seq_now or type(s) is not dict or type(o) is not dict: return _unknown("invalid_soft_receipt")
            age=o.get("source_age_ms"); maximum=o.get("max_source_age_ms"); src=o.get("source_value"); val=s.get("value"); floor=o.get("hard_minimum")
            flags=(o.get("keep_existing_policy") is True and o.get("requires_new_decision") is False and o.get("grants_input_authority") is False and o.get("may_only_preserve_or_reduce_existing_authority") is True and o.get("semantic_change_identified") is True and o.get("task_success_verified") is False)
            if (set(s)!={"status","signal_id","value","binding","capture_ns"} or set(o)!={"format","guard_id","signal_id","status","reason","source_value","current_value","hard_minimum","source_age_ms","max_source_age_ms","keep_existing_policy","requires_new_decision","grants_input_authority","may_only_preserve_or_reduce_existing_authority","semantic_change_identified","task_success_verified"}
                or s.get("binding")!=expected_binding or s.get("status")!="observed" or s.get("signal_id")!="health"
                or not _int(s.get("capture_ns")) or s["capture_ns"]<=0 or o.get("format")!="observable-signal-guard-outcome-v1"
                or o.get("signal_id")!="health" or o.get("status")!="SOFT_CHANGED" or o.get("reason")!="within_validity_envelope"
                or type(o.get("guard_id")) is not str or not 1<=len(o["guard_id"])<=64
                or not _int(src) or not _int(val) or not _int(floor) or not floor<=val<=src<=1_000_000 or o.get("current_value")!=val
                or type(age) not in (int,float) or isinstance(age,bool) or not math.isfinite(age) or not _int(maximum) or not 100<=maximum<=30000 or not 0<=age<=maximum or not flags):
                return _unknown("invalid_soft_receipt")
            prior=n
        last=events[-1]; s=last["signal"]; o=last["outcome"]
        return {"state":"OBSERVED","sequence":last["sequence"],"signal_id":"health","source_value":o["source_value"],
            "current_value":s["value"],"source_age_ms":o["source_age_ms"],"guard_id":o["guard_id"],"outcome":"SOFT_CHANGED",
            "soft_event_count":len(events),"grants_input_authority":False,"task_success_verified":False}
    if state not in {"invalidated","unknown","expired"} or events!=[] or type(receipt) is not dict: return _unknown("invalid_receipt")
    if set(receipt)!={"sequence","binding","guard_id","format","signal_id","status","reason","source_value","current_value","hard_minimum","source_age_ms","max_source_age_ms","keep_existing_policy","requires_new_decision","grants_input_authority","may_only_preserve_or_reduce_existing_authority","semantic_change_identified","task_success_verified"}:
        return _unknown("invalid_receipt")
    n=receipt["sequence"]; age=receipt["source_age_ms"]; maximum=receipt["max_source_age_ms"]; src=receipt["source_value"]; val=receipt["current_value"]; floor=receipt["hard_minimum"]
    common=(receipt["binding"]==expected_binding and _int(n) and 0<=n<seq_now and type(receipt["guard_id"]) is str and 1<=len(receipt["guard_id"])<=64
        and receipt["format"]=="observable-signal-guard-outcome-v1" and receipt["signal_id"]=="health" and _int(src) and _int(floor) and floor<=src<=1_000_000
        and _int(maximum) and 100<=maximum<=30000 and receipt["keep_existing_policy"] is False and receipt["requires_new_decision"] is True
        and receipt["grants_input_authority"] is False and receipt["may_only_preserve_or_reduce_existing_authority"] is True and receipt["task_success_verified"] is False)
    if not common: return _unknown("invalid_receipt")
    if state=="invalidated":
        good=(receipt["status"]=="HARD_INVALIDATED" and receipt["reason"]=="below_hard_minimum" and _int(val) and 0<=val<floor
            and type(age) in (int,float) and not isinstance(age,bool) and math.isfinite(age) and 0<=age<=maximum and receipt["semantic_change_identified"] is True)
    elif state=="unknown":
        good=(receipt["status"]=="UNKNOWN" and receipt["reason"]=="signal_unavailable" and val is None and age is None and receipt["semantic_change_identified"] is False)
    else:
        good=(receipt["status"]=="UNKNOWN" and receipt["reason"]=="source_expired" and _int(val) and floor<=val<=src
            and type(age) in (int,float) and not isinstance(age,bool) and math.isfinite(age) and age>maximum and receipt["semantic_change_identified"] is False)
    return _unknown(state) if good else _unknown("invalid_receipt")


def audit_packet(packet, fixture):
    if type(packet) is not dict or set(packet)!=PACKET_KEYS or packet.get("schema")!="soft-event-context-6561-t0b-packet-v1": raise ValueError("packet_schema")
    source=fixture.get("cases"); binding=fixture.get("fixture_binding"); rows=packet.get("cases")
    if type(source) is not list or type(binding) is not dict or type(rows) is not list or len(rows)!=len(source): raise ValueError("fixture_or_denominator")
    expected_ids={c.get("case_id") for c in source}
    if len(expected_ids)!=6 or expected_ids!={"NONE","ONE_SOFT","MULTI_SOFT","HARD","UNKNOWN","EXPIRED"}: raise ValueError("fixture_case_set")
    seen=set(); raw_keys={"case_id","history_state","current_sequence","binding","raw_events","invalidation_receipt"}
    for row in rows:
        if type(row) is not dict or set(row)!=ROW_KEYS: raise ValueError("row_schema")
        cid=row.get("case_id")
        if cid in seen or cid not in expected_ids: raise ValueError("row_id")
        seen.add(cid); expected_case=next(c for c in source if c["case_id"]==cid)
        raw={k:row[k] for k in raw_keys}
        if raw!=expected_case: raise ValueError(f"{cid}:raw_input_not_fixture_bound")
        expected=derive(expected_case,binding)
        if row["context"]!=expected: raise ValueError(f"{cid}:context_mismatch")
        if expected.get("state")=="OBSERVED" and (expected.get("grants_input_authority") is not False or expected.get("task_success_verified") is not False): raise ValueError("authority_or_success")
        prompt=PROMPT_PREFIX+json.dumps(expected,sort_keys=True,separators=(",",":"))+"\n"
        if row["prompt"]!=prompt: raise ValueError(f"{cid}:prompt_mismatch")
    if seen!=expected_ids: raise ValueError("row_denominator")
    return {"status":"PASS_METHOD_SCOPED","case_count":len(rows),"errors":[],"model_calls":0,"external_effects":0}


def main(argv):
    if len(argv)!=4: print("usage: auditor.py CASES.json RAW_PACKET.json AUDIT.json",file=sys.stderr); return 2
    try:
        fixture=json.loads(Path(argv[1]).read_text(encoding="utf-8")); packet=json.loads(Path(argv[2]).read_text(encoding="utf-8"))
        result=audit_packet(packet,fixture); Path(argv[3]).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    except (OSError,json.JSONDecodeError,ValueError,TypeError) as exc:
        result={"status":"FAIL_AUDIT","case_count":0,"errors":[str(exc)],"model_calls":0,"external_effects":0}
        Path(argv[3]).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        print(f"FAIL_AUDIT: {exc}",file=sys.stderr); return 1
    print(json.dumps(result,sort_keys=True)); return 0


if __name__=="__main__": raise SystemExit(main(sys.argv))
