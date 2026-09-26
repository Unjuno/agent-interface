"""Independent auditor for allocation 03; reads evidence, writes elsewhere."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
from PIL import Image

IN=Path(sys.argv[1]); REPORT=Path(sys.argv[2]); REPORT.mkdir(parents=True,exist_ok=True)
rows=json.loads((IN/"candidate_results.json").read_text())
oracle=json.loads((IN/"sealed_oracle.json").read_text())
allocation=json.loads((IN/"allocation.json").read_text())
names=["complete_initial","complete_unmasked_change","complete_masked_change","abort_initial",
 "abort_unmasked_change","missing_fact","contradictory_fact","partial_observation",
 "stale_observation","target_replacement","ambiguous_target","intent_epoch_mismatch"]
assert allocation["cases"]==12 and allocation["input_dispatched"] is False and allocation["side_effect_authority"] is False
assert [x["case"] for x in rows]==names and [x["case"] for x in oracle]==names
R={x["case"]:x for x in rows}; O={x["case"]:x for x in oracle}; doms=("T","D","E","S")
points={"T":(60,60),"D":(180,60),"E":(300,60),"S":(420,60)}
palette={(0,180,0):1,(220,0,0):0,(128,128,128):None}

def terminal(p,s):
 t,d,e,z=s
 if p=="PREPARE":return "ABORT" if z else ("READY" if t and d else "WAIT")
 if p=="EFFECT_PENDING":return "ABORT" if z else ("COMPLETE" if e else ("CONTINUE" if t and d else "WAIT"))
 if p=="TERMINAL":return "ABORT" if z else ("COMPLETE" if e else "TERMINAL_UNRESOLVED")
 raise AssertionError(p)

def minimum(p,s):
 from itertools import combinations
 for n in range(5):
  for m in combinations(doms,n):
   okay=True
   for value in range(16):
    other=tuple((value>>i)&1 for i in range(4))
    if all(s[doms.index(k)]==other[doms.index(k)] for k in m) and terminal(p,other)!=terminal(p,s):
     okay=False; break
   if okay:return list(m)
 raise AssertionError("no certificate")

png_files=list((IN/"captures").glob("*.png")); pngs={}
for p in png_files: pngs.setdefault(hashlib.sha256(p.read_bytes()).hexdigest(),[]).append(p)
assert len(png_files)==11
assert len({R["complete_initial"]["observation_id"],R["complete_unmasked_change"]["observation_id"],
 R["complete_masked_change"]["observation_id"],R["abort_initial"]["observation_id"],R["abort_unmasked_change"]["observation_id"],
 R["missing_fact"]["observation_id"],R["contradictory_fact"]["observation_id"],R["partial_observation"]["observation_id"],
 R["stale_observation"]["observation_id"],R["target_replacement"]["observation_id"],R["intent_epoch_mismatch"]["observation_id"]})==11
valid_pixels=[]
for name in names:
 row=R[name]; exp=O[name]
 assert row.get("phase")==exp.get("phase") and row.get("intent_epoch")==exp.get("intent_epoch")
 assert row.get("binding")==exp.get("binding") and row.get("api_calls")==exp.get("api_calls")
 if name=="ambiguous_target":
  assert row["disposition"]=="YIELD" and row["api_calls"]==0 and len(row["matching_xids"])==2
  assert row["matching_xids"]==exp["matching_xids"] and row["matching_origins"]==[[20,20],[700,20]]
  assert row["matching_xids"]==exp["matching_xids"] and row.get("observation_id") is None
  assert row["matching_origins"]==exp["matching_origins"] and abs(row["matching_origins"][0][0]-row["matching_origins"][1][0])>=520
  continue
 assert row["api_status"]=="returned" and row["observation_id"] and row["receipt_sha256"]
 assert row["input_dispatched"] is False and row["side_effect_authority"] is False
 assert row["native_window_id"]==row["binding"]["xid"]==exp["native_window_id"]
 assert row["artifact_sha256"]==exp["artifact_sha256"] and row["raw_image_sha256"]==exp["raw_image_sha256"]
 candidates=pngs[row["artifact_sha256"]]
 assert any(row["artifact_path"].endswith(file.name) for file in candidates) and row["region"]==exp["region"]
 assert row["capture_ended_ns"]==exp["capture_ended_ns"] and row["decision_monotonic_ns"]>=row["capture_ended_ns"]
 file=next(file for file in candidates if row["artifact_path"].endswith(file.name))
 im=Image.open(file).convert("RGB")
 assert im.size==(row["region"][2],row["region"][3])
 truth=exp["state"]
 if name=="missing_fact":
  assert im.getpixel(points["E"])==(128,128,128) and row["disposition"]=="YIELD"
 elif name=="contradictory_fact":
  assert palette.get(im.getpixel(points["D"]))==truth[1]
  assert palette.get(im.getpixel((180,120)))!=truth[1] and row["disposition"]=="YIELD"
 elif name=="partial_observation":
  assert row["region"][2]<points["S"][0]+1 and row["disposition"]=="YIELD"
 else:
  sampled=tuple(palette.get(im.getpixel(points[k]),"UNRECOGNIZED") for k in doms)
  assert list(sampled)==truth,(name,sampled,truth)
  assert terminal(row["phase"],sampled)==terminal(exp["phase"],tuple(exp["state"]))
  if name in names[5:]: assert row["disposition"]=="YIELD"
  else:
   assert row["disposition"] in ("FORWARD","SUPPRESS")
   assert row.get("certificate_generation_ns") is not None
   assert row["capture_ended_ns"]<=row["certificate_generation_ns"]<=row["decision_monotonic_ns"]
   valid_pixels.append(name)

for a,b,phase in (("complete_initial","complete_unmasked_change","EFFECT_PENDING"),
                  ("abort_initial","abort_unmasked_change","PREPARE")):
 first=O[a]; second=O[b]; mask=minimum(phase,tuple(first["state"]))
 changed=[d for i,d in enumerate(doms) if first["state"][i]!=second["state"][i]]
 assert R[a]["mask"]==mask and R[b]["prior_mask"]==mask and R[b]["reused_mask"]==mask
 assert R[b]["disposition"]=="SUPPRESS" and set(changed).isdisjoint(mask)
 assert terminal(phase,tuple(first["state"]))==terminal(phase,tuple(second["state"]))
 support=set(doms if phase=="EFFECT_PENDING" else ("T","D","S"))
 assert set(changed)&support and set(changed)&set(doms)
assert R["complete_masked_change"]["disposition"]=="FORWARD"
assert "E" in R["complete_masked_change"]["reused_mask"]
assert terminal("EFFECT_PENDING",tuple(O["complete_unmasked_change"]["state"]))!=terminal("EFFECT_PENDING",tuple(O["complete_masked_change"]["state"]))
for name in names[5:]: assert R[name]["disposition"]=="YIELD"
assert R["stale_observation"]["decision_monotonic_ns"]-R["stale_observation"]["capture_ended_ns"]>250_000_000
assert R["target_replacement"]["new_xid"]!=R["target_replacement"]["old_xid"]
assert R["target_replacement"]["binding"]["xid"]==R["target_replacement"]["new_xid"]
assert R["target_replacement"]["prior_binding"]["xid"]==R["target_replacement"]["old_xid"]
assert R["intent_epoch_mismatch"]["intent_epoch"]!=R["intent_epoch_mismatch"]["prior_intent_epoch"]
assert R["intent_epoch_mismatch"]["binding"]==R["intent_epoch_mismatch"]["prior_binding"]
report={"status":"PASS_LIVE_MANIPULATE_CERTIFICATE_SCOPED","allocation":"05","cases":12,
 "public_api_returns":11,"api_calls_on_ambiguous":0,"png_artifacts":11,"unsafe_suppressions":0,
 "independently_pixel_and_terminal_scored":valid_pixels,
 "strict_narrowing":[{"transition":"complete_initial->complete_unmasked_change","mask":R["complete_initial"]["mask"],"changed":["D","T"],"phase_union":"FORWARD","global_support":"FORWARD"},
 {"transition":"abort_initial->abort_unmasked_change","mask":R["abort_initial"]["mask"],"changed":["D","E","T"],"phase_union":"FORWARD","global_support":"FORWARD"}],
 "scope":"private Xvfb color-cell fixture; public X11 observe API; no GUI action or real-app/effect claim"}
(REPORT/"independent_audit.json").write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
print(json.dumps(report,sort_keys=True))
