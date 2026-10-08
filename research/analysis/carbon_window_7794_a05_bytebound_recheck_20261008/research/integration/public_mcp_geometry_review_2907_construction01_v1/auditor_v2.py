"""Independent read-only audit of geometry construction01/02 raw traces."""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]);errs=[]
def read(p):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception as e:errs.append(f'{p}: unreadable {type(e).__name__}');return {}
r1=read(root/'construction01/result.json');t1=r1.get('trace',{});r2=read(root/'construction02/result.json');t2=read(root/'construction02/trace.json')
g0=t1.get('geometry_before',{});g1=t1.get('geometry_after',{});ins=t1.get('inspect',{});rev=t1.get('review',{})
def raw_dispatch(row):return row.get('receipt',{}).get('source',{}).get('raw_report',{})
stale=raw_dispatch(t1.get('stale_dispatch',{}));fresh=raw_dispatch(t1.get('fresh_dispatch',{}))
if g0!=g1 or g0.get('WIDTH')!=1600 or g0.get('HEIGHT')!=981:errs.append('construction01 geometry source rows inconsistent')
title=ins.get('evidence',{}).get('title','')
if ins.get('status')!='needs_review' or not title.startswith('Tip of the Day'):errs.append('construction01 focused modal evidence inconsistent')
if rev.get('status')!='needs_review':errs.append('construction01 failed review not retained')
for name,row in [('stale',stale),('fresh',fresh)]:
 if row.get('error')!='SESSION_BINDING_REVISION_MISMATCH' or row.get('input_dispatched') is not False:errs.append(f'construction01 {name} dispatch did not fail closed')
if t1.get('close',{}).get('release_attempted') is not False:errs.append('construction01 close release unexpected')
obs=t2.get('observe_before',{}).get('observation',{})
if obs.get('status')!='observation_failed' or 'BadDrawable' not in obs.get('error',''):errs.append('construction02 BadDrawable stop not evidenced')
if t2.get('calls') or t2.get('close',{}).get('release_attempted') is not False:errs.append('construction02 continued beyond precondition stop')
if r2.get('error')!="KeyError('stale_dispatch')":errs.append('construction02 wrapper failure history mismatch')
print(json.dumps({'schema':'agent-interface/2907-geometry-review-audit-v2','decision':'FAIL_RAW_AUDIT' if errs else 'HOLD_SETUP_NOT_ESTABLISHED','errors':errs,'formal_allocation':False,'construction01':{'geometry_before':g0,'geometry_after':g1,'inspect_title':title,'review_status':rev.get('status'),'dispatch_errors':[stale.get('error'),fresh.get('error')],'input_dispatched':[stale.get('input_dispatched'),fresh.get('input_dispatched')]},'construction02':{'observation_status':obs.get('status'),'observation_error':obs.get('error'),'trace_decision':t2.get('decision'),'wrapper_error':r2.get('error'),'calls':len(t2.get('calls',[]))},'scope':'geometry transition not established; no input dispatch'},sort_keys=True,indent=2));raise SystemExit(2 if errs else 0)
