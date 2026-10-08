import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SCHEDULE=json.loads((ROOT/'schedule.json').read_text())
RESULT=json.loads((ROOT/'FORMAL_RESULT.json').read_text())

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(result):
    errs=[]
    if result.get('formal_invocations')!=1 or result.get('reruns')!=0:errs.append('formal_count')
    rows=result.get('rows',[])
    if len(rows)!=20:errs.append('row_count')
    by={x.get('case_id'):x for x in rows}
    for spec in SCHEDULE['rows']:
        r=by.get(spec['case_id'])
        if r is None:errs.append(spec['case_id']+':missing');continue
        expg=4 if spec['replace'] or spec['capacity']==1 else 2
        expr=2 if (not spec['replace'] and spec['capacity']==2) else 0
        if r.get('capacity')!=spec['capacity'] or bool(r.get('replace'))!=bool(spec['replace']):errs.append(spec['case_id']+':condition')
        if r.get('groundings')!=expg:errs.append(spec['case_id']+':ground')
        if r.get('reuses')!=expr:errs.append(spec['case_id']+':reuse')
        if r.get('clicks')!=spec['sequence']:errs.append(spec['case_id']+':clicks')
        if r.get('terminal_button_neutral') is not True:errs.append(spec['case_id']+':button')
        ss=r.get('step_surfaces',[])
        if spec['replace']:
            if r.get('old_probe_count',0)<1:errs.append(spec['case_id']+':probe_count')
            if any(x!='SCOPE_MISMATCH' for x in r.get('old_probe_statuses',[])):errs.append(spec['case_id']+':probe_status')
            if len(ss)!=4 or not (ss[0]==ss[1] and ss[2]==ss[3] and ss[0]!=ss[2]):errs.append(spec['case_id']+':surface')
        else:
            if r.get('old_probe_count')!=0:errs.append(spec['case_id']+':stable_probe')
            if len(set(ss))!=1:errs.append(spec['case_id']+':stable_surface')
        case_dir=ROOT/'cases'/spec['case_id']
        raw=json.loads((case_dir/'result.json').read_text())
        ledger=[json.loads(x) for x in (case_dir/'fixture.jsonl').read_text().splitlines() if x.strip()]
        clicks=[x['target'] for x in ledger if x.get('event')=='click']
        if clicks!=spec['sequence']:errs.append(spec['case_id']+':raw_ledger')
        if raw['groundings']!=r['groundings'] or raw['reuses']!=r['reuses']:errs.append(spec['case_id']+':raw_counts')
        ch=result.get('case_hashes',{}).get(spec['case_id'],{})
        if ch.get('result_sha256')!=sha(case_dir/'result.json') or ch.get('fixture_sha256')!=sha(case_dir/'fixture.jsonl'):errs.append(spec['case_id']+':hash')
        if spec['replace']:
            # Independent currentness check from raw receipts: every old probe has distinct XIDs and is ineligible scope mismatch.
            if any(p.get('old_surface')==p.get('new_surface') or p.get('eligible') or p.get('status')!='SCOPE_MISMATCH' for p in raw.get('old_probes',[])):errs.append(spec['case_id']+':raw_old_probe')
            surfaces=[x for x in ledger if x.get('event')=='surface']
            if len(surfaces)!=2 or surfaces[0]['surface_xid']==surfaces[1]['surface_xid']:errs.append(spec['case_id']+':fixture_surface')
    cells=result.get('cells',{})
    expected={'k1_stable':[4]*5,'k2_stable':[2]*5,'k1_replace':[4]*5,'k2_replace':[4]*5}
    for key,gs in expected.items():
        if cells.get(key,{}).get('groundings')!=gs:errs.append('cell:'+key)
    if result.get('decision')!='PASS_TARGET_HANDLE_CAPACITY_X11_SCOPED' or result.get('pass') is not True:errs.append('decision')
    return errs

base_errors=validate(RESULT)
corruptions=[]
for name,mut in [
 ('grounding',lambda r:r['rows'][0].__setitem__('groundings',99)),
 ('click',lambda r:r['rows'][1].__setitem__('clicks',['A','B','B','B'])),
 ('probe',lambda r:r['rows'][2].__setitem__('old_probe_statuses',['VALID'])),
 ('button',lambda r:r['rows'][3].__setitem__('terminal_button_neutral',False)),
]:
    c=copy.deepcopy(RESULT);mut(c);corruptions.append({'name':name,'rejected':bool(validate(c))})
out={'task':RESULT.get('task'),'errors':base_errors,'corruption_controls':corruptions,'pass':not base_errors and all(x['rejected'] for x in corruptions)}
(ROOT/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True));sys.exit(0 if out['pass'] else 1)
