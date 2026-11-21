#!/usr/bin/env python3
"""Independent raw-event reconstruction and frozen decision gate for #7722."""
import argparse, copy, hashlib, json, math, random
from collections import deque
from pathlib import Path

POLICIES = ("shared_priority", "shared_backpressure", "reserved_server")
BUDGET_KEYS = ("period_ticks", "horizon_ticks", "total_budget_ticks", "control_budget_ticks",
               "best_effort_budget_ticks", "control_service_ticks", "best_effort_service_ticks",
               "control_deadline_ticks", "backpressure_queue_jobs")

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def expected_jobs(cfg, case):
    out = {}
    p = cfg["period_ticks"]
    def put(jid, kind, release, work):
        out[jid] = {"job_class": kind, "release_tick": release, "required_ticks": work,
                    "deadline_tick": release + cfg["control_deadline_ticks"] if kind == "control" else None}
    if case["kind"] in ("schedulable", "negative"):
        for epoch, off in enumerate(case["control_offsets"]):
            put(f"{case['case_id']}-c{epoch}", "control", epoch*p+off, cfg["control_service_ticks"])
            for j in range(case["best_effort_jobs_per_period"]):
                put(f"{case['case_id']}-b{epoch}-{j}", "best_effort", epoch*p,
                    cfg["best_effort_service_ticks"])
    else:
        for j, at in enumerate(case["control_offsets"]):
            put(f"{case['case_id']}-c{j}", "control", at, cfg["control_service_ticks"])
        for j in range(case["best_effort_jobs_per_period"]):
            put(f"{case['case_id']}-b0-{j}", "best_effort", 0, cfg["best_effort_service_ticks"])
    return out

def check_run(run, cfg, case):
    errors = []
    policy = run.get("policy")
    if run.get("case_id") != case["case_id"] or run.get("kind") != case["kind"]:
        errors.append("run_identity_mismatch")
    if policy not in POLICIES:
        return ["unknown_policy"]
    expected = expected_jobs(cfg, case)
    rows = run.get("jobs")
    if not isinstance(rows, list):
        return ["job_rows_missing"]
    by_id = {r.get("job_id"): r for r in rows if isinstance(r, dict)}
    if len(by_id) != len(rows) or set(by_id) != set(expected):
        errors.append("job_obligation_set_mismatch")
    evs = run.get("events")
    if not isinstance(evs, list):
        return errors + ["events_missing"]
    service = {jid: [] for jid in expected}
    global_window, ctl_window, be_window = deque(), deque(), deque()
    previous_tick = -1
    for ev in evs:
        if not isinstance(ev, dict):
            errors.append("malformed_event"); continue
        t, jid = ev.get("tick"), ev.get("job_id")
        if not isinstance(t, int) or t < 0 or t >= cfg["horizon_ticks"]:
            errors.append("event_tick_out_of_range"); continue
        if t <= previous_tick:
            errors.append("cpu_overlap_or_event_order"); continue
        previous_tick = t
        if jid not in expected:
            errors.append("unknown_or_uncharged_job"); continue
        job = expected[jid]
        if t < job["release_tick"] or ev.get("job_class") != job["job_class"]:
            errors.append("service_before_release_or_wrong_class")
        if ev.get("service_ticks") != 1:
            errors.append("uncharged_or_nonunit_service")
        correct_channels = ["global"]
        if policy == "reserved_server":
            correct_channels.append("control" if job["job_class"] == "control" else "best_effort")
        if ev.get("channels") != correct_channels:
            errors.append("budget_channel_mismatch")
        for q in (global_window, ctl_window, be_window):
            while q and q[0] <= t - cfg["period_ticks"]:
                q.popleft()
        if len(global_window) >= cfg["total_budget_ticks"]:
            errors.append("global_budget_exceeded")
        global_window.append(t)
        if policy == "reserved_server":
            q, limit = ((ctl_window, cfg["control_budget_ticks"]) if job["job_class"] == "control"
                        else (be_window, cfg["best_effort_budget_ticks"]))
            if len(q) >= limit:
                errors.append("class_budget_early_replenishment_or_excess")
            q.append(t)
        service[jid].append(t)
    rejected = run.get("rejected_best_effort")
    if not isinstance(rejected, list) or len(rejected) != len(set(rejected)):
        errors.append("backpressure_rejection_record_invalid"); rejected = []
    if not set(rejected).issubset({jid for jid,j in expected.items() if j["job_class"] == "best_effort"}):
        errors.append("invalid_rejected_job")
    computed = {}
    for jid, spec in expected.items():
        ticks = service[jid]
        complete = len(ticks) == spec["required_ticks"]
        if len(ticks) > spec["required_ticks"]:
            errors.append("job_over_service")
        finish = ticks[-1]+1 if complete else None
        status = "completed" if complete else ("rejected_backpressure" if jid in rejected else "pending")
        row = by_id.get(jid)
        expected_row = {"job_id": jid, **spec, "finish_tick": finish, "status": status}
        if row != expected_row:
            errors.append("job_result_false_or_missing")
        computed[jid] = expected_row
        if jid in rejected and ticks:
            errors.append("rejected_job_received_service")
    controls = [r for r in computed.values() if r["job_class"] == "control"]
    misses = [r for r in controls if r["finish_tick"] is None or r["finish_tick"] > r["deadline_tick"]]
    disposition = ("UNKNOWN_OVERLOAD" if misses and case["kind"] in ("overload", "boundary") else
                   "DEADLINE_MISS" if misses else "COMPLETED_WITHIN_DEADLINE")
    if run.get("disposition") != disposition:
        errors.append("overload_or_disposition_misreported")
    return errors

