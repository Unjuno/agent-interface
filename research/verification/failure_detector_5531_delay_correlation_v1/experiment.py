"""One-shot synthetic delay/correlation experiment for Issue #5531."""
import json, random, os, sys, hashlib, platform

ALLOCATION = "fd5531-delay-correlation-20261001-01"
N = 10000
HORIZON = 16
THRESHOLDS = (2, 4, 8)
SCENARIOS = ("healthy_fast", "healthy_heavy_tail", "partition_recover", "crashed", "restarted")
SEED_BASE = 55310000

def draw_episode(scenario, seed):
    r = random.Random(seed)
    if scenario == "healthy_fast":
        response = r.randint(1, 3); restart = None
    elif scenario == "healthy_heavy_tail":
        z = r.random()
        response = r.randint(1, 3) if z < .75 else (r.randint(4, 8) if z < .95 else r.randint(9, 16))
        restart = None
    elif scenario == "partition_recover":
        response = r.randint(3, 12) + r.randint(1, 3); restart = None
    elif scenario == "crashed":
        response = None; restart = None
    else:
        restart = 10; response = restart + r.randint(1, 3)
    # Two observers share domain host-A; the third is on independent host-B.
    common_false = (r.random() < .04) if scenario != "crashed" else False
    independent_false = (r.random() < .005) if scenario != "crashed" else False
    host_a = (common_false or r.random() < .005) if scenario != "crashed" else (r.random() < .96)
    host_b = independent_false if scenario != "crashed" else (r.random() < .94)
    return {"response_tick": response, "restart_tick": restart,
            "host_a_witness": host_a, "host_b_witness": host_b,
            "decoys": [{"tick": 3, "kind": "SEMANTICALLY_INVALID", "generation": 1},
                       {"tick": 5, "kind": "STALE_RESPONSE", "generation": 0}]}

def run_candidate(ep, threshold):
    state = "AUTHORIZED"; generation = 1; suspect_ticks = 0
    false_reactivation = 0; clear_tick = None; failed_tick = None; terminal_failures = 0; decoys_ignored = 0
    for tick in range(HORIZON + 1):
        if ep["restart_tick"] == tick:
            generation += 1
            if state == "FAILED":
                state = "AUTHORIZED"
        if tick == 6 and ep["host_a_witness"] and ep["host_b_witness"]:
            state = "FAILED"; failed_tick = tick; terminal_failures += 1
        if state == "AUTHORIZED" and tick >= threshold and (ep["response_tick"] is None or ep["response_tick"] > tick):
            state = "SUSPECTED_UNAVAILABLE"
        if any(d["tick"] == tick for d in ep["decoys"]):
            decoys_ignored += 1
        # Only current-generation, semantically valid responses clear suspicion.
        if ep["response_tick"] == tick and tick >= (ep["restart_tick"] or 0):
            if state == "FAILED":
                false_reactivation += 1
            elif state == "SUSPECTED_UNAVAILABLE":
                state = "AUTHORIZED"; clear_tick = tick
        if state == "SUSPECTED_UNAVAILABLE":
            suspect_ticks += 1
    return {"final": state, "suspect_ticks": suspect_ticks, "false_reactivation": false_reactivation,
            "clear_tick": clear_tick, "failed_tick": failed_tick,
            "terminal_failures": terminal_failures, "decoys_ignored": decoys_ignored}

def run_baseline(ep, threshold):
    state = "AUTHORIZED"; suspect_ticks = 0; failed_tick = None
    for tick in range(HORIZON + 1):
        if ep["restart_tick"] == tick and state == "FAILED":
            state = "AUTHORIZED"
        if state == "AUTHORIZED" and tick >= threshold and (ep["response_tick"] is None or ep["response_tick"] > tick):
            state = "FAILED"; failed_tick = tick
        # Baseline treats a late response as insufficient to clear terminal failure.
        if state == "SUSPECTED_UNAVAILABLE": suspect_ticks += 1
    return {"final": state, "suspect_ticks": suspect_ticks, "false_reactivation": 0,
            "clear_tick": None, "failed_tick": failed_tick, "terminal_failures": int(failed_tick is not None), "decoys_ignored": 0}

def summarize(policy, threshold):
    rows = []
    for scenario_index, scenario in enumerate(SCENARIOS):
        agg = {"n": N, "final": {}, "false_failed": 0, "crash_failed_by_8": 0,
               "suspect_tick_sum": 0, "suspect_any": 0, "false_reactivation": 0, "false_terminal_failures": 0, "decoys_ignored": 0,
               "hash_chain": "0" * 64}
        chain = bytes(32)
        for i in range(N):
            ep = draw_episode(scenario, SEED_BASE + scenario_index * N + i)
            result = (run_candidate(ep, threshold) if policy == "typed" else run_baseline(ep, threshold))
            agg["final"][result["final"]] = agg["final"].get(result["final"], 0) + 1
            agg["suspect_tick_sum"] += result["suspect_ticks"]
            agg["suspect_any"] += result["suspect_ticks"] > 0
            agg["false_reactivation"] += result["false_reactivation"]
            agg["decoys_ignored"] += result["decoys_ignored"]
            agg["false_terminal_failures"] += result["terminal_failures"] if scenario != "crashed" else 0
            is_crash = scenario == "crashed"
            agg["false_failed"] += result["final"] == "FAILED" and not is_crash
            agg["crash_failed_by_8"] += is_crash and result["failed_tick"] is not None and result["failed_tick"] <= 8
            row = f'{i}|{result["final"]}|{result["suspect_ticks"]}|{result["failed_tick"]}|{result["clear_tick"]}|{result["false_reactivation"]}|{result["terminal_failures"]}|{result["decoys_ignored"]}'.encode()
            chain = hashlib.sha256(chain + row).digest()
        agg["hash_chain"] = chain.hex()
        rows.append({"scenario": scenario, **agg})
    return rows

def main():
    output = {"schema": "fd5531-delay-correlation-raw-v1", "allocation": ALLOCATION,
              "freeze_blob_sha": os.environ.get("FREEZE_BLOB_SHA"),
              "runtime": {"python": platform.python_version(), "platform": sys.platform, "container": False},
              "parameters": {"episodes_per_scenario": N, "horizon": HORIZON, "thresholds": list(THRESHOLDS),
                "primary_threshold": 4, "witness_quorum": 2, "observer_domains": {"observer_a":"host-A","observer_b":"host-A","observer_c":"host-B"},
                "healthy_fast_delay": [1,3], "heavy_tail": {"p_fast":.75,"p_medium":.20,"p_slow":.05,"fast":[1,3],"medium":[4,8],"slow":[9,16]},
                "partition_recovery_delay": "uniform(3,12)+uniform(1,3)", "restart_tick":10,
                "false_witness": {"shared_domain_event_p":.04,"independent_domain_p":.005},
                "crash_witness": {"host_a_p":.96,"host_b_p":.94}, "seed_base":SEED_BASE},
              "threshold_results": {}}
    for threshold in THRESHOLDS:
        output["threshold_results"][str(threshold)] = {
            "typed": summarize("typed", threshold),
            "timeout_as_failure": summarize("baseline", threshold)}
    print(json.dumps(output, sort_keys=True, separators=(",",":")))
if __name__ == "__main__":
    main()
