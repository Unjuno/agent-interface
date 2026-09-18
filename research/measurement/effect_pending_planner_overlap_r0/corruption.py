#!/opt/pyvenv/bin/python3
import json,pathlib
from model import EffectPendingTracker


def run_trace(trace):
    t=EffectPendingTracker()
    for x in trace: t.ingest_symbol(x)
    return t.view()

controls={
 "authority_escalation": run_trace(["RELEASE_OK","EFFECT_AUTH"]),
 "wrong_token": run_trace(["RELEASE_OK","EFFECT_BAD_TOKEN"]),
 "effect_after_timeout": run_trace(["RELEASE_OK","TIMEOUT","EFFECT_OK"]),
 "duplicate_effect": run_trace(["RELEASE_OK","EFFECT_OK","EFFECT_OK"]),
 "terminal_not_effect": run_trace(["RELEASE_OK","TERMINAL_OK"]),
}
passed={
 "authority_escalation": controls["authority_escalation"]["state"]=="needs_reconciliation" and not controls["authority_escalation"]["task_effect_resolved"],
 "wrong_token": controls["wrong_token"]["state"]=="needs_reconciliation" and not controls["wrong_token"]["task_effect_resolved"],
 "effect_after_timeout": controls["effect_after_timeout"]["state"]=="needs_reconciliation" and not controls["effect_after_timeout"]["task_effect_resolved"],
 "duplicate_effect": controls["duplicate_effect"]["state"]=="needs_reconciliation" and not controls["duplicate_effect"]["task_effect_resolved"],
 "terminal_not_effect": controls["terminal_not_effect"]["state"]=="tracked" and controls["terminal_not_effect"]["task_effect_status"]=="pending" and not controls["terminal_not_effect"]["task_effect_resolved"],
}
out={"controls":controls,"passed":passed,"pass_count":sum(passed.values()),"total":len(passed)}
pathlib.Path('/tmp/ai_1616/CORRUPTION.json').write_text(json.dumps(out,indent=2,sort_keys=True))
print(json.dumps({"passed":passed,"pass_count":out["pass_count"],"total":out["total"]},indent=2))
raise SystemExit(0 if all(passed.values()) else 1)
