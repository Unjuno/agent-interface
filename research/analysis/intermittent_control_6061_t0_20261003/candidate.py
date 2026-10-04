import json, math, sys

fixture=json.load(open(sys.argv[1],encoding="utf-8"))
H=fixture["horizon"]
rows=[]

def clip(v,m):
    return max(-m,min(m,v))

for s in fixture["rows"]:
    for policy in ("fixed","triggered","sample_hold","yield"):
        agent=s["initial_agent"]
        velocity=s["initial_velocity"]
        last_capture_t=0
        last_capture_x=s["target"][0]
        prev_residual=0.0
        captures=[0] if policy!="yield" else []
        actions=[]
        release=None
        residual_checks=0
        chunks=1 if policy!="yield" else 0
        if policy=="yield":
            release="voluntary_yield"
        else:
            for t in range(H):
                if not (s["present"][t] and s["lease"][t] and s["focus"][t] and s["bound"][t]):
                    release="target_lost" if not s["present"][t] else "lease_invalid" if not s["lease"][t] else "focus_invalid" if not s["focus"][t] else "target_binding_unknown"
                    break
                observe=(t==0 or policy=="fixed" or
                         (policy=="sample_hold" and t % fixture["capture_period"]==0))
                residual=0.0
                if policy=="triggered":
                    residual_checks+=1
                    prediction=last_capture_x+velocity*(t-last_capture_t)
                    residual=s["fast_position"][t]-prediction
                    if t>0 and abs(residual)>fixture["residual_threshold"]:
                        observe=True
                        velocity=clip(velocity+residual-prev_residual,fixture["max_speed"])
                if observe and t>0:
                    captures.append(t)
                    chunks+=1
                    if policy in ("fixed","sample_hold"):
                        velocity=clip((s["target"][t]-last_capture_x)/(t-last_capture_t),fixture["max_speed"])
                    last_capture_t=t
                    last_capture_x=s["target"][t]
                prev_residual=0.0 if observe else residual
                velocity=clip(velocity,fixture["max_speed"])
                agent+=velocity
                actions.append({"tick":t,"input":velocity})
            if release is None:
                release="horizon"
        end_t=len(actions)
        target_x=s["target"][end_t-1] if end_t else s["target"][0]
        error=abs(agent-target_x)
        rows.append({"scenario":s["id"],"policy":policy,"capture_ticks":captures,"residual_checks":residual_checks,"chunks":chunks,"actions":actions,"release":release,"final_agent":agent,"final_target":target_x,"final_error":error,"effect":bool(release=="horizon" and end_t==H and error<=0.5),"safe":all(a["tick"]<H and s["present"][a["tick"]] and s["lease"][a["tick"]] and s["focus"][a["tick"]] and s["bound"][a["tick"]] for a in actions)})
print(json.dumps({"schema":"intermittent-t0-candidate-v1","rows":rows},sort_keys=True))
