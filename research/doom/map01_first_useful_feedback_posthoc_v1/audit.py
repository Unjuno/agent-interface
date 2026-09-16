#!/usr/bin/env python3
"""Read-only independent selection audit for #503 result.
Shared primitive HUD reader is frozen, but inventory/window/earliest selection are recomputed here.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from hud_independent import IndependentHudReader, locate_wad, sha256
from analyze import load_events, inventory, resolve_png, typed_values, rgb_sha

def audit(result_path, repo):
    result=json.loads(Path(result_path).read_text()); errors=[]
    reader=IndependentHudReader(locate_wad())
    for rr in result["runs"]:
        root=Path(repo)/"research/doom/results"/rr["run"]
        report=json.loads((root/"report.json").read_text()); events=load_events(root/"runtime/events.jsonl")
        if rr["report_sha256"]!=sha256(root/"report.json") or rr["events_sha256"]!=sha256(root/"runtime/events.jsonl"):
            errors.append(f"{rr['run']}: source hash"); continue
        obs={x["sequence"]:x for x in events if x.get("event")=="observation"}; typed={x["sequence"]:x for x in events if x.get("event")=="typed_observation"}
        expected_inv=inventory(report,events)
        if result["mode"]=="construction": expected_inv=expected_inv[:1]
        actual={p["iteration"]:p for p in rr["plans"]}
        if [x["iteration"] for x in expected_inv] != [p["iteration"] for p in rr["plans"]]: errors.append(f"{rr['run']}: inventory"); continue
        for inv in expected_inv:
            p=actual[inv["iteration"]]; b=obs[inv["baseline_sequence"]]; bpng=resolve_png(root,b)
            base_reader=reader.read(bpng,b["pointer_binding"]); base={k:v["value"] if v["status"]=="observed" else None for k,v in base_reader.items()}
            if base!=p["baseline_independent"] or base!=typed_values(typed[b["sequence"]]): errors.append(f"{rr['run']}:{inv['iteration']}: baseline")
            cand=sorted([x for x in obs.values() if inv["accepted_ns"]<=x["capture_ns"]<=inv["terminal_ns"]],key=lambda x:(x["capture_ns"],x["sequence"]))
            earliest=None
            for x in cand:
                png=resolve_png(root,x); got=reader.read(png,x["pointer_binding"]); vals={k:v["value"] if v["status"]=="observed" else None for k,v in got.items()}
                if rgb_sha(png)!=x["frame_rgb_sha256"] or vals!=typed_values(typed[x["sequence"]]): errors.append(f"{rr['run']}:{inv['iteration']}: obs {x['sequence']}")
                changed=[k for k in ("health","ammo") if vals[k]!=base[k]]
                if changed and earliest is None:
                    earliest={"sequence":x["sequence"],"capture_ns":x["capture_ns"],"accepted_to_feedback_ms":(x["capture_ns"]-inv["accepted_ns"])/1e6,"changed":changed,"from":base,"to":vals}
            if earliest!=p["earliest_state_feedback"]: errors.append(f"{rr['run']}:{inv['iteration']}: earliest")
            if p["stronger_task_effect_feedback"] is not None: errors.append(f"{rr['run']}:{inv['iteration']}: unsupported stronger effect")
    state=all(p["earliest_state_feedback"] is not None for r in result["runs"] for p in r["plans"])
    strong=all(p["stronger_task_effect_feedback"] is not None for r in result["runs"] for p in r["plans"])
    decision="SCHEMA_INSUFFICIENT_FIRST_USEFUL_FEEDBACK" if not state else ("RETAIN_STATE_FEEDBACK_ONLY_SCHEMA_LIMIT" if not strong else "RETAIN_FIRST_TASK_RELEVANT_FEEDBACK_SCOPED")
    if decision!=result["decision"]: errors.append("decision")
    return {"pass":not errors,"errors":errors,"decision":decision,"plans":sum(len(r["plans"]) for r in result["runs"])}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("result");ap.add_argument("--repo",required=True);ap.add_argument("--out");a=ap.parse_args(); value=audit(a.result,a.repo)
    if a.out: Path(a.out).write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")
    print(json.dumps(value,sort_keys=True)); raise SystemExit(0 if value["pass"] else 1)
if __name__=="__main__":main()
