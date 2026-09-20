"""Independent, read-only auditor; intentionally does not import candidate/model."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
from PIL import Image

ROOT=Path(sys.argv[1] if len(sys.argv)>1 else "/out")
rows=json.loads((ROOT/"candidate_results.json").read_text())
oracle=json.loads((ROOT/"sealed_oracle.json").read_text())
allocation=json.loads((ROOT/"allocation.json").read_text())
expected=["complete_initial","complete_unmasked_change","complete_masked_change","abort_initial",
"abort_unmasked_change","missing_fact","contradictory_fact","partial_observation",
"stale_observation","target_replacement","ambiguous_target","intent_epoch_mismatch"]
assert allocation["cases"]==12 and [r["case"] for r in rows]==expected
bycase={r["case"]:r for r in rows}; truth={r["case"]:r for r in oracle}
assert len(truth)==12
doms=("T","D","E","S"); rgb={"T":(60,60),"D":(180,60),"E":(300,60),"S":(420,60)}
palette={(0,180,0):1,(220,0,0):0,(128,128,128):None}

def decide(p,s):
 t,d,e,z=s
 if p=="PREPARE": return "ABORT" if z else ("READY" if t and d else "WAIT")
 if p=="EFFECT_PENDING": return "ABORT" if z else ("COMPLETE" if e else ("CONTINUE" if t and d else "WAIT"))
 if p=="TERMINAL": return "ABORT" if z else ("COMPLETE" if e else "TERMINAL_UNRESOLVED")
 raise AssertionError("unknown phase")

def minmask(p,s):
 from itertools import combinations
 for n in range(5):
  for m in combinations(doms,n):
   safe=True
   for bits in range(16):
    other=tuple((bits>>i)&1 for i in range(4))
    if all(s[doms.index(x)]==other[doms.index(x)] for x in m) and decide(p,other)!=decide(p,s): safe=False; break
   if safe:return list(m)
 raise AssertionError("no certificate")

# Re-open each retained PNG using its hash-addressed oracle link; verify facts
# from pixels independently from the candidate's decoder and output.
hash_to_file={hashlib.sha256(p.read_bytes()).hexdigest():p for p in (ROOT/"captures").glob("*.png")}
for tag in expected:
 o=truth[tag]; h=o.get("artifact_sha256")
 if h and h in hash_to_file and o.get("state") is not None:
  im=Image.open(hash_to_file[h]).convert("RGB")
  if im.size==(520,160):
   sampled=tuple(palette.get(im.getpixel(rgb[d]),"UNRECOGNIZED") for d in doms)
   assert list(sampled)==o["state"],(tag,sampled,o["state"])
   if tag=="contradictory_fact":
    assert palette.get(im.getpixel((180,120)),"UNRECOGNIZED") != sampled[1]

unsafe=[]; gains=[]; state_by={r["case"]:tuple(truth[r["case"]]["state"]) for r in rows if truth[r["case"]].get("state") is not None}
for first,second,phase in (("complete_initial","complete_unmasked_change","EFFECT_PENDING"),("abort_initial","abort_unmasked_change","PREPARE")):
 a,b=bycase[first],bycase[second]; sa,sb=state_by[first],state_by[second]
 mask=minmask(phase,sa); changed=[d for i,d in enumerate(doms) if sa[i]!=sb[i]]
 assert a["mask"]==mask,(first,a["mask"],mask)
 assert b["reused_mask"]==mask,(second,b.get("reused_mask"),mask)
 assert b["disposition"]=="SUPPRESS" and all(d not in mask for d in changed),(second,b,changed,mask)
 assert decide(phase,sa)==decide(phase,sb),(first,second)
 # Both the phase-union and global-support controls forward for any changed
 # supported fact; neither gets the current-state certificate optimization.
 phase_support=set(doms if phase=="EFFECT_PENDING" else ("T","D","S"))
 assert set(changed)&phase_support and set(changed)&set(doms)
 gains.append({"transition":first+"->"+second,"certificate_mask":mask,"changed":changed,
               "phase_union":"FORWARD","global_support":"FORWARD","candidate":"SUPPRESS"})
sa=state_by["complete_unmasked_change"]; sb=state_by["complete_masked_change"]
assert bycase["complete_masked_change"]["disposition"]=="FORWARD"
assert decide("EFFECT_PENDING",sa)!=decide("EFFECT_PENDING",sb)
for tag in expected[5:]:
 if bycase[tag]["disposition"]!="YIELD": unsafe.append(tag)
assert not unsafe,unsafe
for tag in ("complete_initial","abort_initial","complete_unmasked_change","complete_masked_change","abort_unmasked_change"):
 r=bycase[tag]; assert r.get("api_status")=="returned" and r.get("observation_id")
assert bycase["stale_observation"]["api_status"]=="returned"
assert bycase["target_replacement"]["new_xid"]!=bycase["target_replacement"]["old_xid"]
assert bycase["ambiguous_target"]["api_calls"]==0 and len(bycase["ambiguous_target"]["matching_xids"])==2
assert allocation["input_dispatched"] is False and allocation["side_effect_authority"] is False
result={"status":"PASS_LIVE_MANIPULATE_CERTIFICATE_SCOPED","cases":12,"unsafe_suppressions":0,
 "independent_terminal_rows":len(state_by),"strict_narrowing_transitions":gains,
 "scope":"private Xvfb color-cell fixture; public X11 observe API; no GUI action; no real application/effect claim"}
(ROOT/"independent_audit.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
print(json.dumps(result,sort_keys=True))
