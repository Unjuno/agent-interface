#!/usr/bin/env python3
"""Independent audit of the retained 32-row evidence; no candidate import."""
import hashlib, json, sys
from pathlib import Path

EXPECTED={
 "valid": {"RESIDENT_INCREMENTAL":1,"LAST_MESSAGE":1,"MESSAGE_COUNT":1,"RESTART_REPLAY_UNGUARDED":1},
 "true_then_revoke": {"RESIDENT_INCREMENTAL":1,"LAST_MESSAGE":0,"MESSAGE_COUNT":1,"RESTART_REPLAY_UNGUARDED":1},
 "revoke_first": {"RESIDENT_INCREMENTAL":0,"LAST_MESSAGE":1,"MESSAGE_COUNT":1,"RESTART_REPLAY_UNGUARDED":1},
 "replacement_delayed_old": {"RESIDENT_INCREMENTAL":0,"LAST_MESSAGE":1,"MESSAGE_COUNT":1,"RESTART_REPLAY_UNGUARDED":1},
 "out_of_order_false": {"RESIDENT_INCREMENTAL":1,"LAST_MESSAGE":0,"MESSAGE_COUNT":1,"RESTART_REPLAY_UNGUARDED":1},
 "duplicate_true": {"RESIDENT_INCREMENTAL":1,"LAST_MESSAGE":1,"MESSAGE_COUNT":2,"RESTART_REPLAY_UNGUARDED":2},
 "restart_replay": {"RESIDENT_INCREMENTAL":1,"LAST_MESSAGE":1,"MESSAGE_COUNT":2,"RESTART_REPLAY_UNGUARDED":2},
 "effect_off": {"RESIDENT_INCREMENTAL":1,"LAST_MESSAGE":1,"MESSAGE_COUNT":1,"RESTART_REPLAY_UNGUARDED":1},
}
POLICIES={"RESIDENT_INCREMENTAL","LAST_MESSAGE","MESSAGE_COUNT","RESTART_REPLAY_UNGUARDED"}
rows=json.loads(Path(sys.argv[1]).read_text())
assert len(rows)==32, f"row count {len(rows)} != 32"
seen=set()
for r in rows:
    key=(r["case"],r["policy"]); assert key not in seen, f"duplicate {key}"; seen.add(key)
    assert r["case"] in EXPECTED and r["policy"] in POLICIES, f"unexpected key {key}"
    want=EXPECTED[r["case"]][r["policy"]]
    assert r["transport_count"]==want, f"{key}: transport {r['transport_count']} != {want}"
    assert len(r["action_event_indices"])==want, f"{key}: action ledger length mismatch"
    assert all(0<=i<len(r["events"]) and r["events"][i]["kind"]=="obs" and r["events"][i].get("value") is True for i in r["action_event_indices"]), f"{key}: action without positive observation"
    assert r["key_release_verified"] is True, f"{key}: key release not verified"
    isoff=r["case"]=="effect_off"
    assert r["effect_enabled"] is (not isoff), f"{key}: fixture mode mismatch"
    assert r["task_effect_count"]==(0 if isoff else want), f"{key}: GUI title effect mismatch"
    assert r["gui_title"]==f"resident-fixture:{0 if isoff else want}", f"{key}: title mismatch"
    assert len(r["screen_before_sha256"])==64 and len(r["screen_after_sha256"])==64
    assert r["screen_changed"]==(r["screen_before_sha256"]!=r["screen_after_sha256"]), f"{key}: screen hash mismatch"
assert seen=={(c,p) for c in EXPECTED for p in POLICIES}, "matrix incomplete"
assert all(r["task_effect_count"]==0 for r in rows if r["case"]=="effect_off"), "effect-off mislabeled"
print(json.dumps({"audit":"PASS","rows":len(rows),"policies":len(POLICIES),"cases":len(EXPECTED),"key_release_rows":sum(r["key_release_verified"] for r in rows),"positive_task_effects":sum(r["task_effect_count"]>0 for r in rows),"effect_off_rows":sum(r["case"]=="effect_off" for r in rows),"screen_changed_rows":sum(r["screen_changed"] for r in rows),"allocation_label_deviation":"rows.json internally says allocation 01; GitHub successor registration is 02; no rerun"},sort_keys=True))
