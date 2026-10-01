#!/usr/bin/env python3
import argparse, base64, hashlib, json, pathlib
SKEW_NS=2_000_000
SCHEDULES=('STABLE','DELAYED_RENDER','FOCUS_CHANGE','WINDOW_REPLACEMENT','IDENTITY_MISMATCH','EFFECT_TRANSITION')
POLICIES=('BOUNDED_SKEW','STRICT_ANCHOR')
TASK={'STABLE','DELAYED_RENDER','EFFECT_TRANSITION'}

def candidate_independent(r):
    f=r['fields']; keys=('focus','target_binding','image','ui_context')
    ids=[(f[k]['session'],f[k]['surface'],f[k]['generation']) for k in keys]
    if len(set(ids)) != 1: return False
    ts=[f[k]['sample_ns'] for k in keys]
    if any(type(x) is not int for x in ts): return False
    anchor=max(ts)
    if anchor > r['now_ns']: return False
    if f['focus']['valid_through_ns'] < anchor or f['target_binding']['valid_through_ns'] < anchor: return False
    if anchor-f['image']['sample_ns'] > SKEW_NS or anchor-f['ui_context']['sample_ns'] > SKEW_NS: return False
    return True

def strict_independent(r):
    if not candidate_independent(r): return False
    f=r['fields']; return len({f[k]['sample_ns'] for k in ('focus','target_binding','image','ui_context')})==1

def oracle_independent(r):
    f=r['fields']; raw=r['raw']; keys=('focus','target_binding','image','ui_context')
    ids=[(f[k]['session'],f[k]['surface'],f[k]['generation']) for k in keys]
    anchor=max(f[k]['sample_ns'] for k in keys)
    noncritical=(anchor-f['image']['sample_ns']<=SKEW_NS and anchor-f['ui_context']['sample_ns']<=SKEW_NS)
    current=(raw['initial_focus']==raw['final_focus'] and raw['initial_geometry']==raw['final_geometry'])
    same_process=(type(raw['app_pid_initial']) is int and type(raw['app_pid_current']) is int and raw['app_pid_initial']==raw['app_pid_current'])
    return len(set(ids))==1 and current and noncritical and same_process

def audit_rows(rows, expected_reps=1):
    errors=[]; expected=expected_reps*len(SCHEDULES)*len(POLICIES)
    if len(rows)!=expected: errors.append(f'row_count:{len(rows)}!={expected}')
    expected_ids={f'r{rep}-{p}-{s}' for rep in range(expected_reps) for s in SCHEDULES for p in POLICIES}
    ids=[r.get('case_id') for r in rows]
    if set(ids)!=expected_ids or len(ids)!=len(set(ids)): errors.append('case_id_set')
    counter=[]
    for r in rows:
        cid=r.get('case_id','?'); p=r.get('policy'); s=r.get('schedule'); raw=r.get('raw',{}); f=r.get('fields',{})
        if p not in POLICIES or s not in SCHEDULES: errors.append('schedule_policy:'+cid); continue
        try: c=candidate_independent(r); st=strict_independent(r); o=oracle_independent(r)
        except Exception as e: errors.append('reconstruct:'+cid+':'+type(e).__name__); continue
        exp_join=c if p=='BOUNDED_SKEW' else st
        if r.get('join') is not exp_join: errors.append('join_reconstruct:'+cid)
        if r.get('oracle_join') is not o: errors.append('oracle_reconstruct:'+cid)
        img=f.get('image',{})
        try: b=base64.b64decode(img['b64'],validate=True)
        except Exception: errors.append('image_b64:'+cid); b=b''
        if len(b)!=img.get('bytes') or hashlib.sha256(b).hexdigest()!=img.get('sha256'): errors.append('image_identity:'+cid)
        rel=r.get('release',{})
        if rel.get('keys_down_after')!=[] or rel.get('pointer_mask_after')!=0: errors.append('release:'+cid)
        if r.get('socket_removed') is not True or r.get('process_exits',{}).get('xvfb')!=0: errors.append('cleanup:'+cid)
        score=r.get('effect_score',{}).get('status')
        if p=='BOUNDED_SKEW' and s in TASK and c:
            if score!='EXACT': errors.append('expected_effect:'+cid)
        else:
            if score!='ABSENT': errors.append('unexpected_effect:'+cid)
        if s=='FOCUS_CHANGE' and c: errors.append('focus_join:'+cid)
        if s=='IDENTITY_MISMATCH' and c: errors.append('identity_join:'+cid)
        if s=='WINDOW_REPLACEMENT':
            if raw.get('app_pid_initial')==raw.get('app_pid_current'): errors.append('replacement_pid_not_changed:'+cid)
            if raw.get('xid_initial')!=raw.get('xid_current'): errors.append('replacement_xid_not_reused:'+cid)
            if raw.get('initial_geometry')!=raw.get('final_geometry'): errors.append('replacement_geometry_changed:'+cid)
            if p=='BOUNDED_SKEW':
                if c is True and o is False and r.get('join') is True: counter.append(cid)
                else: errors.append('missing_replacement_counterexample:'+cid)
    if len(counter)!=expected_reps: errors.append(f'counterexample_count:{len(counter)}!={expected_reps}')
    return {'integrity':'PASS' if not errors else 'FAIL','scientific_disposition':'HOLD_LIVE_TRANSFER_UNSAFE_REPLACEMENT_ALIAS' if not errors else 'HOLD_EVIDENCE_INTEGRITY','rows':len(rows),'errors':errors,'replacement_counterexamples':counter}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('rows'); ap.add_argument('--reps',type=int,default=1); ap.add_argument('--out'); a=ap.parse_args()
    rows=json.loads(pathlib.Path(a.rows).read_text()); r=audit_rows(rows,a.reps); txt=json.dumps(r,indent=2,sort_keys=True)+'\n'
    if a.out: pathlib.Path(a.out).write_text(txt)
    print(txt,end=''); raise SystemExit(0 if not r['errors'] else 1)
if __name__=='__main__': main()
