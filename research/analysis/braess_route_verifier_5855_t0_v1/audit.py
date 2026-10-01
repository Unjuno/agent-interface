"""Independent raw-only DES reconstruction for the frozen #5855 T0."""
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).parent
raw = json.loads((ROOT / "candidate-output" / "candidate-result.json").read_text(encoding="utf-8"))
N, DEADLINE = 16, 32
OBS, MODEL, SLOW_LOCAL, FAST_LOCAL, SLOW_V, CLEANUP = 2, 8, 5, 4, 4, 1


def replay(bits, interval, fast_v, disjoint=False):
    output_free = 0
    model_free = 0
    path_free = {"A": 0, "B": 0, "F": 0}
    jobs = []
    for j in range(N):
        arrival = j * interval
        observed = max(arrival, output_free) + OBS
        output_free = observed
        fast = bits[j] == "1"
        klass = "A" if j % 2 == 0 else "B"
        if fast:
            path = "F"
            model_end = None
            ready = observed
            service = FAST_LOCAL
        else:
            path = klass
            model_start = max(observed, model_free)
            model_end = model_start + MODEL
            model_free = model_end
            ready = model_end
            service = SLOW_LOCAL
        local_start = max(ready, path_free[path])
        local_end = local_start + service
        path_free[path] = local_end
        jobs.append({"id":j,"arrival":arrival,"class":klass,"route":path,"observation_done":observed,
                     "model_start":None if fast else model_end-MODEL,"model_done":model_end,
                     "local_start":local_start,"local_done":local_end,
                     "verify_work":fast_v if fast else SLOW_V})
    wait_sum = 0
    if disjoint:
        verifier_lanes = {"A":0,"B":0}
        fast_count = fast_v // SLOW_V
        fast_lanes = [0] * fast_count
        for job in sorted(jobs,key=lambda z:(z["local_done"],z["id"])):
            if job["route"]=="F":
                starts=[]
                ends=[]
                for k in range(fast_count):
                    s=max(job["local_done"],fast_lanes[k])
                    starts.append(s)
                    fast_lanes[k]=s+SLOW_V
                    ends.append(fast_lanes[k])
                job["verify_start"]=min(starts)
                job["verify_done"]=max(ends)
                job["verify_wait"]=max(0,max(starts)-job["local_done"])
            else:
                lane=job["route"]
                s=max(job["local_done"],verifier_lanes[lane])
                job["verify_start"]=s
                job["verify_done"]=s+SLOW_V
                job["verify_wait"]=s-job["local_done"]
                verifier_lanes[lane]=job["verify_done"]
            wait_sum += job["verify_wait"]
    else:
        verifier_free=0
        for job in sorted(jobs,key=lambda z:(z["local_done"],z["id"])):
            s=max(job["local_done"],verifier_free)
            job["verify_start"]=s
            job["verify_done"]=s+job["verify_work"]
            job["verify_wait"]=s-job["local_done"]
            verifier_free=job["verify_done"]
            wait_sum += job["verify_wait"]
    clean_free=0
    for job in sorted(jobs,key=lambda z:(z["verify_done"],z["id"])):
        s=max(job["verify_done"],clean_free)
        job["cleanup_start"]=s
        job["completion"]=s+CLEANUP
        job["latency"]=job["completion"]-job["arrival"]
        job["cleanup_wait"]=s-job["verify_done"]
        job["effect_exact"]=job["release_verified"]=job["safety_passed"]=True
        job["on_time"]=job["latency"]<=DEADLINE
        clean_free=job["completion"]
    lat=sorted(z["latency"] for z in jobs)
    return {"mask":bits,"fast_count":bits.count("1"),"mean_latency":sum(lat)/N,
            "p95_latency":lat[math.ceil(.95*N)-1],"on_time":sum(z["on_time"] for z in jobs),
            "verifier_work":sum(z["verify_work"] for z in jobs),"verifier_wait_total":wait_sum,
            "model_calls":sum(z["route"]!="F" for z in jobs),
            "synthetic_model_wait":sum(MODEL for z in jobs if z["route"]!="F"),
            "synthetic_token_units":sum(20 for z in jobs if z["route"]!="F"),
            "observation_work":N*OBS,"cleanup_work":N*CLEANUP,
            "exact_effects":sum(z["effect_exact"] for z in jobs),
            "verified_releases":sum(z["release_verified"] for z in jobs),
            "safety_passes":sum(z["safety_passed"] for z in jobs),"tasks":jobs}


