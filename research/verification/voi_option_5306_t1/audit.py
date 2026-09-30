import hashlib
import itertools
import json
import sys
from decimal import Decimal as D

raw_bytes = sys.stdin.buffer.read()
raw = json.loads(raw_bytes)
grid = {"p_safe":["0.2","0.4","0.6","0.8","0.95"], "loss":["1","4","16"],
        "sensitivity":["0.6","0.8","1"], "false_pass":["0","0.1","0.3"],
        "delay_cost":["0","0.05","0.2"]}
def oracle(p, loss, sensitivity, false_pass, delay):
    action = p - (D(1)-p)*loss
    stop = max(D(0), action)
    passed = max(D(0), p*sensitivity-(D(1)-p)*loss*false_pass)
    failed = max(D(0), p*(D(1)-sensitivity)-(D(1)-p)*loss*(D(1)-false_pass))
    after = passed + failed
    wait = after - delay
    premium = (D(1)-p)*loss if action > D("1e-12") else D(0)
    return {
        "action_value":action, "stop_value":stop, "pass_value":passed,
        "fail_value":failed, "test_value":after, "continue_value":wait,
        "net_voi":wait-stop, "immediate_action":"ADMIT" if action>D("1e-12") else "YIELD",
        "voi_decision":"CONTINUE" if wait>stop+D("1e-12") else "STOP",
        "bellman_decision":"CONTINUE" if wait>stop+D("1e-12") else "STOP",
        "option_premium":premium, "premium_continue_value":wait+premium,
        "premium_decision":"CONTINUE" if wait+premium>stop+D("1e-12") else "STOP",
        "premium_dominated_wait":wait+premium>stop+D("1e-12") and wait<stop-D("1e-12"),
    }
errors=[]
if raw.get("schema")!="voi_option_5306_t1_raw_v1": errors.append("schema")
if raw.get("base_main_sha")!="bc1ca7f316d86ecaee5f24b3f961b69f8be32eae": errors.append("base_sha")
rows=raw.get("rows",[])
expected=list(itertools.product(grid["p_safe"],grid["loss"],grid["sensitivity"],grid["false_pass"],grid["delay_cost"]))
if len(rows)!=405: errors.append("row_count")
seen=set(); mismatches=0; changes=0; dominated=0
for idx,(row,vals) in enumerate(zip(rows,expected)):
    cid=f"voi-option-{idx:03d}"
    if row.get("case_id")!=cid or cid in seen: errors.append("coverage_or_duplicate")
    seen.add(cid)
    inp=row.get("inputs",{})
    if [D(str(inp.get(k))) for k in ("p_safe","loss","sensitivity","false_pass","delay_cost")] != [D(v) for v in vals]: errors.append("input_grid")
    want=oracle(*[D(v) for v in vals])
    for key,expected_value in want.items():
        actual=row.get(key)
        if isinstance(expected_value,D):
            try:
                if abs(D(str(actual))-expected_value)>D("1e-10"): errors.append("value_mismatch")
            except Exception: errors.append("non_numeric")
        elif actual!=expected_value: errors.append("decision_mismatch")
    mismatches+=int(row.get("voi_decision")!=row.get("bellman_decision"))
    changes+=int(row.get("premium_decision")!=row.get("voi_decision"))
    dominated+=int(bool(row.get("premium_dominated_wait")))
if len(seen)!=405: errors.append("unique_coverage")
summary={"case_count":405,"voi_bellman_mismatches":mismatches,
         "premium_decision_changes":changes,"premium_dominated_waits":dominated}
if raw.get("summary",{}).get("case_count")!=405 or raw.get("summary",{}).get("voi_bellman_mismatches")!=mismatches or raw.get("summary",{}).get("premium_decision_changes")!=changes or raw.get("summary",{}).get("premium_dominated_waits")!=dominated: errors.append("summary")
if mismatches: errors.append("voi_oracle_disagreement")
if dominated==0: errors.append("no_dominated_premium_wait")
out={"schema":"voi_option_5306_t1_audit_v1","status":"PASS_REDUNDANCY_SCOPED" if not errors else "FAIL_AUDIT",
     "errors":errors,"case_count":len(rows),"voi_bellman_mismatches":mismatches,
     "premium_decision_changes":changes,"premium_dominated_waits":dominated,
     "raw_sha256":hashlib.sha256(raw_bytes).hexdigest()}
print(json.dumps(out,sort_keys=True,separators=(",",":")))
raise SystemExit(0 if not errors else 1)
