import argparse,hashlib,json
from pathlib import Path
GOOD={'MEASURED_SAME_POPULATION','BOUNDED_SAME_POPULATION'};REQ=('p','g','w','reuse_rate','version_maintenance_cost')
EXPECTED={
'o3_relevance_generation':('AUTHORED_CONTROL',None,None,None,None),
'x11_target_revalidation':('AUTHORED_CONTROL','WRONG_MECHANISM',None,None,None),
'adaptive_acquisition_testdouble':('TEST_DOUBLE_MECHANICS',None,None,'TEST_DOUBLE_MECHANICS',None),
'x11_phase_overlap':('AUTHORED_CONTROL','WRONG_MECHANISM','WRONG_MECHANISM',None,None),
'current_evidence_guard_cost':('AUTHORED_CONTROL',None,None,None,'WRONG_MECHANISM'),
'reuse_semantic_theorem':('ANALYTIC_ONLY',None,None,'ANALYTIC_ONLY',None),
'integrated_efficiency_fixed_sequence':('DESCRIPTIVE_FIXED_SEQUENCE','WRONG_MECHANISM',None,'DESCRIPTIVE_FIXED_SEQUENCE',None),
}
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ledger',required=True);ap.add_argument('--result',required=True);ap.add_argument('--freeze',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();o=Path(a.output);assert not o.exists();L=json.loads(Path(a.ledger).read_text());R=json.loads(Path(a.result).read_text());F=json.loads(Path(a.freeze).read_text());by={x['id']:x for x in L['families']}
    role_ok=True
    for fid,vals in EXPECTED.items():
        for k,v in zip(REQ,vals):
            if v is not None and by[fid]['fields'].get(k)!=v:role_ok=False
    cal=[]
    for r in L['families']:
        if r.get('same_job_population') and r.get('commensurate_cost_model') and r.get('representative_population') and all(r['fields'].get(k) in GOOD for k in REQ):cal.append(r['id'])
    blocked=all(any(r['fields'].get(k) not in GOOD for k in REQ) for r in L['families'])
    checks={'decision':R['decision']=='PASS_RETAINED_EVIDENCE_COMPUTE_CALIBRATION_NOT_IDENTIFIABLE_SCOPED','families':len(L['families'])>=7 and R['family_count']==len(L['families']),'roles':role_ok,'calibratable_zero':cal==[] and R['calibratable_families']==[],'all_blocked':blocked,'no_estimate':L['production_estimate'] is None and not R['production_estimate_emitted'],'no_recommendation':L['scheduler_recommendation'] is None and not R['scheduler_recommendation_emitted'],'corruptions':all(R['corruption_controls'].values()),'formal':R['formal_invocations']==1 and R['reruns']==0 and R['replacements']==0 and R['tuning']==0,'source_plan':h('PLAN.md')==F['sha256']['PLAN.md'],'source_map':h('SOURCE_MAP.json')==F['sha256']['SOURCE_MAP.json'],'source_ledger':h('LEDGER.json')==F['sha256']['LEDGER.json'],'source_analyze':h('analyze.py')==F['sha256']['analyze.py'],'source_audit':h('audit.py')==F['sha256']['audit.py']}
    Z={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'result_sha256':h(a.result),'freeze_sha256':h(a.freeze)};o.write_text(json.dumps(Z,indent=2,sort_keys=True)+'\n');print(json.dumps(Z,indent=2,sort_keys=True));raise SystemExit(0 if Z['status']=='PASS' else 1)
if __name__=='__main__':main()
