"""Single-shot public-observation transfer allocation for Issue 2918.

The candidate receives only the public observe() reply. Oracle rows are written
to a different output file for the post-run independent auditor.
"""
from __future__ import annotations
import hashlib, json, os, sys, time
from pathlib import Path
from Xlib import X, display
from Xlib.Xatom import STRING
from runtime.cli_v1.observe import observe
from research.analysis.observation_manipulate_dynamic_certificate_v1.live_candidate import decide

OUT = Path(os.environ.get("OUT", "/out")); CAP = OUT / "captures"
OUT.mkdir(parents=True, exist_ok=True); CAP.mkdir(exist_ok=True)
D = display.Display(os.environ.get("DISPLAY")); ROOT = D.screen().root
COLORS = {1: "#00b400", 0: "#dc0000", None: "#808080"}
SQUARES = [(20,20),(140,20),(260,20),(380,20)]

class Fixture:
    def __init__(self, state, duplicate=None, origin=(20,20)):
        self.origin=origin
        self.win = ROOT.create_window(origin[0],origin[1],520,160,0,D.screen().root_depth,
            X.InputOutput,X.CopyFromParent,background_pixel=D.screen().white_pixel)
        self.win.set_wm_name("issue2918-live-fixture")
        self.win.map(); D.sync(); self.draw(state, duplicate)
    @property
    def xid(self): return self.win.id
    def draw(self,state,duplicate=None):
        for (x,y),v in zip(SQUARES,state):
            c=D.screen().default_colormap.alloc_named_color(COLORS[v]).pixel
            self.win.fill_rectangle(self.win.create_gc(foreground=c),x,y,80,80)
        if duplicate is not None:
            c=D.screen().default_colormap.alloc_named_color(COLORS[duplicate]).pixel
            self.win.fill_rectangle(self.win.create_gc(foreground=c),140,100,80,40)
        D.sync()
    def replace(self,state):
        old=self.xid; origin=self.origin; self.win.destroy(); D.sync(); self.__init__(state,origin=origin)
        return old,self.xid

def capture(fx, tag, region=(0,0,520,160)):
    before=time.monotonic_ns()
    row=observe({"fixture":fx.xid},target="fixture",frame="window_client",
        region=list(region),capture_directory=str(CAP),display_name=os.environ["DISPLAY"])
    after=time.monotonic_ns()
    meta={"tag":tag,"before_ns":before,"after_ns":after,"api":row}
    CAPTURE_META[tag]=meta
    return meta

