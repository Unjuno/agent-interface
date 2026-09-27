#!/usr/bin/env python3
"""Independent audit of allocation-03 raw ledger and exact image artifacts."""
import hashlib,json,sys
from pathlib import Path
EXPECTED={
"valid":{"RESIDENT_INCREMENTAL":1,"LAST_MESSAGE":1,"MESSAGE_COUNT":1,"RESTART_REPLAY_UNGUARDED":1},
"true_then_revoke":{"RESIDENT_INCREMENTAL":1,"LAST_MESSAGE":0,"MESSAGE_COUNT":1,"RESTART_REPLAY_UNGUARDED":1},
"revoke_first":{"RESIDENT_INCREMENTAL":0,"LAST_MESSAGE":1,"MESSAGE_COUNT":1,"RESTART_REPLAY_UNGUARDED":1},
"replacement_delayed_old":{"RESIDENT_INCREMENTAL":0,"LAST_MESSAGE":1,"MESSAGE_COUNT":1,"RESTART_REPLAY_UNGUARDED":1},
"out_of_order_false":{"RESIDENT_INCREMENTAL":1,"LAST_MESSAGE":0,"MESSAGE_COUNT":1,"RESTART_REPLAY_UNGUARDED":1},
"duplicate_true":{"RESIDENT_INCREMENTAL":1,"LAST_MESSAGE":1,"MESSAGE_COUNT":2,"RESTART_REPLAY_UNGUARDED":2},
"restart_replay":{"RESIDENT_INCREMENTAL":1,"LAST_MESSAGE":1,"MESSAGE_COUNT":2,"RESTART_REPLAY_UNGUARDED":2},
"effect_off":{"RESIDENT_INCREMENTAL":1,"LAST_MESSAGE":1,"MESSAGE_COUNT":1,"RESTART_REPLAY_UNGUARDED":1}}
policies=set(next(iter(EXPECTED.values())))
bundle=json.loads(Path(sys.argv[1]).read_text());assert bundle["allocation"]=="issue3518-resident-gtk-incremental-03"
rows=bundle["rows"];assert len(rows)==32
seen=set();base=Path(sys.argv[2])
for r in rows:
 key=(r["case"],r["policy"]);assert key not in seen;seen.add(key)
 n=EXPECTED[r["case"]][r["policy"]];assert r["transport_count"]==n and len(r["action_event_indices"])==n
 assert all(0<=i<len(r["events"]) and r["events"][i]["kind"]=="obs" and r["events"][i].get("value") is True for i in r["action_event_indices"])
 assert r["gui_title"]==f"resident-fixture:{0 if r['case']=='effect_off' else n}"
 assert r["task_effect_count"]==(0 if r["case"]=="effect_off" else n)
 assert r["key_release_verified"] is True
 assert r["fixture_reaped"] and r["xvfb_reaped"] and r["fixture_exit_code"]==-15 and r["xvfb_exit_code"]==0
 assert r["fixture_pid"]!=r["xvfb_pid"] and r["fixture_start_ticks"] and r["xvfb_start_ticks"]
 assert r["width"]>0 and r["height"]>0 and r["bytes_per_frame"]==r["width"]*r["height"]*4
 assert len(r["frame_paths"])==2
 for suffix,sha in zip(("before","after"),(r["before_sha256"],r["after_sha256"])):
  p=base/(r["frame_paths"][0] if suffix=="before" else r["frame_paths"][1]);data=p.read_bytes()
  assert len(data)==r["bytes_per_frame"] and hashlib.sha256(data).hexdigest()==sha
 assert r["window_pixels_changed"]==(r["before_sha256"]!=r["after_sha256"])
assert seen=={(c,p) for c in EXPECTED for p in policies}
print(json.dumps({"audit":"PASS","allocation":bundle["allocation"],"rows":len(rows),"images":64,"key_release_rows":32,"cleanup_rows":32,"effect_off_rows":4},sort_keys=True))
