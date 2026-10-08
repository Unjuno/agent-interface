import hashlib, json, random, sys

SEED=60012026
N=12
DECK=("localize_target","abstain_no_target","action_schema","temporal_cue","negative_control")
CASES=("stationary_noise","in_deck_behavior_shift","out_of_deck_shift","schema_only_break","prompt_context_drift","within_block_model_switch")

def phash(label): return hashlib.sha256(label.encode()).hexdigest()
def outcome(case,phase,probe,attempt,rng):
    p=.92
    if case=="in_deck_behavior_shift" and phase=="post" and probe!="negative_control": p=.35
    elif case=="out_of_deck_shift" and phase=="post" and probe=="route_task": p=.35
    elif case=="within_block_model_switch" and phase=="mid" and probe!="negative_control": p=.35
    elif case=="within_block_model_switch" and phase=="post" and probe!="negative_control": p=.35
    elif case=="prompt_context_drift" and phase=="post" and probe=="route_task": p=.35
    return int(rng.random()<p)

def main(path):
    rows=[]
    for ci,case in enumerate(CASES):
        episodes=200 if case=="stationary_noise" else (2 if case=="in_deck_behavior_shift" else 1)
        for episode in range(episodes):
            rng=random.Random(SEED+ci*1000+episode)
            if case=="schema_only_break":
                rows.append({"case":case,"episode":episode,"phase":"post","probe":"route_task","attempt":0,"route":"B","alias":"fixed-v1","model_fingerprint":"opaque-fixed-v1","metadata":"fixed-v1","prompt_hash":phash("task-v1"),"schema_ok":False,"correct":None,"request_id":f"{case}-schema-break"})
                continue
            phases=("pre","mid","post") if case=="within_block_model_switch" else ("pre","post")
            probes=DECK+(("out_of_deck",) if case=="out_of_deck_shift" else ())
            for phase in phases:
                canary_phase=phase
                for probe in probes:
                    for attempt in range(N):
                        rows.append({"case":case,"episode":episode,"phase":canary_phase,"probe":probe,"attempt":attempt,"route":"none","alias":"fixed-v1","model_fingerprint":"opaque-fixed-v1","metadata":"fixed-v1","prompt_hash":phash("canary-v1"),"schema_ok":True,"correct":outcome(case,canary_phase,probe,attempt,rng),"request_id":f"{case}-{episode}-canary-{canary_phase}-{probe}-{attempt}"})
                if phase in ("pre","post"):
                    order="AB" if episode%2==0 else "BA"
                    arm=order[0] if phase=="pre" else order[1]
                    task_prompt="task-v2" if case=="prompt_context_drift" and arm=="B" else "task-v1"
                    for attempt in range(N):
                        rows.append({"case":case,"episode":episode,"order":order,"phase":phase,"probe":"route_task","attempt":attempt,"route":arm,"alias":"fixed-v1","model_fingerprint":"opaque-fixed-v1","metadata":"fixed-v1","prompt_hash":phash(task_prompt),"schema_ok":True,"correct":outcome(case,phase,"route_task",attempt,rng),"request_id":f"{case}-{episode}-route-{arm}-{attempt}"})
    with open(path,"w",encoding="utf-8") as f:
        for row in rows: f.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")
    raw=open(path,"rb").read()
    print(json.dumps({"rows":len(rows),"raw_sha256":hashlib.sha256(raw).hexdigest(),"seed":SEED},sort_keys=True))
if __name__=="__main__": main(sys.argv[1])