def main():
    global CAPTURE_META
    CAPTURE_META={}
    cases=[]; oracle=[]; prior=None; contexts={}; decisions={}
    # Two held-out fact transitions exercise EFFECT_PENDING and PREPARE.
    schedules=[("complete_initial","EFFECT_PENDING",(1,1,1,0),"complete-A"),
      ("complete_unmasked_change","EFFECT_PENDING",(0,0,1,0),"complete-A"),
      ("complete_masked_change","EFFECT_PENDING",(0,0,0,0),"complete-A"),
      ("abort_initial","PREPARE",(1,0,0,1),"abort-B"),
      ("abort_unmasked_change","PREPARE",(0,1,1,1),"abort-B")]
    fx=Fixture(schedules[0][2]); binding={"display":os.environ["DISPLAY"],"xid":fx.xid,"role":"fixture"}
    for i,(tag,phase,state,intent) in enumerate(schedules):
        fx.draw(state)
        if i==3: prior=None; binding={"display":os.environ["DISPLAY"],"xid":fx.xid,"role":"fixture"}
        raw=capture(fx,tag); api=raw["api"]; obs=api.get("observation",{})
        row=decide(artifact=obs.get("artifact",{}),phase=phase,binding=binding,
          intent_epoch=intent,captured_ns=obs.get("capture_ended_ns",raw["before_ns"]),now_ns=raw["after_ns"],
          observed_xid=obs.get("native_window_id"),prior=prior)
        row.update({"case":tag,"observation_id":api.get("observation_id"),"api_status":api.get("status"),
          "receipt_sha256":obs.get("sha256"),"artifact_sha256":obs.get("artifact",{}).get("sha256"),
          "native_window_id":obs.get("native_window_id"),"capture_started_ns":obs.get("capture_started_ns"),
          "capture_ended_ns":obs.get("capture_ended_ns"),"frame":obs.get("frame"),"region":obs.get("region"),
          "binding":binding,"intent_epoch":intent,"phase":phase})
        contexts[tag]={"phase":phase,"state":list(state),"intent_epoch":intent,"binding":binding,"prior":prior}
        decisions[tag]=raw["after_ns"]
        cases.append(row); oracle.append({"case":tag,"phase":phase,"state":state,"intent_epoch":intent,
          "binding":binding,"artifact_sha256":obs.get("artifact",{}).get("sha256"),"api_status":api.get("status")})
        if row.get("mask") is not None: prior={"phase":phase,"state":tuple(state),"mask":row["mask"],"binding":binding,"intent_epoch":intent}
    # Fail-open controls, each using an actual public API observation.
    controls=[("missing_fact",(1,1,None,0),"EFFECT_PENDING"),
      ("contradictory_fact",(1,1,1,0),"EFFECT_PENDING"),
      ("partial_observation",(1,1,1,0),"EFFECT_PENDING")]
    for tag,state,phase in controls:
        fx.draw(state, duplicate=(0 if tag=="contradictory_fact" else None))
        region=(0,0,400,160) if tag=="partial_observation" else (0,0,520,160)
        raw=capture(fx,tag,region); api=raw["api"]; obs=api.get("observation",{})
        row=decide(artifact=obs.get("artifact",{}),phase=phase,binding=binding,intent_epoch="control",
          captured_ns=obs.get("capture_ended_ns",raw["before_ns"]),now_ns=raw["after_ns"],
          observed_xid=obs.get("native_window_id"),partial=(tag=="partial_observation"),prior=None)
        row.update({"case":tag,"api_status":api.get("status"),"observation_id":api.get("observation_id"),
          "artifact_sha256":obs.get("artifact",{}).get("sha256"),"receipt_sha256":obs.get("sha256"),
          "native_window_id":obs.get("native_window_id"),"capture_started_ns":obs.get("capture_started_ns"),
          "capture_ended_ns":obs.get("capture_ended_ns"),"frame":obs.get("frame"),"region":obs.get("region")}); cases.append(row)
        contexts[tag]={"phase":phase,"state":list(state),"intent_epoch":"control","binding":binding,"prior":None}
        decisions[tag]=raw["after_ns"]
        oracle.append({"case":tag,"phase":phase,"state":state,"artifact_sha256":obs.get("artifact",{}).get("sha256"),"api_status":api.get("status")})
    # Stale actual capture: age one returned observation past fixed 250ms gate.
    fx.draw((1,1,1,0)); raw=capture(fx,"stale_observation"); api=raw["api"]; obs=api.get("observation",{})
    time.sleep(.275)
    stale_decision_ns=time.monotonic_ns()
    row=decide(artifact=obs.get("artifact",{}),phase="EFFECT_PENDING",binding=binding,intent_epoch="stale",
      captured_ns=obs.get("capture_ended_ns",raw["before_ns"]),now_ns=stale_decision_ns,
      observed_xid=obs.get("native_window_id"),prior=None)
    contexts["stale_observation"]={"phase":"EFFECT_PENDING","state":[1,1,1,0],"intent_epoch":"stale","binding":binding,"prior":None}
    decisions["stale_observation"]=stale_decision_ns
    row.update({"case":"stale_observation","api_status":api.get("status"),"observation_id":api.get("observation_id"),
      "artifact_sha256":obs.get("artifact",{}).get("sha256"),"receipt_sha256":obs.get("sha256"),
      "native_window_id":obs.get("native_window_id"),"capture_ended_ns":obs.get("capture_ended_ns")}); cases.append(row)
    oracle.append({"case":"stale_observation","phase":"EFFECT_PENDING","state":[1,1,1,0],"artifact_sha256":obs.get("artifact",{}).get("sha256"),"api_status":api.get("status")})
    # Replacement must invalidate old binding before any certificate reuse.
    old,new=fx.replace((1,1,1,0)); newbinding={"display":os.environ["DISPLAY"],"xid":new,"role":"fixture"}
    raw=capture(fx,"target_replacement"); api=raw["api"]; obs=api.get("observation",{})
    target_prior={"phase":"EFFECT_PENDING","state":(1,1,1,0),"mask":["E","S"],"binding":{"xid":old},"intent_epoch":"replace"}
    row=decide(artifact=obs.get("artifact",{}),phase="EFFECT_PENDING",binding=newbinding,intent_epoch="replace",
      captured_ns=obs.get("capture_ended_ns",raw["before_ns"]),now_ns=raw["after_ns"],observed_xid=obs.get("native_window_id"),
      prior=target_prior)
    contexts["target_replacement"]={"phase":"EFFECT_PENDING","state":[1,1,1,0],"intent_epoch":"replace","binding":newbinding,"prior":target_prior}
    decisions["target_replacement"]=raw["after_ns"]
    row.update({"case":"target_replacement","old_xid":old,"new_xid":new,"api_status":api.get("status"),"observation_id":api.get("observation_id"),
      "receipt_sha256":obs.get("sha256"),"capture_ended_ns":obs.get("capture_ended_ns")}); cases.append(row)
    oracle.append({"case":"target_replacement","old_xid":old,"new_xid":new,"state":[1,1,1,0],"api_status":api.get("status")})
    # Ambiguous matching-role registry yields without invoking observation API.
    second=Fixture((1,1,1,0),origin=(700,20)); matches=[fx.xid,second.xid]
    ambiguous_now=time.monotonic_ns()
    row=decide(artifact={},phase="EFFECT_PENDING",binding=newbinding,intent_epoch="ambiguous",
      captured_ns=ambiguous_now,now_ns=ambiguous_now,ambiguous=(len(matches)!=1),prior=None)
    contexts["ambiguous_target"]={"phase":"EFFECT_PENDING","state":None,"intent_epoch":"ambiguous","binding":newbinding,"prior":None}
    decisions["ambiguous_target"]=ambiguous_now
    origins=[list(fx.origin),list(second.origin)]
    row.update({"case":"ambiguous_target","matching_xids":matches,"matching_origins":origins,"api_calls":0}); cases.append(row)
    oracle.append({"case":"ambiguous_target","matching_xids":matches,"matching_origins":origins,"api_calls":0})
    # A fresh complete capture paired with a different intent epoch is invalid.
    raw=capture(fx,"intent_epoch_mismatch"); api=raw["api"]; obs=api.get("observation",{})
    intent_prior={"phase":"EFFECT_PENDING","state":(1,1,1,0),"mask":["E","S"],"binding":newbinding,"intent_epoch":"old-intent"}
    row=decide(artifact=obs.get("artifact",{}),phase="EFFECT_PENDING",binding=newbinding,intent_epoch="new-intent",
      captured_ns=obs.get("capture_ended_ns",raw["before_ns"]),now_ns=raw["after_ns"],observed_xid=obs.get("native_window_id"),
      prior=intent_prior)
    contexts["intent_epoch_mismatch"]={"phase":"EFFECT_PENDING","state":[1,1,1,0],"intent_epoch":"new-intent","binding":newbinding,"prior":intent_prior}
    decisions["intent_epoch_mismatch"]=raw["after_ns"]
    row.update({"case":"intent_epoch_mismatch","api_status":api.get("status"),"observation_id":api.get("observation_id"),
      "receipt_sha256":obs.get("sha256"),"capture_ended_ns":obs.get("capture_ended_ns")}); cases.append(row)
    oracle.append({"case":"intent_epoch_mismatch","state":[1,1,1,0],"api_status":api.get("status")})
    # Persist complete capture, target-binding, intent-epoch and decision
    # lineage for every candidate row, including early fail-open returns.
    for result in cases:
        tag=result["case"]; ctx=contexts[tag]; meta=CAPTURE_META.get(tag)
        api=meta["api"] if meta else {}; obs=api.get("observation",{})
        result.update({"phase":ctx["phase"],"intent_epoch":ctx["intent_epoch"],"binding":ctx["binding"],
          "decision_monotonic_ns":decisions[tag],"prior_binding":ctx["prior"].get("binding") if ctx["prior"] else None,
          "prior_intent_epoch":ctx["prior"].get("intent_epoch") if ctx["prior"] else None,
          "prior_mask":ctx["prior"].get("mask") if ctx["prior"] else None,
          "native_window_id":obs.get("native_window_id"),"capture_started_ns":obs.get("capture_started_ns"),
          "capture_ended_ns":obs.get("capture_ended_ns"),"frame":obs.get("frame"),"region":obs.get("region"),
          "raw_image_sha256":obs.get("sha256"),"artifact_sha256":obs.get("artifact",{}).get("sha256"),
          "artifact_path":obs.get("artifact",{}).get("path"),"api_calls":1 if meta else 0,
          "input_dispatched":api.get("input_dispatched",False),"side_effect_authority":api.get("side_effect_authority",False)})
        audit_oracle=next(item for item in oracle if item["case"]==tag)
        audit_oracle.update({key:result.get(key) for key in ("phase","intent_epoch","binding","native_window_id",
          "capture_started_ns","capture_ended_ns","frame","region","raw_image_sha256","artifact_sha256",
          "observation_id","api_calls","input_dispatched","side_effect_authority")})
        if ctx["prior"]:
            audit_oracle["prior_binding"]=ctx["prior"].get("binding")
            audit_oracle["prior_intent_epoch"]=ctx["prior"].get("intent_epoch")
    # Candidate and oracle are deliberately separate post-run outputs.
    (OUT/"candidate_results.json").write_text(json.dumps(cases,sort_keys=True,indent=2)+"\n")
    (OUT/"sealed_oracle.json").write_text(json.dumps(oracle,sort_keys=True,indent=2)+"\n")
    (OUT/"allocation.json").write_text(json.dumps({"cases":len(cases),"display":os.environ["DISPLAY"],"input_dispatched":False,"side_effect_authority":False},sort_keys=True,indent=2)+"\n")
    print(json.dumps({"cases":len(cases),"out":str(OUT)}))
    second.win.destroy(); fx.win.destroy(); D.sync(); D.close()

if __name__=="__main__": main()
