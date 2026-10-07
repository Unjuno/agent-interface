import pathlib,json,copy
from strict_converter import convert
import caller_main as caller
R=pathlib.Path(__file__).resolve().parent;saved=json.loads((R/'native-first-result.json').read_text(encoding='utf-8-sig'));rows=[]
for source in saved['rows']:
    row={'case':source['case'],'native_program':source['program'],'native_receipt':source['native_receipt'],'conversion':convert(source['program'],source['native_receipt']),'calls':[],'events':[]}
    def execute(_):row['calls'].append('execute');return copy.deepcopy(row['conversion']['decision'])
    def verify(_):row['calls'].append('verify');return {'status':'unavailable'}
    row['caller_result']=caller.run(json.loads((R/'caller_spec.json').read_text()),dict(reuse_revalidate=lambda _:{'status':'revalidated'},final_revalidate=lambda _:{'status':'revalidated'},execute=execute,verify_effect=verify,journal=row['events'].append))
    rows.append(row)
expected={'completed':'TASK_NOT_VERIFIED','preinput_refusal':'EXECUTION_INCOMPLETE','partial_wait_fault':'EXECUTION_INCOMPLETE','release_omission':'EXECUTION_INCOMPLETE'}
compatible=all(row['caller_result']['outcome']==expected[row['case']] for row in rows)
print(json.dumps({'rows':rows,'disposition':'SUPPORT_CURRENT_MAIN_DECISION_ACCEPTANCE_SCOPED' if compatible else 'HOLD_CURRENT_MAIN_COMPOSITION','native_runs':0,'model_calls':0},indent=2))
# Retain compatibility failures as scientific outcomes, not runner crashes.
raise SystemExit(0)
