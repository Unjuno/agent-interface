import json
import time
from pathlib import Path

from research.live_control import integrated_efficiency_compiled_adapter_v1 as v1
from research.live_control import integrated_efficiency_compiled_adapter_v2 as v2
from runtime.core_v1.compiled_gui import run as run_compiled
from research.live_control.adaptive_acquisition_caller_v3 import run as run_caller

METHODS = {
    "v1": (v1, {"first_action":"enter_exact_token", "continue_when":"field_pixels_changed_and_submit_revalidated", "second_action":"activate_submit", "complete_when":"submission_pixels_changed_then_independent_score"}),
    "v2": (v2, {"first_action":"enter_exact_token", "continue_when":"exact_task_value_observed_and_submit_revalidated", "second_action":"activate_submit", "complete_when":"submission_pixels_changed_then_independent_score"}),
}
ROWS = [
    {"field_pixels_changed":False,"field_value_matches_task":False,"field_target_present":True,"submit_target_present":True,"submission_pixels_changed":False},
    {"field_pixels_changed":True,"field_value_matches_task":False,"field_target_present":True,"submit_target_present":True,"submission_pixels_changed":False},
    {"field_pixels_changed":True,"field_value_matches_task":False,"field_target_present":True,"submit_target_present":True,"submission_pixels_changed":True},
]
TARGET = {"field":"field-handle","submit":"submit-handle","session":"synthetic-session"}

class Clock:
    def __init__(self): self.value=1000
    def __call__(self): self.value+=10; return self.value

def arm(version, module, contract):
    compiled = module.compile_form_method(interface_id="caller-guard-a01", session_scope="synthetic-session", surface="form", field_handle="field-handle", submit_handle="submit-handle", method_contract=contract)
    seq = 0
    simulated_ops = []
    verify_calls = []
    inner_receipts = []
    def observe(_payload):
        nonlocal seq
        row=ROWS[seq]; seq+=1
        declared={k:v for k,v in row.items() if k in compiled["predicates"]}
        return {"sequence":seq,"captured_ns":time.perf_counter_ns(),"surface":"form","predicates":declared,"evidence_ref":f"synthetic-frame-{version}-{seq}","evidence_digest":f"synthetic-digest-{version}-{seq}"}
    def admit(payload):
        return {"eligible":True,"status":"revalidated","authorization":"synthetic-one-use","expected_sequence":payload["observation"]["sequence"],"valid_until_ns":time.perf_counter_ns()+1_000_000_000}
    def execute(payload):
        simulated_ops.append(payload["operation"])
        return {"status":"completed","action_id":f"{version}-action-{len(simulated_ops)}","effect_ref":f"{version}-effect-{len(simulated_ops)}","release":{"verified":True,"keys_down":[],"buttons_down":[]}}
    def inner_effect(payload):
        return {"status":"succeeded","evidence_ref":payload["observation"]["evidence_ref"]}
    def caller_execute(_payload):
        receipt=run_compiled(compiled,{"observe":observe,"admit":admit,"execute":execute,"verify_effect":inner_effect,"cancelled":lambda:False})
        inner_receipts.append(receipt)
        if receipt["outcome"] == "SAFE_YIELD":
            return {"status":"safe_yield","reason":receipt["reason"],"completed_actions":receipt["completed_transitions"]}
        if receipt["outcome"] == "TASK_SUCCEEDED":
            return {"status":"completed"}
        return {"status":"failed"}
    calls=[]
    def local(name, result):
        def f(_payload): calls.append(name); return result
        return f
    def score(_payload):
        verify_calls.append("independent_effect_check")
        # This fixed synthetic scorer knows exact task value was not observed.
        return {"status":"failed","evidence_ref":"synthetic-score-wrong-value"}
    spec={"target":"form","route":"reuse","coarse_origin":"caller_provided","provided_coarse":None,"cached_target":TARGET,"local_repair_on":[],"repair_on":[],"session_id":"caller-guard-a01"}
    adapters={"reuse_revalidate":local("reuse_revalidate",{"status":"revalidated"}),"final_revalidate":local("final_revalidate",{"status":"revalidated"}),"execute":caller_execute,"verify_effect":score,"journal":lambda _event:None}
    outer=run_caller(spec,adapters,clock=Clock(),id_factory=lambda:"unused-no-model-call")
    return {"version":version,"outer":outer,"runtime":inner_receipts[0],"simulated_ops":simulated_ops,"caller_stage_calls":calls,"scorer_calls":verify_calls,"observations_used":seq}

results=[arm(name,*entry) for name,entry in METHODS.items()]
v1r,v2r=results
ok=(v1r["runtime"]["outcome"]=="TASK_SUCCEEDED" and v1r["outer"]["outcome"]=="TASK_NOT_VERIFIED" and v1r["outer"]["task_effect"]=="failed" and v1r["simulated_ops"]==["enter_exact_token","activate_submit"] and v1r["scorer_calls"]==["independent_effect_check"] and v2r["runtime"]["outcome"]=="SAFE_YIELD" and v2r["outer"]["outcome"]=="EXECUTION_INCOMPLETE" and v2r["outer"]["reason"]=="effect_failed" and v2r["outer"]["delivery"]=="confirmed_partial" and v2r["outer"]["execution_progress"]["completed_actions"]==1 and v2r["simulated_ops"]==["enter_exact_token"] and v2r["scorer_calls"]==[] and all(x["outer"]["accounting"]["attempted_calls"]==0 for x in results))
raw={"experiment_id":"compiled-caller-guard-3311-20261005-a02","decision":"PASS_CALLER_ACCOUNTING_CONTRAST" if ok else "FAIL_CALLER_ACCOUNTING_CONTRAST","input_rows":ROWS,"actual_os_inputs":0,"model_requests":0,"results":results}
out=Path(__file__).parent / "runs/a02/raw.json"
with out.open("x",encoding="utf-8") as f: json.dump(raw,f,sort_keys=True,indent=2); f.write("\n")
print(json.dumps({"experiment_id":raw["experiment_id"],"decision":raw["decision"],"arms":[{"version":x["version"],"runtime_outcome":x["runtime"]["outcome"],"caller_outcome":x["outer"]["outcome"],"reason":x["outer"]["reason"],"delivery":x["outer"]["delivery"],"operations":x["simulated_ops"],"scorer_calls":len(x["scorer_calls"]),"model_calls":x["outer"]["accounting"]["attempted_calls"]} for x in results]},sort_keys=True,indent=2))
if not ok: raise SystemExit(1)
