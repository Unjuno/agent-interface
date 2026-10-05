#!/usr/bin/env python3
"""Independent arithmetic audit of the saved guard replay table."""
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
freeze=json.loads((HERE/"FREEZE.json").read_text())
readout=json.loads((HERE/"input/VISUAL_READOUT.json").read_text())
raw=json.loads((HERE/"raw.json").read_text())
rows={float(x["game_clock"].rstrip("s")):x for x in readout["samples"]}
expected={3:47.0,4:54.8,5:54.8,6:56.4,12:56.4}
errors=[]
if hashlib.sha256((HERE/"input/VISUAL_READOUT.json").read_bytes()).hexdigest()!="610b77f02302150f26c7de81e46bcba5e8a4fc646d6195442c86db93c6305724":errors.append("input_sha")
if raw.get("controller_sha256")!=freeze["controller_source_sha256"]:errors.append("controller_sha")
if raw.get("guard_sha256")!=freeze["guard_source_sha256"]:errors.append("guard_sha")
if raw.get("source_readout_sample_count")!=10:errors.append("input_count")
if len(raw.get("sweep",[]))!=5:errors.append("sweep_count")
for result in raw.get("sweep",[]):
 loss=result.get("maximum_health_loss")
 floor=max(35,100-loss)
 if result.get("hard_minimum")!=floor:errors.append(f"floor_{loss}")
 first=result.get("first_invalidation")
 want=expected.get(loss)
 if want is None or type(first)is not dict or first.get("game_time_s")!=want:errors.append(f"first_time_{loss}")
 else:
  if first.get("status")!="HARD_INVALIDATED" or first.get("health",100)>=floor:errors.append(f"hard_crossing_{loss}")
# Frozen gate requires 3/4/5 before model return, while 6/12 first cross afterward.
for result in raw.get("sweep",[]):
 loss=result.get("maximum_health_loss"); first=result.get("first_invalidation") or {}
 before=first.get("game_time_s",999)<freeze["model_pending_last_sample_game_s"]
 if before != (loss in (3,4,5)):errors.append(f"pending_boundary_{loss}")
if raw.get("source_video_sha256")!="201ab6aaa8ab5823285b44864ad1df899ebe5a19c97ec6e84b8cc5db063f6be4":errors.append("video_identity")
out={"status":"PASS_SCOPED_GUARD_REPLAY_AUDIT" if not errors else "FAIL_GUARD_REPLAY_AUDIT","errors":errors,
     "sweep_rows":len(raw.get("sweep",[])),"result":"3/4/5 invalidate before the last pending sample; 6/12 first invalidate at the first local-plan sample",
     "scope":"independent arithmetic reconstruction; not a V39 session or live gameplay result",
     "raw_sha256":hashlib.sha256((HERE/"raw.json").read_bytes()).hexdigest()}
(HERE/"AUDIT.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out,indent=2))
if errors:raise SystemExit(1)
