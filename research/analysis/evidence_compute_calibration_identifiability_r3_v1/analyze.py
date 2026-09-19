import argparse,hashlib,json
from pathlib import Path
GOOD={'MEASURED_SAME_POPULATION','BOUNDED_SAME_POPULATION'}
EXPECTED={
'o3_relevance_generation':{'p':'AUTHORED_CONTROL'},
'x11_target_revalidation':{'p':'AUTHORED_CONTROL','g':'WRONG_MECHANISM'},
'adaptive_acquisition_testdouble':{'p':'TEST_DOUBLE_MECHANICS','reuse_rate':'TEST_DOUBLE_MECHANICS'},
'x11_phase_overlap':{'p':'AUTHORED_CONTROL','g':'WRONG_MECHANISM','w':'WRONG_MECHANISM'},
'current_evidence_guard_cost':{'p':'AUTHORED_CONTROL','version_maintenance_cost':'WRONG_MECHANISM'},
'reuse_semantic_theorem':{'p':'ANALYTIC_ONLY','reuse_rate':'ANALYTIC_ONLY'},
'integrated_efficiency_fixed_sequence':{'p':'DESCRIPTIVE_FIXED_SEQUENCE','reuse_rate':'DESCRIPTIVE_FIXED_SEQUENCE','g':'WRONG_MECHANISM'},
}
REQ=('p','g','w','reuse_rate','version_maintenance_cost')

def calibratable(row):
    return row.get('same_job_population') is True and row.get('commensurate_cost_model') is True and row.get('representative_population') is True and all(row['fields'].get(k) in GOOD for k in REQ)

def validate(ledger):
    errors=[]
    ids={r['id'] for r in ledger['families']}
    if set(EXPECTED)-ids: errors.append('missing_family')
    by={r['id']:r for r in ledger['families']}
    for fid,reqs in EXPECTED.items():
        for k,v in reqs.items():
            if by[fid]['fields'].get(k)!=v:errors.append(f'{fid}:{k}:role')
    if ledger.get('production_estimate') is not None:errors.append('production_estimate')
    if ledger.get('scheduler_recommendation') is not None:errors.append('scheduler_recommendation')
    if len(ledger.get('forbidden_substitutions',[]))<6:errors.append('forbidden_substitutions')
    return errors

def decide(ledger):
    errors=validate(ledger)
    cal=[r['id'] for r in ledger['families'] if calibratable(r)]
    blocked={r['id']:[k for k in REQ if r['fields'].get(k) not in GOOD] for r in ledger['families']}
    good=(not errors and len(ledger['families'])>=7 and not cal and all(blocked.values()))
    return {'decision':'PASS_RETAINED_EVIDENCE_COMPUTE_CALIBRATION_NOT_IDENTIFIABLE_SCOPED' if good else 'FAIL_INTEGRITY','errors':errors,'family_count':len(ledger['families']),'calibratable_families':cal,'blocking_fields':blocked,'production_estimate_emitted':ledger.get('production_estimate') is not None,'scheduler_recommendation_emitted':ledger.get('scheduler_recommendation') is not None}

def corruptions(ledger):
    out={}
    def mut(fid,field,value):
        x=json.loads(json.dumps(ledger));r=next(z for z in x['families'] if z['id']==fid);r['fields'][field]=value;return x
    out['authored_p_promotion_detected']=decide(mut('o3_relevance_generation','p','MEASURED_SAME_POPULATION'))['decision']=='FAIL_INTEGRITY'
    out['testdouble_reuse_promotion_detected']=decide(mut('adaptive_acquisition_testdouble','reuse_rate','MEASURED_SAME_POPULATION'))['decision']=='FAIL_INTEGRITY'
    out['phase_gain_as_g_detected']=decide(mut('x11_phase_overlap','g','MEASURED_SAME_POPULATION'))['decision']=='FAIL_INTEGRITY'
    out['guard_cost_as_version_cost_detected']=decide(mut('current_evidence_guard_cost','version_maintenance_cost','MEASURED_SAME_POPULATION'))['decision']=='FAIL_INTEGRITY'
    out['fixed_sequence_rate_promotion_detected']=decide(mut('integrated_efficiency_fixed_sequence','reuse_rate','MEASURED_SAME_POPULATION'))['decision']=='FAIL_INTEGRITY'
    x=json.loads(json.dumps(ledger));x['families'].append({'id':'cross_family_laundered','fields':{k:'MEASURED_SAME_POPULATION' for k in REQ},'same_job_population':True,'commensurate_cost_model':True,'representative_population':True});out['cross_family_laundering_detected']=decide(x)['decision']=='FAIL_INTEGRITY'
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ledger',required=True);ap.add_argument('--construction',action='store_true');ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();L=json.loads(Path(a.ledger).read_text());R=decide(L);R['corruption_controls']=corruptions(L);R['formal_invocations']=0 if a.construction else 1;R['reruns']=0;R['replacements']=0;R['tuning']=0
    if not all(R['corruption_controls'].values()):R['decision']='FAIL_INTEGRITY'
    if a.construction and R['decision'].startswith('PASS_'):R['decision']='CONSTRUCTION_PASS'
    raw=json.dumps(R,sort_keys=True,separators=(',',':')).encode();R['digest']=hashlib.sha256(raw).hexdigest();o.write_text(json.dumps(R,indent=2,sort_keys=True)+'\n');print(json.dumps(R,indent=2,sort_keys=True))
if __name__=='__main__':main()
