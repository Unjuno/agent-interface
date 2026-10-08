#!/usr/bin/env python3
"""Independent raw-only auditor for Issue #5692 T0; does not import candidate."""
from __future__ import annotations
import argparse, base64, hashlib, json
from pathlib import Path
from typing import Any

EXPECTED = {
 ("clear","SCREENSHOT_GEOMETRY"):(True,True,"target"), ("clear","RECIPIENT_PRECHECK"):(True,True,"target"),
 ("visible","SCREENSHOT_GEOMETRY"):(False,False,None), ("visible","RECIPIENT_PRECHECK"):(False,False,None),
 ("transparent-input","SCREENSHOT_GEOMETRY"):(True,False,"overlay"), ("transparent-input","RECIPIENT_PRECHECK"):(False,False,None),
 ("input-transparent","SCREENSHOT_GEOMETRY"):(True,True,"target"), ("input-transparent","RECIPIENT_PRECHECK"):(True,True,"target"),
 ("visible","DIAGNOSTIC_FORCE_CLICK"):(True,False,"overlay"), ("race-after-check","RECIPIENT_PRECHECK"):(True,True,"overlay"),
}

def audit(doc:dict[str,Any])->dict[str,Any]:
 errors=[]
 def ck(ok,msg):
  if not ok: errors.append(msg)
 ck(doc.get("schema")=="ui-redress-5692-t0-raw-v1","schema")
 rows=doc.get("rows"); ck(isinstance(rows,list) and len(rows)==10,"exact ten-row matrix")
 if not isinstance(rows,list): rows=[]
 seen=set(); got={}
 for i,row in enumerate(rows):
  if not isinstance(row,dict): ck(False,f"row {i} invalid"); continue
  key=(row.get("condition"),row.get("policy"))
  if key not in EXPECTED or key in seen: ck(False,f"unexpected/duplicate {key}"); continue
  seen.add(key); got[key]=row; admit,target_pre,recipient=EXPECTED[key]
  ck(row.get("admitted") is admit,f"{key} admission"); ck(row.get("click_delivered") is admit,f"{key} delivery")
  ck(row.get("recipient_is_target_at_precheck") is target_pre,f"{key} precheck")
  target,overlay=row.get("target"),row.get("overlay")
  ck(isinstance(target,dict) and type(target.get("pid")) is int,f"{key} target identity")
  target_id=target.get("window_id") if isinstance(target,dict) else None
  overlay_id=overlay.get("window_id") if isinstance(overlay,dict) else None
  if key[0] in ("visible","transparent-input","input-transparent","race-after-check"):
   ck(type(overlay_id) is int,f"{key} overlay identity")
  mode={"visible":("visible",True),"transparent-input":("input",True),"input-transparent":("empty-input",False)}.get(key[0])
  if mode: ck(isinstance(overlay,dict) and overlay.get("mode")==mode[0] and overlay.get("input_shape") is mode[1],f"{key} mode/shape")
  if key[0]=="race-after-check": ck(isinstance(overlay,dict) and overlay.get("mode")=="input" and overlay.get("mapped") is True,"race overlay mapped")
  b,a=row.get("before_crop"),row.get("after_crop")
  for label,crop in (("before",b),("after",a)):
   if not isinstance(crop,dict): ck(False,f"{key} {label} crop missing"); continue
   try:
    pix=base64.b64decode(crop.get("base64",""),validate=True)
    ck(hashlib.sha256(pix).hexdigest()==crop.get("sha256"),f"{key} {label} digest")
    ck(crop.get("format")=="X11_ZPixmap_raw" and len(pix)>0,f"{key} {label} pixels")
   except Exception: ck(False,f"{key} {label} base64")
  if isinstance(b,dict) and isinstance(a,dict):
   same=b.get("sha256")==a.get("sha256"); ck(row.get("visual_same") is same,f"{key} visual consistency")
   ck(same is (key[0]!="visible"),f"{key} visual control")
  te,oe=row.get("target_events"),row.get("overlay_events")
  ck(isinstance(te,list) and isinstance(oe,list),f"{key} event logs")
  if not isinstance(te,list): te=[]
  if not isinstance(oe,list): oe=[]
  def ev(seq,typ): return [x for x in seq if isinstance(x,dict) and x.get("type")==typ]
  tp,tr=ev(te,"ButtonPress"),ev(te,"ButtonRelease"); op,orr=ev(oe,"ButtonPress"),ev(oe,"ButtonRelease")
  if recipient=="target": ck(len(tp)==len(tr)==1 and not op and not orr,f"{key} target exclusive")
  elif recipient=="overlay":
   ck(len(op)==len(orr)==1 and not tp and not tr,f"{key} overlay exclusive")
   ck(overlay_id!=target_id and type(row.get("precheck_child_id")) is int,f"{key} foreign identity")
  else: ck(not tp and not tr and not op and not orr,f"{key} refusal delivered input")
  if key[0]=="race-after-check": ck(row.get("visual_same") is True and row.get("admitted") is True,"race check order")
 ck(seen==set(EXPECTED),"matrix coverage")
 ti=got.get(("transparent-input","SCREENSHOT_GEOMETRY")); tp=got.get(("transparent-input","RECIPIENT_PRECHECK"))
 it=got.get(("input-transparent","RECIPIENT_PRECHECK")); race=got.get(("race-after-check","RECIPIENT_PRECHECK"))
 res={"transparent_pixels_equal":bool(ti and tp and ti.get("visual_same") and tp.get("visual_same")),
      "static_transparent_precheck_refused":bool(tp and tp.get("admitted") is False),
      "input_transparent_reached_target":bool(it and it.get("target_events")),
      "visible_overlay_intercepted":bool(got.get(("visible","DIAGNOSTIC_FORCE_CLICK"),{}).get("overlay_events")),
      "postcheck_race_redirected":bool(race and race.get("overlay_events") and not race.get("target_events")),"errors":errors}
 res["disposition"]="METHOD_PASS_SCOPED" if not errors else "STOP_OR_FAIL_AUDIT"
 return res

def main():
 p=argparse.ArgumentParser(); p.add_argument("raw"); p.add_argument("--out"); a=p.parse_args()
 raw=Path(a.raw).read_bytes(); res=audit(json.loads(raw)); res["raw_sha256"]=hashlib.sha256(raw).hexdigest()
 text=json.dumps(res,sort_keys=True)+"\n"
 if a.out: Path(a.out).write_text(text,encoding="utf-8")
 print(text,end=""); return 0 if res["disposition"]=="METHOD_PASS_SCOPED" else 1

if __name__=="__main__": raise SystemExit(main())
