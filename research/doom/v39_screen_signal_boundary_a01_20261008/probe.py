import hashlib, json, sys
from pathlib import Path
sys.path[:0] = [r"C:\Users\user\Documents\Codex\2026-10-08\work\issue59-main-576d\research\doom", r"C:\Users\user\Documents\Codex\2026-10-08\work\issue59-main-576d\research\live_control"]
from map01_overlap_controller_v39 import DoomCoverSignalPairMonitor
from observable_signal_guard_v2 import ObservableSignalGuard

binding = {"surface_id": "synthetic-map01"}
def monitor():
    guards = {}
    for name, value, floor in (("health", 100, 80), ("ammo", 50, 1)):
        source = {"status":"observed","signal_id":name,"value":value,"sequence":1,"capture_ns":1_000_000,"binding":binding}
        spec = {"op":"observable_signal_guard","guard_id":name,"source_sequence":1,"signal_id":name,"source_value":value,"hard_minimum":floor,"max_source_age_ms":30000,"on_soft_change":"preserve_existing_policy","on_hard_change":"needs_decision","on_unknown":"needs_decision"}
        guards[name] = ObservableSignalGuard(spec, source, binding)
    return DoomCoverSignalPairMonitor(guards, None, None)

def row(frame, health):
    seq, captured = 2, 2_000_000
    signals = {name:{"status":"observed","signal_id":name,"value":value,"sequence":seq,"capture_ns":captured,"binding":binding} for name,value in (("health",health),("ammo",50))}
    return {"event":"typed_observation","sequence":seq,"capture_ns":captured,"pointer_binding":binding,"signals":signals,"frame_rgb_sha256":hashlib.sha256(frame).hexdigest()}

black = bytes([0,0,0])*16
red = bytes([255,0,0])*16
screen_case = {"frame_hash_changed":hashlib.sha256(black).hexdigest()!=hashlib.sha256(red).hexdigest(),"health_source":100,"health_current":100,"ammo_source":50,"ammo_current":50,"result":monitor().observe(row(red,100))}
hud_case = {"frame_hash_changed":True,"health_source":100,"health_current":79,"ammo_source":50,"ammo_current":50,"result":monitor().observe(row(red,79))}
result = {"experiment":"issue59-screen-signal-boundary-a01-20261008","status":"CONSTRUCTION_OBSERVATION","screen_only_change":screen_case,"typed_hard_crossing":hud_case,"scope":"Synthetic current-main controller behavior only; not live threat efficacy."}
print(json.dumps(result,sort_keys=True,indent=2))