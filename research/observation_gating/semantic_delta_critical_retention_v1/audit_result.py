#!/usr/bin/env python3
import argparse,json,pathlib,sys,hashlib

def load(p): return json.loads(pathlib.Path(p).read_text())
def sha(b): return hashlib.sha256(b).hexdigest()
def audit(f,r):
    errs=[]
    if r.get('formal_invocations')!=1: errs.append('formal_invocations')
    if r.get('formal_reruns')!=0: errs.append('formal_reruns')
    if r.get('source_blobs')!=f.get('source_blobs'): errs.append('source_blobs')
    rows=r.get('rows',[])
    if len(rows)!=16: errs.append('row_count')
    by={(x.get('case'),x.get('representation')):x for x in rows}
    wf_e=by.get(('calc-workflow-excursion','EVENT_AWARE_SEMANTIC_DELTA'),{}); wf_p=by.get(('calc-workflow-excursion','ENDPOINT_STATE_DELTA'),{})
    if wf_e.get('excursion_retained') is not True or wf_e.get('critical_count_ok') is not True: errs.append('calc_excursion')
    if wf_p.get('endpoint_alias_observed') is not True: errs.append('endpoint_discriminator')
    for case in f['cases']:
        e=by.get((case['id'],'EVENT_AWARE_SEMANTIC_DELTA')); p=by.get((case['id'],'ENDPOINT_STATE_DELTA'))
        if e is None or p is None: errs.append('missing:'+case['id']); continue
        if case.get('expected_critical_event_count') is not None and e.get('critical_count_ok') is not True: errs.append('critical_count:'+case['id'])
        if case.get('expected_unknown') and (e.get('unknown_ok') is not True or p.get('unknown_ok') is not True): errs.append('unknown:'+case['id'])
        if e['output'].get('authority')!='none' or p['output'].get('authority')!='none': errs.append('authority:'+case['id'])
    if not all(x.get('pass') for x in r.get('negative_controls',[])): errs.append('negative_controls')
    gates=r.get('gates',{})
    if not gates or not all(gates.values()): errs.append('gates')
    if not errs and r.get('decision')!='PASS_SEMANTIC_DELTA_CRITICAL_RETENTION_SCOPED': errs.append('decision')
    canonical=json.dumps(r,indent=2,sort_keys=True)+'\n'
    return {'audit':'PASS' if not errs else 'FAIL','errors':errs,'decision':r.get('decision'),'result_sha256':sha(canonical.encode())}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('fixture'); ap.add_argument('result'); ap.add_argument('--output'); a=ap.parse_args(); o=audit(load(a.fixture),load(a.result)); text=json.dumps(o,indent=2,sort_keys=True)+'\n'
    if a.output: pathlib.Path(a.output).write_text(text,encoding='utf-8',newline='\n')
    else: print(text,end='')
    raise SystemExit(0 if o['audit']=='PASS' else 1)
if __name__=='__main__': main()
