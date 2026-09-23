from __future__ import annotations
import json,hashlib
from collections import defaultdict
from oracle import acceptable_from_facts
from schema import VISIBLE_KEYS,FORBIDDEN_VISIBLE_KEYS,EXECUTABLE,disp_key

def validate(rows, expected_rows=None, expected_units=None):
    errors=[]; positives=negatives=noact=yieldn=alternatives=0; ops=set(); units=set(); split_units=defaultdict(set); signatures=defaultdict(set)
    for row in rows:
        units.add(row["scenario_unit_id"]); split_units[row["split"]].add(row["scenario_unit_id"])
        pkt=row["candidate_input"]
        if set(pkt)!=VISIBLE_KEYS: errors.append([row["row_id"],"visible_keys"])
        if set(pkt)&FORBIDDEN_VISIBLE_KEYS: errors.append([row["row_id"],"leakage"])
        exp=acceptable_from_facts(row["oracle_facts"])
        if sorted(map(disp_key,exp))!=sorted(map(disp_key,row["acceptable"])): errors.append([row["row_id"],"oracle_mismatch"])
        if row.get("grants_input_authority") is not False: errors.append([row["row_id"],"authority"])
        execs=[d for d in exp if d["op"] in EXECUTABLE]
        if execs: positives+=1; ops.update(d["op"] for d in execs)
        else: negatives+=1
        noact += any(d["op"]=="NO_LOCAL_ACTION" for d in exp)
        yieldn += any(d["op"]=="YIELD" for d in exp)
        alternatives += len(execs)>=2
        sig=json.dumps(pkt,sort_keys=True,separators=(",",":"))
        signatures[sig].add(tuple(sorted(disp_key(d) for d in exp)))
    alias=sum(1 for v in signatures.values() if len(v)>1)
    if alias: errors.append(["corpus","alias_groups",alias])
    if split_units["train"] & split_units["eval"]: errors.append(["corpus","split_leakage"])
    if expected_rows is not None and len(rows)!=expected_rows: errors.append(["corpus","rows",len(rows)])
    if expected_units is not None and len(units)!=expected_units: errors.append(["corpus","units",len(units)])
    stats={"rows":len(rows),"scenario_units":len(units),"positives":positives,"semantic_negatives":negatives,"no_local_action":noact,"yield":yieldn,"target_alternative_rows":alternatives,"executable_operation_families":sorted(ops),"alias_groups":alias,"train_units":len(split_units['train']),"eval_units":len(split_units['eval'])}
    return errors,stats
