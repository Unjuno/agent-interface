import argparse, json, hashlib
from fractions import Fraction
from pathlib import Path
EXPECTED=[
 'cached_reuse_current','cached_reuse_at_deadline','cached_expired','cached_mismatch','cached_mismatch_attractive','cached_mismatch_expired',
 'active_run_low_p','active_wait_high_p','active_tie_shared','active_tie_zero','active_stale_attractive','active_tardy_attractive',
 'active_capture_invalidation','active_compute_invalidation','active_partial_cancel','active_deadline_cross','rebuild_measure_then_active','rebuild_no_implicit_run'
]

def oracle(d):
    if d['object']=='CACHED_COMPLETE':
        if tuple(d['source_versions'])!=tuple(d['current_versions']): return 'REBUILD_REQUIRED'
        if int(d['t_ns'])>int(d['deadline_ns']): return 'DROP_EXPIRED'
        return 'REUSE'
    if tuple(d['source_versions'])!=tuple(d['current_versions']): return 'CANCEL_STALE'
    if int(d['t_ns'])+int(d['remaining_cost_ns'])>int(d['deadline_ns']): return 'CANCEL_TARDY'
    p=Fraction(int(d['p_num']),int(d['p_den'])); run=p*int(d['w_ns']); wait=(1-p)*int(d['g_ns'])
    return 'RUN' if run<wait else ('WAIT' if run>wait else 'TIE')

def audit(root):
    root=Path(root); errors=[]; seen=[]; decision_count=0; published_bad=0; partial_bad=0
    for b in [0,1]:
        br=root/f'batch-{b}'/'batch_receipt.json'
        if not br.exists(): errors.append(f'missing_batch_receipt:{b}'); continue
        rr=json.loads(br.read_text());
        if not rr.get('complete'): errors.append(f'batch_incomplete:{b}')
        for row in rr.get('rows',[]):
            if row.get('returncode')!=0: errors.append(f'case_exit:{row.get("case")}:{row.get("returncode")}')
    files=sorted(root.glob('batch-*/*/result.json'))
    for f in files:
        r=json.loads(f.read_text()); name=r['case']; seen.append(name)
        for d in r['decisions']:
            decision_count+=1; exp=oracle(d)
            if d['disposition']!=exp: errors.append(f'decision:{name}:{d["stage"]}:{d["disposition"]}!={exp}')
        later=r['decisions'][1:]
        if r.get('published_reusable') and any(d['disposition'] in ('CANCEL_STALE','CANCEL_TARDY') for d in later): published_bad+=1; errors.append(f'published_after_cancel:{name}')
        if name=='active_partial_cancel' and not r.get('partial_result'): partial_bad+=1; errors.append('partial_missing')
        if name.startswith('rebuild_'):
            if r['decisions'][0]['disposition']!='REBUILD_REQUIRED': errors.append(f'rebuild_initial:{name}')
            if name=='rebuild_measure_then_active' and len(r['decisions'])<2: errors.append('rebuild_measure_missing_new_job')
    if seen!=EXPECTED: errors.append('case_order_or_denominator')
    return {'decision':'PASS_RAW_AUDIT' if not errors else 'FAIL_RAW_AUDIT','errors':errors,'cases':len(seen),'decisions':decision_count,'published_after_cancel':published_bad,'partial_missing':partial_bad}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--out'); a=ap.parse_args(); r=audit(a.root); s=json.dumps(r,sort_keys=True,indent=2)+'\n'
    if a.out: Path(a.out).write_text(s)
    print(s,end=''); raise SystemExit(0 if not r['errors'] else 1)
if __name__=='__main__': main()
