import json, sys
from pathlib import Path

REQ = (
    'real_app',
    'pre_action_decision',
    'operation_target_choice_not_preselected',
    'finite_candidate_set',
    'intent_fixed_predecision',
    'independent_acceptable_set',
    'label_not_final_score_derived',
    'arguments_complete',
    'no_oracle_feature_leakage',
)

def qualify(e):
    return all(e['gates'][k] is True for k in REQ)

def compute(ledger):
    entries=[]
    for e in ledger['entries']:
        q=qualify(e)
        x=dict(e)
        x['oracle_qualified']=q
        entries.append(x)
    qual=[e for e in entries if e['oracle_qualified']]
    pos=sum(e['rows'] for e in qual if e['semantic_class']=='positive')
    neg=sum(e['rows'] for e in qual if e['semantic_class']=='negative')
    total=sum(e['rows'] for e in qual)
    reviewed=sum(e['rows'] for e in entries)
    ops=sorted({e['operation_family'] for e in qual if e.get('operation_family')})
    alt=sum(e['rows'] for e in qual if e.get('target_alternatives',False))
    explicit=sum(e['rows'] for e in qual if e.get('explicit_yield_no_local_action',False))
    direct=sum(e['rows'] for e in qual if e.get('direct_1015_compatible',False))
    adapter=sum(e['rows'] for e in qual if e.get('lossless_adapter_eligible',False))
    split=len({e['split_unit'] for e in qual})
    leakage=sum(e['rows'] for e in qual if not e['gates']['no_oracle_feature_leakage'])
    ready_gates={
        'positive_rows_ge_32': pos>=32,
        'negative_rows_ge_32': neg>=32,
        'operation_families_ge_2': len(ops)>=2,
        'target_alternative_rows_gt_0': alt>0,
        'explicit_yield_no_action_gt_0': explicit>0,
        'independent_split_units_ge_12': split>=12,
        'direct_1015_compatibility_for_all_qualified': direct==total,
        'oracle_leakage_zero': leakage==0,
    }
    ready=all(ready_gates.values())
    if ready:
        decision='READY_RETAINED_REALDESKTOP_OPERATION_TARGET_CORPUS'
    elif total>0:
        decision='PARTIAL_REALDESKTOP_ORACLE_PROGRESS_BLOCKED_DATA'
    else:
        decision='BLOCKED_DATA_NO_NEW_ORACLE_ROWS'
    return {
        'task': ledger['task'],
        'formal_invocations':1,
        'reruns':0,
        'reviewed_opportunities':reviewed,
        'oracle_qualified_rows':total,
        'oracle_qualified_positive_rows':pos,
        'oracle_qualified_semantic_negative_rows':neg,
        'qualified_operation_families':ops,
        'qualified_operation_family_count':len(ops),
        'target_alternative_rows':alt,
        'explicit_yield_no_local_action_rows':explicit,
        'direct_1015_compatible_rows':direct,
        'lossless_adapter_eligible_rows':adapter,
        'independent_split_units':split,
        'oracle_leakage_rows':leakage,
        'ready_gates':ready_gates,
        'decision':decision,
        'entries':entries,
        'model_calls':0,
        'gui_actions':0,
        'task_input_actions':0,
    }

def main():
    if len(sys.argv)!=3: raise SystemExit('usage: analyze.py LEDGER OUT')
    ledger=json.loads(Path(sys.argv[1]).read_text())
    out=compute(ledger)
    Path(sys.argv[2]).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='entries'},indent=2,sort_keys=True))
if __name__=='__main__':main()