def nearest_rank_p99(values):
    if not values: return None
    s = sorted(values)
    return s[max(0, math.ceil(0.99*len(s))-1)]

def evaluate(raw, cfg, freeze, manifest, run_mutations=True):
    errors = []
    for c in cfg.get("cases", []):
        if c.get("kind") == "schedulable":
            rng = random.Random(c.get("seed"))
            generated = [rng.randint(400, 600) for _ in range(10)]
            if c.get("control_offsets") != generated:
                errors.append(f"{c.get('case_id')}:seeded_trace_mismatch")
    if raw.get("schema") != "cpu-control-7722-raw-v1": errors.append("raw_schema_mismatch")
    if raw.get("allocation_id") != cfg.get("allocation_id"): errors.append("allocation_mismatch")
    if raw.get("cases_sha256") != manifest["cases_sha256"]: errors.append("case_source_hash_mismatch")
    if raw.get("candidate_sha256") != manifest["candidate_sha256"]: errors.append("candidate_source_hash_mismatch")
    if raw.get("protocol_sha256") != manifest["protocol_sha256"]: errors.append("protocol_source_hash_mismatch")
    declared = {k: cfg[k] for k in BUDGET_KEYS}
    if raw.get("declared_budgets") != declared: errors.append("budget_or_deadline_declaration_mismatch")
    cases = {c["case_id"]: c for c in cfg["cases"]}
    runs = raw.get("runs")
    expected_keys = {(c["case_id"], p) for c in cfg["cases"] for p in POLICIES}
    seen = set()
    if not isinstance(runs, list):
        runs = []; errors.append("runs_missing")
    for run in runs:
        if not isinstance(run, dict):
            errors.append("malformed_run"); continue
        key = (run.get("case_id"), run.get("policy"))
        if key in seen: errors.append("duplicate_run")
        seen.add(key)
        if key[0] not in cases: errors.append("unknown_case"); continue
        errors.extend(f"{key[0]}/{key[1]}:{e}" for e in check_run(run, cfg, cases[key[0]]))
    if seen != expected_keys: errors.append("run_matrix_incomplete")

    run_index = {(r.get("case_id"),r.get("policy")):r for r in runs if isinstance(r,dict)}
    metrics = {}
    for c in cfg["cases"]:
        for p in POLICIES:
            r = run_index.get((c["case_id"],p), {})
            jobs = r.get("jobs", [])
            controls = [j for j in jobs if j.get("job_class")=="control"]
            responses = [(j["finish_tick"]-j["release_tick"] if j.get("finish_tick") is not None
                          else cfg["horizon_ticks"]-j["release_tick"]) for j in controls]
            misses = sum(j.get("finish_tick") is None or j.get("finish_tick")>j.get("deadline_tick",0) for j in controls)
            be_done = sum(j.get("job_class")=="best_effort" and j.get("status")=="completed" for j in jobs)
            metrics[(c["case_id"],p)] = {"p99_response_ticks":nearest_rank_p99(responses),
                 "control_deadline_misses":misses,"best_effort_completed":be_done,
                 "control_obligations":len(controls),"disposition":r.get("disposition")}
    h_errors=[]
    sched=[c for c in cfg["cases"] if c["kind"]=="schedulable"]
    for c in sched:
        m=metrics[(c["case_id"],"reserved_server")]
        for basep in ("shared_priority","shared_backpressure"):
            b=metrics[(c["case_id"],basep)]
            if b["p99_response_ticks"] is None or m["p99_response_ticks"] is None or m["p99_response_ticks"] > .8*b["p99_response_ticks"]:
                h_errors.append(f"{c['case_id']}:{basep}:p99_threshold")
            if b["control_deadline_misses"] < 1 or m["control_deadline_misses"] != 0:
                h_errors.append(f"{c['case_id']}:{basep}:deadline_gate")
        b=metrics[(c["case_id"],"shared_priority")]["best_effort_completed"]
        r=metrics[(c["case_id"],"reserved_server")]["best_effort_completed"]
        if b == 0 or (b-r)/b > .10:
            h_errors.append(f"{c['case_id']}:best_effort_loss")
    neg=next(c for c in cfg["cases"] if c["kind"]=="negative")
    n0=metrics[(neg["case_id"],"shared_priority")]["p99_response_ticks"]
    n1=metrics[(neg["case_id"],"reserved_server")]["p99_response_ticks"]
    if n0 is None or n1 is None or abs(n1-n0)/max(1,n0)>.05:
        h_errors.append("negative_control_not_equivalent")
    for c in cfg["cases"]:
        if c["kind"] in ("overload","boundary"):
            r=run_index.get((c["case_id"],"reserved_server"),{})
            if r.get("disposition")!="UNKNOWN_OVERLOAD": h_errors.append(f"{c['case_id']}:unknown_not_reported")
            if len([j for j in r.get("jobs",[]) if j.get("job_class")=="control"])!=len(c["control_offsets"]):
                h_errors.append(f"{c['case_id']}:control_obligation_lost")

    mutations={}
    if run_mutations and runs:
        def rejected(name, mutate_raw, mutate_cfg=None):
            rr=copy.deepcopy(raw); cc=copy.deepcopy(cfg)
            mutate_raw(rr)
            if mutate_cfg: mutate_cfg(cc)
            found,_=evaluate(rr,cc,freeze,manifest,False)
            mutations[name]=bool(found)
        rejected("budget_mutation",lambda r:r["declared_budgets"].update(total_budget_ticks=99))
        rejected("deadline_mutation",lambda r:r["declared_budgets"].update(control_deadline_ticks=99))
        def lose(r):
            r["runs"][0]["jobs"]=[j for j in r["runs"][0]["jobs"] if j["job_class"]!="control"]
        rejected("lost_obligation",lose)
        def early(r):
            x=r["runs"][0]["events"][0]; r["runs"][0]["events"].append(copy.deepcopy(x))
        rejected("early_replenishment_or_double_charge",early)
        def uncharged(r): r["runs"][0]["events"][0]["channels"]=[]
        rejected("uncharged_service",uncharged)
        def false(r): r["runs"][0]["jobs"][0]["finish_tick"]=-1
        rejected("false_completion",false)
    method_ok=not errors and len(mutations)==6 and all(mutations.values())
    h_ok=method_ok and not h_errors
    return ({"method":"METHOD_PASS_SCOPED" if method_ok else "FAIL_AUDIT",
             "hypothesis":"H_PASS_SCOPED" if h_ok else "FAIL_HYPOTHESIS",
             "errors":errors,"hypothesis_errors":h_errors,"mutation_rejections":mutations,
             "metrics":{f"{k[0]}/{k[1]}":v for k,v in metrics.items()}},
            not method_ok)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cases",required=True); ap.add_argument("--freeze",required=True)
    ap.add_argument("--raw",required=True)
    a=ap.parse_args()
    cfg=json.loads(Path(a.cases).read_text(encoding="utf-8-sig"))
    freeze=json.loads(Path(a.freeze).read_text(encoding="utf-8-sig"))
    raw=json.loads(Path(a.raw).read_text(encoding="utf-8-sig"))
    manifest=freeze["source_hashes"]
    result,_=evaluate(raw,cfg,freeze,manifest)
    actual={"cases_sha256":digest(Path(a.cases)),"candidate_sha256":digest(Path(__file__).with_name("candidate.py")),
            "auditor_sha256":digest(Path(__file__)),"protocol_sha256":digest(Path(__file__).with_name("PROTOCOL.md"))}
    if actual != {k:manifest[k] for k in actual}:
        result["errors"].append("frozen_source_hash_mismatch")
        result["method"]="FAIL_AUDIT"
        result["hypothesis"]="FAIL_HYPOTHESIS"
    if raw.get("freeze_sha256") != digest(Path(a.freeze)):
        result["errors"].append("freeze_identity_mismatch")
        result["method"]="FAIL_AUDIT"
        result["hypothesis"]="FAIL_HYPOTHESIS"
    result["auditor_sha256"]=digest(Path(__file__))
    print(json.dumps(result,sort_keys=True,separators=(",",":")))
    if result["method"]!="METHOD_PASS_SCOPED": raise SystemExit(2)

if __name__=="__main__": main()
