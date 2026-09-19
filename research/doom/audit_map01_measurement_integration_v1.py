"""Fail-closed audit for MAP01 v13 direct-release + isolated scorer integration."""
from __future__ import annotations
import argparse,hashlib,json,statistics
from collections import Counter
from pathlib import Path
from analyze_map01_direct_retained_input_v1 import analyze as analyze_retained_input
REQUIRED_SOURCES={'doom/session_map01_v12.py','doom/session_map01_v13.py','doom/map01_scorer_stdio_adapter_v1.py','doom/main_thread_scorer_polling_v1.py','doom/independent_progress_clock_v2.py','doom/doom_retained_input_backend_v3.py','live_control/input_transition_owner_v3.py'}
EXPECTED_SAMPLE_FIELDS={'schema','sample_ns','kill_count','death_count','episode_finished','player_dead','map_exit'}
def rows(path):
    p=Path(path);return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()] if p.exists() else []
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def _scorer_schema(row):return isinstance(row.get('schema'),str) and row['schema'].startswith('independent-progress-')
def audit(root,research_root=None):
    root=Path(root);research_root=Path(research_root) if research_root else Path(__file__).resolve().parent.parent
    events=rows(root/'events.jsonl');delivered=rows(root/'delivered.jsonl');samples=rows(root/'scorer-samples.jsonl');score_events=rows(root/'scorer-events.jsonl')
    if events!=delivered:fail=['controller event/delivery streams diverge']
    else:fail=[]
    sources=json.loads((root/'sources.json').read_text(encoding='utf-8')) if (root/'sources.json').exists() else {}
    leak=[r for r in events+delivered if _scorer_schema(r)]
    if leak:fail.append(f'controller scorer leak count={len(leak)}')
    missing=sorted(REQUIRED_SOURCES-set(sources))
    if missing:fail.append('missing sources: '+','.join(missing))
    bad=[]
    for name,digest in sources.items():
        p=research_root/name
        if not p.exists() or sha(p)!=digest:bad.append(name)
    if bad:fail.append('source hash mismatch: '+','.join(sorted(bad)))
    direct=analyze_retained_input(events)
    if direct.get('measurement_ready') is not True:fail.append('direct retained-input analyzer not measurement-ready')
    active=None;completed=[];interrupted=[]
    for r in events:
        e=r.get('event')
        if e=='step_started' and r.get('operation')=='hold':
            if active is not None:fail.append('overlapping hold')
            active={'id':r['id'],'step':r['step'],'admissions':[],'transitions':[]}
        elif active is not None and e=='input_admission':active['admissions'].append(r)
        elif active is not None and e=='input_release_transition' and r.get('release_batch_identifier')==active['id'] and r.get('release_batch_step')==active['step']:active['transitions'].append(r)
        elif active is not None and e=='step_completed' and (r.get('id'),r.get('step'))==(active['id'],active['step']):completed.append(active);active=None
        elif active is not None and e=='terminal' and r.get('id')==active['id']:interrupted.append(active);active=None
    if active is not None:fail.append('unterminated hold')
    if not completed:fail.append('no completed hold measured')
    windows=[]
    for h in completed:
        admissions=h['admissions'];transitions=h['transitions'];n=len(admissions)
        if not n:fail.append(f"no admissions {h['id']}:{h['step']}");continue
        if len(transitions)!=n:fail.append(f"release transition count {h['id']}:{h['step']}={len(transitions)} admissions={n}");continue
        expected=Counter((x.get('intent_token'),x.get('key')) for x in admissions);actual=Counter((x.get('intent_token'),x.get('key')) for x in transitions)
        if expected!=actual:fail.append(f"release transition keys mismatch {h['id']}:{h['step']}")
        positions=sorted(x.get('release_batch_position') for x in transitions if type(x.get('release_batch_position')) is int)
        if positions!=list(range(n)) or any(x.get('release_batch_size')!=n for x in transitions):fail.append(f"release batch shape invalid {h['id']}:{h['step']}")
        if any(x.get('release_batch_schema')!='input-release-batch-v3' for x in transitions):fail.append(f"release batch schema invalid {h['id']}:{h['step']}")
        if any(x.get('owner_transition_verified') is not True for x in transitions):fail.append(f"unverified transition {h['id']}:{h['step']}")
        if any(x.get('owned_keycodes_after_batch')!=[] for x in transitions):fail.append(f"owner nonempty after batch {h['id']}:{h['step']}")
        if any(x.get('ordinary_release_candidate') is not True for x in transitions):fail.append(f"nonordinary transition {h['id']}:{h['step']}")
        starts=[x.get('release_call_started_ns') for x in transitions];returns=[x.get('release_call_returned_ns') for x in transitions]
        if all(type(x) is int for x in starts+returns):windows.append(max(returns)-min(starts))
    terminals=[r for r in events if r.get('event')=='terminal']
    for t in terminals:
        rel=t.get('release') or {}
        if rel.get('verified') is not True or rel.get('keys_down')!=[] or rel.get('buttons_down',[])!=[]:fail.append('terminal release not empty '+str(t.get('id')))
    if len(samples)<4:fail.append('fewer than four scorer samples')
    sns=[]
    for r in samples:
        if r.get('controller_visible') is not False:fail.append('sample visibility invalid');break
        payload=r.get('payload') or {}
        if set(payload)!=EXPECTED_SAMPLE_FIELDS or payload.get('schema')!='independent-progress-sample-v2':fail.append('sample schema/fields invalid');break
        sns.append(payload.get('sample_ns'))
    if any(type(x) is not int for x in sns) or sns!=sorted(sns):fail.append('scorer sample clock invalid')
    sample_set=set(sns)
    for e in score_events:
        if e.get('schema')!='independent-progress-event-v2' or e.get('controller_visible') is not False:fail.append('scorer event isolation invalid');break
        if e.get('observed_ns') not in sample_set:fail.append('scorer event not bound to sample');break
    summary_path=root/'scorer-summary.json';summary=json.loads(summary_path.read_text(encoding='utf-8')) if summary_path.exists() else None
    if not isinstance(summary,dict) or summary.get('controller_visible') is not False:fail.append('scorer summary missing/visible')
    elif (summary.get('scheduler') or {}).get('missed_sample_periods')!=0:fail.append('scorer scheduler missed sample periods')
    result={'schema':'map01-measurement-integration-audit-v3','pass':not fail,'failures':fail,'controller_scorer_leak_count':len(leak),'completed_hold_count':len(completed),'interrupted_hold_count':len(interrupted),'direct_retained_input':direct,'release_transition_count':sum(len(h['transitions']) for h in completed),'release_batch_window_us':({'min':min(windows)/1e3,'median':statistics.median(windows)/1e3,'max':max(windows)/1e3} if windows else None),'scorer_sample_count':len(samples),'scorer_event_count':len(score_events),'positive_useful_event_count':sum(e.get('useful') is True for e in score_events),'zero_positive_events_allowed':True,'decision':'PASS measurement integration' if not fail else 'FAIL measurement integration'}
    return result
def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--research-root',type=Path);ap.add_argument('--out',type=Path);a=ap.parse_args();r=audit(a.root,a.research_root);text=json.dumps(r,indent=2,sort_keys=True)+'\n';print(text,end='')
    if a.out:a.out.write_text(text,encoding='utf-8')
    raise SystemExit(0 if r['pass'] else 1)
if __name__=='__main__':main()
