import copy, json, sys

SCHEMA="agent-interface/motor-state-v1"
ALLOWED_UNCERTAINTY={"NONE","OS_UNCONFIRMED","SURFACE_UNKNOWN","FOCUS_UNKNOWN"}
ALLOWED_RELEASE={"NOT_TERMINAL","VERIFIED_EMPTY","UNVERIFIED","FAILED"}

def validate(row):
    if not isinstance(row,dict) or row.get("schema")!=SCHEMA: return False,"schema"
    for k in ("state_id","owner_id","observation_id","surface_id","coordinate_frame"):
        if not isinstance(row.get(k),str) or not row[k]: return False,k
    if type(row.get("owner_revision")) is not int or row["owner_revision"]<0: return False,"owner_revision"
    if set(row)-{"schema","state_id","owner_id","owner_revision","observation_id","surface_id","coordinate_frame","commanded_pointer","observed_pointer","held_keys","held_buttons","input_ack","release","uncertainty","events"}:
        return False,"unknown_or_authority_field"
    if not isinstance(row.get("commanded_pointer"),dict): return False,"commanded_pointer"
    obs=row.get("observed_pointer")
    if obs is not None and not isinstance(obs,dict): return False,"observed_pointer"
    if not isinstance(row.get("held_keys"),list) or not isinstance(row.get("held_buttons"),list): return False,"held"
    ack=row.get("input_ack")
    if not isinstance(ack,dict) or not isinstance(ack.get("id"),str) or ack.get("status") not in {"ACKED","PENDING","UNKNOWN"}: return False,"input_ack"
    rel=row.get("release")
    if not isinstance(rel,dict) or rel.get("status") not in ALLOWED_RELEASE or type(rel.get("retained")) is not bool: return False,"release"
    if row.get("uncertainty") not in ALLOWED_UNCERTAINTY: return False,"uncertainty"
    events=row.get("events")
    if not isinstance(events,list): return False,"events"
    if rel["status"] in {"VERIFIED_EMPTY","UNVERIFIED","FAILED"} and not any(isinstance(e,dict) and e.get("type")=="RELEASE_TRANSITION" for e in events):
        return False,"release_event_not_retained"
    if row.get("uncertainty")=="NONE" and (obs is None or ack["status"]!="ACKED"): return False,"implicit_confirmation"
    return True,"ok"

def base():
    return {"schema":SCHEMA,"state_id":"s1","owner_id":"o1","owner_revision":2,"observation_id":"obs1","surface_id":"surface1","coordinate_frame":"window_client","commanded_pointer":{"x":10,"y":20},"observed_pointer":{"x":10,"y":20},"held_keys":[],"held_buttons":[],"input_ack":{"id":"ack1","status":"ACKED"},"release":{"status":"NOT_TERMINAL","retained":False},"uncertainty":"NONE","events":[]}

cases=[]
r=base(); cases.append(("confirmed",r,True))
r=base(); r["uncertainty"]="OS_UNCONFIRMED"; r["observed_pointer"]=None; r["input_ack"]["status"]="UNKNOWN"; cases.append(("os_unconfirmed",r,True))
r=base(); r["release"]={"status":"VERIFIED_EMPTY","retained":True}; r["events"]=[{"type":"RELEASE_TRANSITION","status":"VERIFIED_EMPTY"}]; cases.append(("release_retained",r,True))
r=base(); r["release"]={"status":"FAILED","retained":True}; r["events"]=[]; cases.append(("release_event_missing",r,False))
r=base(); r["authority"]={"lease_id":"extend-me"}; cases.append(("authority_promotion",r,False))
r=base(); r["uncertainty"]="NONE"; r["observed_pointer"]=None; cases.append(("implicit_confirmation",r,False))
r=base(); r["surface_id"]=""; cases.append(("missing_surface_binding",r,False))

results=[]
for name,row,want in cases:
    got,reason=validate(row); results.append({"case":name,"expected":want,"accepted":got,"reason":reason,"pass":got==want})
print(json.dumps({"schema":SCHEMA,"cases":results,"decision":"PASS_MOTOR_STATE_CONTRACT_SCOPED" if all(x["pass"] for x in results) else "FAIL_MOTOR_STATE_CONTRACT","scope":"contract audit only; no runtime authority or GUI claim"},indent=2))
raise SystemExit(0 if all(x["pass"] for x in results) else 1)