def central(interval, fast_v):
    winner=None
    max_due=-1
    best_due="0"*N
    for number in range(1<<N):
        bits=format(number,f"0{N}b")
        score=replay(bits,interval,fast_v)
        if score["on_time"]>max_due:
            max_due=score["on_time"]
            best_due=bits
        obj=(round(score["mean_latency"]*N,8),score["p95_latency"],number)
        if winner is None or obj<winner[0]:
            winner=(obj,score)
    return winner[1],max_due,best_due


assert raw["schema"]=="braess-route-verifier-t0-result-v1"
assert raw["offers_per_scenario"]==N and raw["deadline_ticks"]==DEADLINE
assert raw["same_offers_across_policies"] is True
checks=0
held=None
overload=None
for case in raw["scenarios"]:
    interval=case["arrival_interval"]
    fast_v=case["fast_verify_work"]
    all_slow="0"*N
    all_fast="1"*N
    cap_n=case["cap_rule"]["fast_count"]
    cap_bits="".join("1" if math.floor((i+1)*cap_n/N)>math.floor(i*cap_n/N) else "0" for i in range(N))
    expected={
      "baseline": replay(all_slow,interval,fast_v),
      "greedy": replay(all_fast,interval,fast_v),
      "capped": replay(cap_bits,interval,fast_v),
    }
    central_result,max_due,best_due=central(interval,fast_v)
    for key,value in expected.items():
        assert case[key]==value,(interval,fast_v,key)
        checks+=1
    assert case["central_exact"]==central_result
    assert case["maximum_deadline_success_over_all_assignments"]==max_due
    assert case["best_deadline_mask"]==best_due
    checks+=1
    for policy in ("baseline","greedy","capped","central_exact"):
        result=case[policy]
        assert result["exact_effects"]==N and result["verified_releases"]==N and result["safety_passes"]==N
        assert all(r["effect_exact"] and r["release_verified"] and r["safety_passed"] for r in result["tasks"])
        assert [r["id"] for r in result["tasks"]]==list(range(N))
        assert [r["arrival"] for r in result["tasks"]]==[i*interval for i in range(N)]
    if interval==16 and fast_v==12:
        assert case["greedy"]["mean_latency"] < case["baseline"]["mean_latency"]
        assert case["greedy"]["p95_latency"] <= case["baseline"]["p95_latency"]
    if interval==8 and fast_v==12:
        held=case
        assert case["held_out"] is True
        assert case["route_isolated_cost"]["fast"] < case["route_isolated_cost"]["slow"]
        assert case["greedy"]["mean_latency"] >= case["baseline"]["mean_latency"]+10
        assert case["greedy"]["p95_latency"] >= case["baseline"]["p95_latency"]+10
        assert case["greedy"]["verifier_work"] > case["baseline"]["verifier_work"]
        assert case["greedy"]["verifier_wait_total"] > case["baseline"]["verifier_wait_total"]
        assert case["capped"]["mean_latency"] <= case["baseline"]["mean_latency"]+2
        assert case["capped"]["p95_latency"] <= case["baseline"]["p95_latency"]+2
        assert case["capped"]["on_time"]==N and case["capped"]["fast_count"]<N
        dis=case["disjoint_negative_control"]
        assert dis["greedy"]["mean_latency"] < dis["baseline"]["mean_latency"]
        assert dis["greedy"]["verifier_wait_total"]==0
    if interval==2 and fast_v==12:
        overload=case
        assert max_due<N
        assert case["maximum_deadline_success_over_all_assignments"]==max_due
    checks+=N*4

assert len(raw["scenarios"])==6 and held is not None and overload is not None
print(json.dumps({"audit":"PASS_SYNTHETIC_DISCRETE_EVENT_RECONSTRUCTION",
                  "scenario_count":len(raw["scenarios"]),"offers_replayed":len(raw["scenarios"])*N,
                  "assignment_vectors_enumerated":len(raw["scenarios"])*(1<<N),
                  "heldout_shared_queue_paradox":True,"benefit_control":True,
                  "disjoint_negative_control":True,"cap_control":True,
                  "overload_deadline_unsatisfiable":overload["maximum_deadline_success_over_all_assignments"],
                  "assertion_groups":checks,"scope":"finite synthetic model only"},sort_keys=True))
