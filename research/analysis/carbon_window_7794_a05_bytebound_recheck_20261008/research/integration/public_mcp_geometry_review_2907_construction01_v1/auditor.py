"""Offline raw audit for geometry construction01; preserves its HOLD."""
import json,sys
from pathlib import Path
root=Path(sys.argv[1]);errs=[]
def read(p):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception as e:errs.append(f'{p.name}: unreadable {type(e).__name__}');return {}
r=read(root/'result.json');t=r.get('trace',{}); before=t.get('geometry_before',{});after=t.get('geometry_after',{});inspect=t.get('inspect',{});review=t.get('review',{})
stale=t.get('stale_dispatch',{}).get('receipt',{}).get('source',{}).get('raw_report',{});fresh=t.get('fresh_dispatch',{}).get('receipt',{}).get('source',{}).get('raw_report',{});close=t.get('close',{})
if before!=after:errs.append('geometry unexpectedly differs from runner raw')
if inspect.get('status')!='needs_review' or inspect.get('evidence',{}).get('title')!='Tip of the Day':errs.append('focused initial surface differs from expected Calc tip dialog')
if review.get('status')!='needs_review':errs.append('review failure missing from raw result')
if stale.get('error')!='SESSION_BINDING_REVISION_MISMATCH' or stale.get('input_dispatched') is not False:errs.append('stale dispatch did not fail before input')
if fresh.get('error')!='SESSION_BINDING_REVISION_MISMATCH' or fresh.get('input_dispatched') is not False:errs.append('fresh dispatch incorrectly proceeded after failed review')
if close.get('status')!='closed' or close.get('release_attempted') is not False:errs.append('no-dispatch close mismatch')
decision='FAIL_RAW_AUDIT' if errs else 'HOLD_GEOMETRY_UNCHANGED_FOCUS_DIALOG'
print(json.dumps({'schema':'agent-interface/2907-geometry-review-audit-v1','decision':decision,'errors':errs,'before':before,'after':after,'inspect_status':inspect.get('status'),'inspect_title':inspect.get('evidence',{}).get('title'),'review_status':review.get('status'),'stale_error':stale.get('error'),'fresh_error':fresh.get('error'),'close':close.get('status'),'scope':'geometry setup did not change the maximized Calc root; focused Tip of the Day modal; no input'},sort_keys=True,indent=2));raise SystemExit(2 if errs else 0)
