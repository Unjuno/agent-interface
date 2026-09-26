#!/usr/bin/env python3
"""Raw-only audit: stdlib only, imports no runner/bridge/Xlib."""
import argparse, hashlib, json, pathlib

def delta_effect(a,b): return b.get('button_presses',-999)-a.get('button_presses',-999)
def audit(raw, expected_mode='formal', expected_sessions=4):
    errors=[]; rows=raw.get('sessions')
    if raw.get('mode')!=expected_mode: errors.append('mode')
    if not isinstance(rows,list) or len(rows)!=expected_sessions: errors.append('sessions') ; rows=rows if isinstance(rows,list) else []
    for i,r in enumerate(rows):
        p=f's{i}:'
        if r.get('status')!='COMPLETE': errors.append(p+'complete'); continue
        w1,w2=r.get('w1',{}),r.get('w2',{})
        if w1.get('xid')!=w2.get('xid'): errors.append(p+'xid')
        if w1.get('snapshot')!=w2.get('snapshot'): errors.append(p+'holder_pixels')
        de=r.get('destroy_event') or {}
        if de.get('type')!=17 or de.get('window')!=w1.get('xid'): errors.append(p+'destroy')
        inv=r.get('invalidation',{})
        if inv.get('review_required') is not True: errors.append(p+'invalidated')
        pre=r.get('stale_pre_review',{}); pr=pre.get('result',{})
        if not (pr.get('status')=='refused' and pr.get('error')=='WINDOW_REVIEW_REQUIRED' and pr.get('input_dispatched') is False): errors.append(p+'pre_refusal')
        if pre.get('emissions_before')!=pre.get('emissions_after') or delta_effect(pre.get('effect_before',{}),pre.get('effect_after',{}))!=0: errors.append(p+'pre_effect')
        rev=r.get('review',{}); rr=rev.get('receipt',{})
        if rr.get('status')!='reviewed': errors.append(p+review)
        if rev.get('binding_revision')!=rev.get('previous_revision',-99)+1: errors.append(p+'revision')
        if rev.get('scope')==rev.get('previous_scope'): errors.append(p+'scope')
        post=r.get('stale_post_review',{}); po=post.get('result',{})
        if not (po.get('status')=='refused' and po.get('input_dispatched') is False): errors.append(p+'post_refusal')
        if post.get('emissions_before')!=post.get('emissions_after') or delta_effect(post.get('effect_before',{}),post.get('effect_after',{}))!=0: errors.append(p+'post_effect')
        fresh=r.get('fresh',{}); fr=fresh.get('result',{})
        if fr.get('status')!='completed' or fr.get('recovery_required') is not False: errors.append(p+'fresh_status')
        if fresh.get('emissions_after',0)-fresh.get('emissions_before',0)!=3: errors.append(p+'fresh_emissions')
        if delta_effect(fresh.get('effect_before',{}),fresh.get('effect_after',{}))!=1: errors.append(p+'fresh_effect')
        rel=fr.get('execution',{}).get('releases',[])
        if not (isinstance(rel,list) and rel and all(x.get('verified') is True and x.get('keys_down')==[] and x.get('buttons_down')==[] for x in rel if isinstance(x,dict))): errors.append(p+'release')
        tr=r.get('terminal_release',{})
        if not (tr.get('verified') is True and tr.get('keys_down')==[] and tr.get('buttons_down')==[]): errors.append(p+'terminal')
        if r.get('actor_exit')!=0 or r.get('socket_absent') is not True: errors.append(p+'cleanup')
        if r.get('formal_alias_attempts')!=2 or r.get('fresh_attempts')!=1: errors.append(p+'denominator')
        blobs=r.get('source_blobs',{})
        if blobs.get('research/live_control/native_handle_bridge_v1.py')!='aa72a835a60ab9bf9f053c680a1a3d81e49c14d5': errors.append(p+'source')
    return {'decision':(('PASS_DESTROY_REVIEW_COMPOSITION_SCOPED' if expected_mode=='formal' else 'PASS_CONSTRUCTION_RAW_CHECK') if not errors else 'FAIL_AUDIT'),'errors':errors,'sessions':len(rows)}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('raw'); ap.add_argument('--out',required=True); ap.add_argument('--mode',choices=['construction','formal'],default='formal'); ap.add_argument('--sessions',type=int,default=4); a=ap.parse_args()
    raw=json.loads(pathlib.Path(a.raw).read_text()); res=audit(raw,a.mode,a.sessions); pathlib.Path(a.out).write_text(json.dumps(res,indent=2,sort_keys=True)+'\n'); print(json.dumps(res,sort_keys=True)); raise SystemExit(0 if not res['errors'] else 1)
if __name__=='__main__': main()
