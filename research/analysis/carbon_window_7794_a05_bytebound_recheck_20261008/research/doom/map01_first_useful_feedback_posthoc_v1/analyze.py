#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from hud_independent import IndependentHudReader, locate_wad, sha256, WAD_SHA256

RUNS = ("map01-v38-integrated-threat-live-01", "map01-v39-coast-liveness-live-01")

def load_events(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]

def jdump(path,obj):
    Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")

def rgb_sha(path):
    from PIL import Image
    with Image.open(path) as im:
        return hashlib.sha256(im.convert("RGB").tobytes()).hexdigest()

def inventory(report, events):
    accepted={r["id"]:r for r in events if r.get("event")=="accepted"}
    terminals={r["id"]:r for r in events if r.get("event")=="terminal"}
    out=[]
    for d in report["decisions"]:
        adm=d.get("final_action_admission") or {}
        if adm.get("status") != "INPUT_ADMITTED":
            continue
        exe=adm["executor_admission"]
        snap=adm["action_validity"]["snapshot"]
        identifier=exe["id"]
        if identifier not in accepted or identifier not in terminals:
            raise AssertionError(f"admitted decision {d['iteration']} missing retained program lifecycle {identifier}")
        if accepted[identifier]["accepted_ns"] != exe["accepted_ns"]:
            raise AssertionError(f"admitted decision {d['iteration']} accepted_ns mismatch")
        terminal=terminals[identifier]["terminal_ns"]
        if terminal < exe["accepted_ns"]:
            raise AssertionError(f"admitted decision {d['iteration']} terminal precedes admission")
        out.append({"iteration":d["iteration"],"id":identifier,"accepted_ns":exe["accepted_ns"],
                    "terminal_ns":terminal,"baseline_sequence":snap["sequence"],
                    "report_snapshot":snap["signals"]})
    return out

def resolve_png(runroot, obs):
    return Path(runroot)/"runtime"/Path(obs["image"]).name

def typed_values(row):
    return {k:(v.get("value") if v.get("status")=="observed" else None) for k,v in row["signals"].items() if k in ("health","ammo")}

