import json, copy

SCHEMA="agent-interface/motor-state-v1"

def adapt(raw):
    if not isinstance(raw,dict): raise ValueError("record")
    target=raw.get("target",{})
    release=raw.get("release",{})
    ex=raw.get("execution",{})
    obs=raw.get("observation")
    uncertainty="NONE"
    if not raw.get("focus_confirmed",False): uncertainty="FOCUS_UNKNOWN"
    if obs is None: uncertainty="OS_UNCONFIRMED"
    rel_status="VERIFIED_EMPTY" if release.get("final_release_verified") is True else ("FAILED" if release.get("error") else "UNVERIFIED")
    event={"type":"RELEASE_TRANSITION","status":rel_status}
    return {"schema":SCHEMA,"state_id":raw.get("result_id","r1"),"owner_id":raw.get("owner_id","owner-unknown"),
      "owner_revision":int(raw.get("binding_revision",0)),"observation_id":obs.get("observation_id","obs-unknown") if obs else "obs-unknown",
      "surface_id":target.get("surface_id",target.get("window_id","surface-unknown")),
      "coordinate_frame":target.get("frame","window_client"),"commanded_pointer":raw.get("commanded_pointer",{}),
      "observed_pointer":obs.get("observed_pointer") if obs else None,"held_keys":raw.get("held_keys",[]),
      "held_buttons":raw.get("held_buttons",[]),"input_ack":{"id":raw.get("ack_id","ack-unknown"),"status":"ACKED" if ex.get("transport_passed") else "UNKNOWN"},
      "release":{"status":rel_status,"retained":True},"uncertainty":uncertainty,"events":[event]}

def valid(m):
    required=("schema","owner_id","observation_id","surface_id","coordinate_frame","input_ack","release","uncertainty","events")
    return all(k in m for k in required) and m["schema"]==SCHEMA and m["uncertainty"] in {"NONE","OS_UNCONFIRMED","FOCUS_UNKNOWN","SURFACE_UNKNOWN"} and any(e.get("type")=="RELEASE_TRANSITION" for e in m["events"])

cases=[
("confirmed_observation",{"result_id":"r1","owner_id":"o1","binding_revision":3,"target":{"surface_id":"x11:10","frame":"window_client"},"focus_confirmed":True,"observation":{"observation_id":"obs1","observed_pointer":{"x":1,"y":2}},"execution":{"transport_passed":True},"release":{"final_release_verified":True},"ack_id":"a1"},True),
("missing_observation_is_uncertain",{"result_id":"r2","owner_id":"o1","target":{"window_id":"w2","frame":"window_client"},"focus_confirmed":True,"execution":{"transport_passed":True},"release":{"final_release_verified":True}},True),
("focus_unknown_is_not_confirmed",{"result_id":"r3","owner_id":"o1","target":{"surface_id":"s3"},"focus_confirmed":False,"observation":{"observation_id":"obs3"},"execution":{"transport_passed":True},"release":{"final_release_verified":True}},True),
("failed_release_retained",{"result_id":"r4","owner_id":"o1","target":{"surface_id":"s4"},"focus_confirmed":False,"execution":{"transport_passed":False},"release":{"error":"cleanup_failed"}},True),
]
rows=[]
for name,raw,want in cases:
    m=adapt(raw); got=valid(m); rows.append({"case":name,"accepted":got,"expected":want,"uncertainty":m["uncertainty"],"release":m["release"],"pass":got==want})
print(json.dumps({"schema":SCHEMA,"cases":rows,"decision":"PASS_NATIVE_MOTOR_STATE_MAPPING_SCOPED" if all(r["pass"] for r in rows) else "FAIL_NATIVE_MOTOR_STATE_MAPPING","scope":"synthetic mapping only; no live backend or authority claim"},indent=2))
raise SystemExit(0 if all(r["pass"] for r in rows) else 1)
