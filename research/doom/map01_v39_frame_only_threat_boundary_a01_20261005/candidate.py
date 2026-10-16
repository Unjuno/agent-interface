"""One-shot source-bound V39 frame-only observation boundary candidate."""
from __future__ import annotations
import hashlib, json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DOOM = ROOT / "research" / "doom"
LIVE = ROOT / "research" / "live_control"
sys.path[:0] = [str(DOOM), str(LIVE)]
import map01_overlap_controller_v39 as controller


def signal(name, value, sequence, capture_ns, binding):
    return {"format":"observable-signal-v1","status":"observed","signal_id":name,
            "value":value,"sequence":sequence,"capture_ns":capture_ns,"binding":binding}

class Reader:
    def __init__(self, signal_id, rows): self.signal_id, self.rows = signal_id, rows
    def read(self, observation): return self.rows[observation["sequence"]]

def main():
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    inp = json.loads((HERE / "input.json").read_text(encoding="utf-8"))
    source_path = ROOT / freeze["source_path"]
    source_bytes = source_path.read_bytes()
    commit = subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    blob = subprocess.check_output(["git","hash-object",str(source_path)],cwd=ROOT,text=True).strip()
    if commit != freeze["source_commit"] or hashlib.sha256(source_bytes).hexdigest() != freeze["source_sha256"] or blob != freeze["source_git_blob"]:
        raise RuntimeError("frozen current-main source identity mismatch")
    if hashlib.sha256((HERE / "input.json").read_bytes()).hexdigest() != freeze["input_sha256"]:
        raise RuntimeError("frozen stimulus identity mismatch")
    binding = inp["binding"]
    base = {"event":"observation","sequence":inp["source_sequence"],
            "capture_ns":inp["source_capture_ns"],"pointer_binding":binding,
            "frame_rgb_sha256":hashlib.sha256(inp["source_frame_payload"].encode()).hexdigest()}
    health = {inp["source_sequence"]:signal("health",inp["health"],inp["source_sequence"],inp["source_capture_ns"],binding),
              inp["next_sequence"]:signal("health",inp["health"],inp["next_sequence"],inp["next_capture_ns"],binding)}
    ammo = {inp["source_sequence"]:signal("ammo",inp["ammo"],inp["source_sequence"],inp["source_capture_ns"],binding),
            inp["next_sequence"]:signal("ammo",inp["ammo"],inp["next_sequence"],inp["next_capture_ns"],binding)}
    monitor, receipt = controller.build_cover_monitor(
        Reader("health",health),base,
        {"signal_id":"health","critical_health_minimum":51,
         "maximum_health_loss":10,"max_source_age_ms":30000},
        0,ammo_reader=Reader("ammo",ammo),requires_ammo=True)
    next_frame = hashlib.sha256(inp["next_frame_payload"].encode()).hexdigest()
    event = {"event":"typed_observation","sequence":inp["next_sequence"],
             "capture_ns":inp["next_capture_ns"],"pointer_binding":binding,
             "frame_rgb_sha256":next_frame,"signals":{"health":health[inp["next_sequence"]],
                                                       "ammo":ammo[inp["next_sequence"]]}}
    result = monitor.observe(event)
    raw = {"schema":"v39-frame-only-threat-boundary-raw-v1","source_commit":commit,
           "source_sha256":freeze["source_sha256"],"source_git_blob":blob,
           "input_sha256":freeze["input_sha256"],"source_observation":base,
           "next_observation":event,"admission_receipt":receipt,
           "monitor_result":result,"post_state":{"last_sequence":monitor.last_sequence,
           "last_values":monitor.last_values,"soft_event_count":monitor.soft_event_count,
           "latest_soft_event":monitor.latest_soft_event,
           "last_frame_rgb_sha256":monitor.last_frame_rgb_sha256}}
    return raw

if __name__ == "__main__":
    out = HERE / "results" / "a01" / "candidate.json"
    if out.exists(): raise SystemExit("candidate output already exists; preserve first outcome")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(main(),indent=2,sort_keys=True)+"\n",encoding="utf-8")
