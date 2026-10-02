"""Independent raw-only exhaustive oracle; does not import candidate.py."""
import copy
import hashlib
import itertools
import json
import sys
from collections import defaultdict, Counter
from pathlib import Path


def canon(x): return json.dumps(x, sort_keys=True, separators=(",", ":"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def legal_completions(spec):
    results=[]
    for a,b,g,opt in itertools.product(spec["mandatory_values"],spec["mandatory_values"],spec["generation_values"],spec["optional_streams"]):
        q=(({"source":"target","type":"result","value":a,"generation":spec["generation"]},),
           ({"source":"effect","type":"result","value":b,"generation":spec["generation"]},),
           ({"source":"generation","type":"status","value":g,"generation":spec["generation"]},),tuple(opt))
        def visit(pos,prefix):
            if all(pos[i] == len(q[i]) for i in range(len(q))):
                results.append(list(prefix)); return
            for i,stream in enumerate(q):
                if pos[i] < len(stream):
                    nxt=list(pos); event=stream[pos[i]]; nxt[i]+=1
                    visit(tuple(nxt),prefix+(event,))
        visit((0,0,0,0),())
    return results


def final_value(trace):
    mandatory={}
    generation=None
    opt=[]
    for event in trace:
        if event["source"] in ("target","effect"): mandatory[event["source"]]=event["value"]
        elif event["source"]=="generation": generation=event["value"]
        else: opt.append(event)
    if generation!="CURRENT": return "UNKNOWN"
    if "FAIL" in mandatory.values(): return "FAIL"
    if len(mandatory)!=2 or any(x!="PASS" for x in mandatory.values()): return "UNKNOWN"
    if any(x.get("type")=="note" and x.get("value")=="CONFLICT" for x in opt): return "FAIL"
    if any(x.get("type")=="frontier" and x.get("value")=="COMPLETE" for x in opt): return "PASS"
    return "UNKNOWN"


def expected_pending(prefix):
    got={(e["source"],e["type"]):e["value"] for e in prefix}
    out=[]
    for source in ("target","effect"):
        if (source,"result") not in got: out.append("mandatory:"+source)
    if ("generation","status") not in got: out.append("generation_status")
    if got.get(("optional","frontier"))!="COMPLETE": out.append("optional_frontier_completion")
    return sorted(out)


def expected_class(prefix, outcomes):
    if len(outcomes)==1:
        return {"PASS":"STABLE_PASS","FAIL":"STABLE_FAIL","UNKNOWN":"STABLE_UNKNOWN"}[outcomes[0]]
    got={(e["source"],e["type"]):e["value"] for e in prefix}
    if all(got.get((s,"result"))=="PASS" for s in ("target","effect")) and got.get(("generation","status"))=="CURRENT" and ("optional","frontier") not in got:
        return "CLOSED_FRONTIER_REQUIRED"
    return "PROVISIONAL"


def reconstruct(spec):
    traces=legal_completions(spec); groups=defaultdict(list)
    for trace in traces:
        for n in range(len(trace)+1): groups[canon(trace[:n])].append(trace)
    rows=[]
    for key,futures in groups.items():
        p=json.loads(key); outs=sorted({final_value(x) for x in futures}); lab=expected_class(p,outs)
        rows.append({"prefix":p,"classification":lab,"reachable_terminal_dispositions":outs,
                     "legal_continuation_count":len(futures),"terminal_prefix":all(len(p)==len(x) for x in futures),
                     "pending_obligations":expected_pending(p),"claim":spec["claim"],
                     "consumer_authority":False,"consumer_side_effects":0})
    rows.sort(key=lambda r:(len(r["prefix"]),canon(r["prefix"])))
    d=dict(sorted(Counter(r["classification"] for r in rows).items()))
    e=dict(sorted(Counter("EARLY_"+r["reachable_terminal_dispositions"][0] for r in rows if not r["terminal_prefix"] and r["classification"].startswith("STABLE_")).items()))
    return traces,rows,d,e


def audit(spec, raw, fixture_path):
    errors=[]; traces,rows,d,e=reconstruct(spec)
    if raw.get("schema")!="prefix-stability-successor-6749-raw-v1": errors.append("schema")
    if raw.get("fixture_sha256")!=sha(fixture_path): errors.append("fixture_hash")
    if raw.get("world_count")!=32: errors.append("world_count")
    if raw.get("trace_count")!=len(traces): errors.append("trace_count")
    if raw.get("unique_prefix_count")!=len(rows): errors.append("prefix_count")
    if raw.get("disposition_counts")!=d: errors.append("disposition_counts")
    if raw.get("early_finalization_metrics")!=e: errors.append("early_finalization_metrics")
    if raw.get("authority_grants")!=0 or raw.get("consumer_side_effects")!=0: errors.append("authority_or_effect")
    expected={canon(r["prefix"]):r for r in rows}; seen={}
    for r in raw.get("rows",[]):
        k=canon(r.get("prefix"))
        if k in seen: errors.append("duplicate_prefix")
        seen[k]=r
    if set(seen)!=set(expected): errors.append("prefix_inventory")
    for k in set(seen)&set(expected):
        if seen[k]!=expected[k]: errors.append("row_mismatch")
    # Explicit contract witness: decisive current-generation failure stays stable,
    # but any mandatory source not yet seen remains pending.
    witnesses=[r for r in rows if r["classification"]=="STABLE_FAIL" and not r["terminal_prefix"] and
               {(x["source"],x["type"]):x["value"] for x in r["prefix"]}.get(("generation","status"))=="CURRENT" and
               any(x["value"]=="FAIL" and x["source"] in ("target","effect") for x in r["prefix"])]
    if not witnesses: errors.append("missing_stable_fail_witness")
    if not any(any(o.startswith("mandatory:") for o in r["pending_obligations"]) for r in witnesses): errors.append("stable_fail_lost_pending_mandatory")
    for r in rows:
        if r["classification"]=="STABLE_PASS":
            s={(x["source"],x["type"]):x["value"] for x in r["prefix"]}
            if not (all(s.get((x,"result"))=="PASS" for x in ("target","effect")) and s.get(("generation","status"))=="CURRENT" and s.get(("optional","frontier"))=="COMPLETE"):
                errors.append("pass_before_full_frontier"); break
    return errors


def mutate(raw,name):
    x=copy.deepcopy(raw)
    if name=="drop_pending_mandatory":
        r=next(r for r in x["rows"] if r["classification"]=="STABLE_FAIL" and any(o.startswith("mandatory:") for o in r["pending_obligations"]))
        r["pending_obligations"]=[o for o in r["pending_obligations"] if not o.startswith("mandatory:")]
    elif name=="mix_derived_metric":
        x["disposition_counts"]["EARLY_FAIL"]=x["early_finalization_metrics"].get("EARLY_FAIL",0)
    elif name=="forge_complete":
        r=next(r for r in x["rows"] if any(e["source"]=="optional" and e["value"]=="TIMEOUT" for e in r["prefix"]))
        for event in r["prefix"]:
            if event["source"]=="optional": event["value"]="COMPLETE"; event["type"]="frontier"; break
    elif name=="stale_as_current":
        r=next(r for r in x["rows"] if any(e["source"]=="generation" and e["value"]=="INVALID" for e in r["prefix"]))
        for event in r["prefix"]:
            if event["source"]=="generation": event["value"]="CURRENT"; break
    elif name=="timeout_as_complete":
        r=next(r for r in x["rows"] if any(e["source"]=="optional" and e["value"]=="TIMEOUT" for e in r["prefix"]))
        for event in r["prefix"]:
            if event["source"]=="optional": event["value"]="COMPLETE"; break
    return x


def main():
    fixture,raw_path,out=map(Path,sys.argv[1:4]); spec=json.loads(fixture.read_text()); raw=json.loads(raw_path.read_text())
    errors=audit(spec,raw,fixture)
    controls={name:bool(audit(spec,mutate(raw,name),fixture)) for name in
              ("drop_pending_mandatory","mix_derived_metric","forge_complete","stale_as_current","timeout_as_complete")}
    if not all(controls.values()): errors.append("mutation_control")
    report={"status":"PASS_METHOD_SCOPED" if not errors else "FAIL_AUDIT","errors":errors,
            "mutation_rejected":controls,"row_count":raw.get("unique_prefix_count"),
            "trace_count":raw.get("trace_count"),"disposition_counts":raw.get("disposition_counts"),
            "early_finalization_metrics":raw.get("early_finalization_metrics"),
            "auditor_sha256":sha(Path(__file__)),"fixture_sha256":sha(fixture),
            "candidate_raw_sha256":sha(raw_path),"authority_grants":0,"consumer_side_effects":0,
            "scope":"independent exhaustive audit of a finite authored evidence model; no runtime, GUI, model, or human data"}
    out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps(report,sort_keys=True))
    raise SystemExit(0 if not errors else 2)


if __name__=="__main__": main()
