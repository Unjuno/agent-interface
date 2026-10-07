"""Ordinary contract test of explicit noncompleted decision mappings."""
import json,pathlib,copy
import adaptive_acquisition_caller_v3 as caller
root=pathlib.Path(__file__).resolve().parent
saved=json.loads((root/'native_raw.json').read_text());rows=[]
cases=[('preinput_refusal',dict(status='safe_yield',reason='execution_refused',completed_actions=0,input_dispatched=False)),('partial_execution_failure',dict(status='safe_yield',reason='execution_failed',completed_actions=1,input_dispatched=True)),('release_unverified_after_prefix',dict(status='safe_yield',reason='delivery_uncertain',completed_actions=33,input_dispatched=True))]
for name,decision in cases:
    callbacks=[];events=[]
    def execute(p):callbacks.append('saved_decision_execute');return copy.deepcopy(decision)
    def verify(p):callbacks.append('verify');raise RuntimeError('noncompleted execution must not verify')
    result=caller.run(saved['caller_spec'],dict(reuse_revalidate=lambda p:{'status':'revalidated'},final_revalidate=lambda p:{'status':'revalidated'},execute=execute,verify_effect=verify,journal=events.append))
    rows.append(dict(case=name,decision=decision,callbacks=callbacks,result=result,events=events))
print(json.dumps(dict(rows=rows,native_input_calls=0,scope='explicit authored projection contract; no actual native failure or automatic converter'),indent=2))