def analyze_run(repo, run, reader, construction=False):
    root=Path(repo)/"research/doom/results"/run
    report=json.loads((root/"report.json").read_text())
    events=load_events(root/"runtime/events.jsonl")
    observations={r["sequence"]:r for r in events if r.get("event")=="observation"}
    typed={r["sequence"]:r for r in events if r.get("event")=="typed_observation"}
    inv=inventory(report,events)
    if construction:
        inv=inv[:1]
    rows=[]
    for plan in inv:
        bseq=plan["baseline_sequence"]
        if bseq not in observations or bseq not in typed:
            raise AssertionError("baseline exact observation missing")
        baseline_obs=observations[bseq]
        bp=resolve_png(root,baseline_obs)
        if sha256(bp) != baseline_obs.get("image_sha256", sha256(bp)):
            raise AssertionError("baseline PNG hash mismatch")
        if rgb_sha(bp) != baseline_obs["frame_rgb_sha256"]:
            raise AssertionError("baseline RGB hash mismatch")
        baseline=reader.read(bp,baseline_obs["pointer_binding"])
        independent_base={k:v["value"] if v["status"]=="observed" else None for k,v in baseline.items()}
        if None in independent_base.values():
            raise AssertionError(f"baseline HUD unreadable {baseline}")
        if independent_base != typed_values(typed[bseq]):
            raise AssertionError(f"baseline typed cross-check mismatch {independent_base} {typed_values(typed[bseq])}")
        if independent_base != {k:v["value"] for k,v in plan["report_snapshot"].items()}:
            raise AssertionError("report snapshot cross-check mismatch")
        candidates=[r for r in observations.values() if plan["accepted_ns"] <= r["capture_ns"] <= plan["terminal_ns"]]
        candidates.sort(key=lambda r:(r["capture_ns"],r["sequence"]))
        evidence=[]; earliest=None
        for obs in candidates:
            seq=obs["sequence"]
            if seq not in typed:
                raise AssertionError(f"typed cross-check missing seq {seq}")
            png=resolve_png(root,obs)
            if rgb_sha(png) != obs["frame_rgb_sha256"]:
                raise AssertionError(f"RGB hash mismatch seq {seq}")
            got=reader.read(png,obs["pointer_binding"])
            vals={k:v["value"] if v["status"]=="observed" else None for k,v in got.items()}
            if None in vals.values():
                raise AssertionError(f"HUD unreadable seq {seq}: {got}")
            typedv=typed_values(typed[seq])
            if vals != typedv:
                raise AssertionError(f"independent/typed mismatch seq {seq}: {vals} != {typedv}")
            changed=[k for k in ("health","ammo") if vals[k] != independent_base[k]]
            e={"sequence":seq,"capture_ns":obs["capture_ns"],"png":png.name,"png_sha256":sha256(png),
               "frame_rgb_sha256":obs["frame_rgb_sha256"],"independent":vals,"typed_crosscheck":typedv,"changed":changed}
            evidence.append(e)
            if changed and earliest is None:
                earliest={"sequence":seq,"capture_ns":obs["capture_ns"],
                          "accepted_to_feedback_ms":(obs["capture_ns"]-plan["accepted_ns"])/1e6,
                          "changed":changed,"from":independent_base,"to":vals}
        score_events=[r for r in events if r.get("event")=="post_control_score"]
        if len(score_events)!=1 or report.get("score") != score_events[0]:
            raise AssertionError("post-control score mismatch")
        rows.append({**plan,"baseline_independent":independent_base,"baseline_png":bp.name,
                     "baseline_png_sha256":sha256(bp),"observations_in_program_envelope":len(candidates),
                     "earliest_state_feedback":earliest,"evidence":evidence,
                     "stronger_task_effect_feedback":None,
                     "stronger_task_effect_limit":"only one run-level post_control_score is retained; no plan-bound kill/death/exit timestamp"})
    return {"run":run,"report_sha256":sha256(root/"report.json"),
            "events_sha256":sha256(root/"runtime/events.jsonl"),"plans":rows,
            "final_score":report["score"]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("mode",choices=("construction","full"));ap.add_argument("--repo",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
    wad=locate_wad(); reader=IndependentHudReader(wad)
    runs=[analyze_run(a.repo,"map01-v39-coast-liveness-live-01",reader,True)] if a.mode=="construction" else [analyze_run(a.repo,r,reader,False) for r in RUNS]
    state_ok=all(p["earliest_state_feedback"] is not None for r in runs for p in r["plans"])
    stronger_ok=all(p["stronger_task_effect_feedback"] is not None for r in runs for p in r["plans"])
    if not state_ok: decision="SCHEMA_INSUFFICIENT_FIRST_USEFUL_FEEDBACK"
    elif not stronger_ok: decision="RETAIN_STATE_FEEDBACK_ONLY_SCHEMA_LIMIT"
    else: decision="RETAIN_FIRST_TASK_RELEVANT_FEEDBACK_SCOPED"
    result={"schema":"map01_first_useful_feedback_posthoc_v1","mode":a.mode,"wad_sha256":WAD_SHA256,
            "scan_window":"accepted primary program envelope [accepted_ns, terminal_ns] inclusive",
            "measurement":"independent PNG/WAD HUD reconstruction; retained typed values used only as integrity cross-check",
            "runs":runs,"state_feedback_all_admitted_plans":state_ok,"stronger_task_effect_all_admitted_plans":stronger_ok,
            "decision":decision,"causality_claimed":False,
            "limits":"health/ammo state changes are decision-relevant observations, not necessarily beneficial or caused by the admitted action; run-level scorer lacks plan-bound task-effect time"}
    jdump(a.out,result); print(json.dumps({"decision":decision,"plans":sum(len(r['plans']) for r in runs)}))
if __name__=="__main__":main()
