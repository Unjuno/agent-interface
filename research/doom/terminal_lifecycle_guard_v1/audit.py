"""Independent retained-file audit; no engine, Xlib or candidate-gate imports."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path

def load(p):return json.loads(Path(p).read_text())
def rows(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def analyze(out,runtime,source):
    out,runtime,source=map(Path,(out,runtime,source));root=out/'runtime';errors=[]
    def check(ok,msg):
        if not ok:errors.append(msg)
    events=rows(root/'events.jsonl');samples=rows(root/'scorer-samples.jsonl');diag=rows(root/'acquisitions.jsonl')
    launch=load(out/'launch.json');spec=launch['spec'];driver=load(out/'driver.json')
    check((root/'events.jsonl').read_bytes()==(root/'delivered.jsonl').read_bytes(),'controller delivery mismatch')
    check(load(out/'exit.json')['returncode']==0,'session failed')
    for n,h in load(root/'sources.json').items():check(sha(runtime/'research'/n)==h,'runtime source '+n)
    for n,h in launch['sources'].items():check(sha(source/n)==h,'experiment source '+n)
    meta=load(root/'candidate-sources.json')
    check(meta['guard'] is spec['guard'] and meta['final_attempted'] is True,'candidate metadata')
    for n,h in meta['sources'].items():check(launch['sources'].get(n)==h,'loaded experiment source '+n)
    check(all(d['thread_id']==meta['owner_thread_id'] for d in diag),'game owner thread')
    check(len(samples)==len(diag),'sample diagnostic count')
    for r,d in zip(samples,diag):
        p=r['payload']; clocks=[r['scheduled_ns'],r['sample_started_ns'],p['sample_ns'],r['sample_finished_ns']]
        check(all(type(x) is int and x>=0 for x in clocks) and clocks==sorted(clocks),'acquisition bracket')
        check(d['sample']==p and d['started_ns']<=p['sample_ns']<=d['finished_ns'],'diagnostic identity/bracket')
        check(r['controller_visible'] is False,'scorer visibility')
    finals=[r for r in samples if r.get('direct_final_sample') is True]
    check(len(finals)==1 and finals[0] is samples[-1],'unique final receipt last')
    endrows=[d for d in diag if d['sample']['episode_finished'] is True]
    first_end=endrows[0]['finished_ns'] if endrows else None
    last=diag[-1]; p=last['sample']; score=load(root/'score.json')
    check(p['episode_finished'] is (spec['timeout_seconds']==40),'terminal exposure')
    check(last['timeout_reached'] is (spec['timeout_seconds']==40),'timeout exposure')
    check(not p['map_exit'] and not p['player_dead'],'unexpected outcome')
    compared=('map_exit','episode_finished','player_dead','death_count','kill_count')
    mismatch=[k for k in compared if type(p[k]) is not type(score[k]) or p[k]!=score[k]]
    pre=events[:next(i for i,r in enumerate(events) if r.get('event')=='post_control_score')]
    leak=any(any(k in r for k in ('kill_count','death_count','timeout_reached')) or
             str(r.get('schema','')).startswith('independent-progress-') for r in pre)
    check(not leak,'privileged score field delivered before finish')
    accepted=[r for r in events if r.get('event')=='accepted' and r.get('id')=='primary']
    terms=[r for r in events if r.get('event')=='terminal']
    check(len(accepted)==1,'primary accepted count')
    a=accepted[0]; t=next(r for r in terms if r['id']=='primary')
    cmd=next(r for r in driver['sent'] if r.get('op')=='submit' and r['id']=='primary')
    digest=hashlib.sha256(json.dumps(cmd['steps'],sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
    check(digest==a['program_sha256'],'accepted action hash')
    check(a['valid_until_ns']==cmd['valid_until_ns'],'owner deadline identity')
    admissions=[r for r in events if r.get('event')=='input_admission' and r.get('intent_token')==a['intent_token']]
    check([r['key'] for r in admissions]==['a','d'],'exact primary chord')
    for term in terms:
        rel=term.get('release') or {};check(rel.get('verified') is True and rel.get('keys_down')==[] and rel.get('buttons_down')==[],'terminal release not empty')
    cause=(t.get('interruption') or {}).get('record') or t['release'];empty=cause.get('verified_ns')
    check(type(empty) is int and cause.get('verified') is True and cause.get('keys_down')==[] and cause.get('buttons_down')==[],'primary cause not verified empty')
    if t.get('interruption'):check(t['interruption'].get('intent_token')==a['intent_token'],'cause intent')
    checks=rows(root/'keymap.jsonl');previous=0
    for r in checks:
        b=r['bitmap'];check(len(b)==32 and all(type(x)is int and 0<=x<=255 for x in b),'X11 bitmap format')
        decoded=[k for k,c in zip(r['keys'],r['keycodes']) if b[c//8] & (1<<(c%8))]
        check(decoded==r['down'],'X11 bitmap decoding')
        check(previous<=r['started_ns']<=r['finished_ns'],'X11 acquisition clocks');previous=r['finished_ns']
    primary_checks=[r for r in checks if a['accepted_ns']<=r['started_ns'] and r['finished_ns']<=t['terminal_ns']]
    held=[r for r in primary_checks if r['down']==['a','d']]
    check(bool(held),'no independently observed primary chord')
    post=[r for r in primary_checks if first_end is not None and r['started_ns']>=first_end and r['down']]
    after=[r for r in checks if empty<=r['started_ns'] and r['finished_ns']<=t['terminal_ns']+100_000_000 and not r['down']]
    check(bool(after),'no independent empty sample after release')
    late_a=[r for r in events if r.get('event')=='accepted' and r.get('id')=='late']
    result=dict(schema='terminal-lifecycle-case-v1',spec=spec,integrity_pass=not errors,failures=errors,
        primary_status=t['status'],primary_admissions=len(admissions),release_reason=cause.get('reason'),
        release_verified=cause.get('verified'),owner_deadline_ns=a['valid_until_ns'],
        primary_accepted_ns=a['accepted_ns'],first_end_observed_ns=first_end,owner_empty_ns=empty,
        observed_end_to_empty_ms=None if first_end is None else (empty-first_end)/1e6,
        deadline_to_empty_ms=(empty-a['valid_until_ns'])/1e6,
        post_end_down_sample_count=len(post),last_down_after_end_ms=None if not post else (post[-1]['started_ns']-first_end)/1e6,
        late_admitted=bool(late_a),late_reply=driver['late'],
        final_cause='TIMEOUT' if last['timeout_reached'] else 'RUNNING',
        historical_score_mismatch_fields=mismatch,historical_false_success=score['map_exit'] and last['timeout_reached'],
        acquisition_count=len(samples),keymap_count=len(checks),
        scorer_missed_periods=load(root/'scorer-summary.json')['scheduler']['missed_sample_periods'],
        prefinish_scorer_leak=leak,strict_full_final_score_equality=not mismatch)
    return result
