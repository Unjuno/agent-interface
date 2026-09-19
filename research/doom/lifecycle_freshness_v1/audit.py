"""Independent retained-file audit; does not import lifecycle candidate code."""
from __future__ import annotations
import hashlib,json
from pathlib import Path

def load(p):return json.loads(Path(p).read_text())
def rows(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def analyze(out,runtime,source):
    out,runtime,source=map(Path,(out,runtime,source));root=out/'runtime';errors=[]
    def check(ok,msg):
        if not ok:errors.append(msg)
    events=rows(root/'events.jsonl');samples=rows(root/'scorer-samples.jsonl');diag=rows(root/'acquisitions.jsonl')
    launch=load(out/'launch.json');spec=launch['spec'];driver=load(out/'driver.json');meta=load(root/'candidate-sources.json')
    check((root/'events.jsonl').read_bytes()==(root/'delivered.jsonl').read_bytes(),'controller delivery mismatch')
    check(load(out/'exit.json')['returncode']==0,'session failed')
    for n,h in load(root/'sources.json').items():check(sha(runtime/'research'/n)==h,'runtime source '+n)
    for n,h in launch['sources'].items():check(sha(source/n)==h,'experiment source '+n)
    for n,h in meta['sources'].items():check(launch['sources'].get(n)==h,'loaded experiment source '+n)
    check(meta['freshness_ms']==spec['freshness_ms'] and meta['fault']==spec['fault'],'candidate metadata')
    check(all(d['thread_id']==meta['owner_thread_id'] for d in diag),'game owner thread')
    check(len(samples)==len(diag),'sample diagnostic count')
    for r,d in zip(samples,diag):
        p=r['payload'];clocks=[r['scheduled_ns'],r['sample_started_ns'],p['sample_ns'],r['sample_finished_ns']]
        check(all(type(x)is int and x>=0 for x in clocks) and clocks==sorted(clocks),'acquisition bracket')
        check(d['sample']==p and d['started_ns']<=p['sample_ns']<=d['finished_ns'],'diagnostic identity/bracket')
    finals=[r for r in samples if r.get('direct_final_sample') is True]
    check(len(finals)==1 and finals[0] is samples[-1],'unique final receipt last')
    accepted=[r for r in events if r.get('event')=='accepted' and r.get('id')=='primary'];check(len(accepted)==1,'primary accepted count')
    a=accepted[0];terms=[r for r in events if r.get('event')=='terminal'];t=next(r for r in terms if r['id']=='primary')
    admissions=[r for r in events if r.get('event')=='input_admission' and r.get('intent_token')==a['intent_token']]
    check([r['key'] for r in admissions]==['a','d'],'exact primary chord')
    cause=(t.get('interruption') or {}).get('record') or t['release'];empty=cause.get('verified_ns')
    check(cause.get('verified') is True and cause.get('keys_down')==[] and cause.get('buttons_down')==[],'primary release not empty')
    for term in terms:
        rel=term.get('release') or {};check(rel.get('verified') is True and rel.get('keys_down')==[] and rel.get('buttons_down')==[],'terminal release not empty')
    checks=rows(root/'keymap.jsonl');check(bool(checks),'missing independent keymap')
    first_end=next((d['finished_ns'] for d in diag if d['sample']['episode_finished'] is True),None)
    delivered=[d for d in diag if d.get('lifecycle_delivery') in ('terminal','terminal_delayed')]
    terminal_delivery_ns=None
    if delivered:
        terminal_delivery_ns=next((d.get('lifecycle_delivered_ns') for d in delivered if type(d.get('lifecycle_delivered_ns')) is int),None)
    late_a=[r for r in events if r.get('event')=='accepted' and r.get('id')=='late']
    late_reply=driver['late'];late_submit=next(r for r in driver['sent'] if r.get('op')=='submit' and r.get('id')=='late')
    running_deliveries=[d for d in diag if d.get('lifecycle_delivery')=='running' and d['finished_ns']<=late_submit['driver_sent_ns']]
    last_running=max((d['finished_ns'] for d in running_deliveries),default=None)
    late_evidence_age_ms=None if last_running is None else (late_submit['driver_sent_ns']-last_running)/1e6
    expected=spec['expected']
    check(t['status']==expected['primary_status'],'primary status')
    check(bool(late_a) is expected['late_admitted'],'late admission')
    if expected.get('late_reason_contains'):
        check(late_reply.get('event')=='rejected' and expected['late_reason_contains'] in late_reply.get('reason',''),'late rejection reason')
    if expected.get('terminal_delivery'):
        check(any(d.get('lifecycle_delivery')==expected['terminal_delivery'] for d in diag),'terminal delivery mode')
    if spec['fault']=='drop_terminal' and spec['timeout_seconds']==40:
        check(not delivered,'dropped terminal unexpectedly delivered')
    if spec['timeout_seconds']==60:
        check(first_end is None,'running control unexpectedly ended')
    else:
        check(first_end is not None,'timeout end not observed')
    if spec['freshness_ms']>0 and spec['fault']=='drop_terminal':
        check(late_evidence_age_ms is not None and late_evidence_age_ms>spec['freshness_ms'],'late evidence not stale')
    score=load(root/'score.json');last=diag[-1];mismatch=[k for k in ('map_exit','episode_finished','player_dead','death_count','kill_count') if type(score[k]) is not type(last['sample'][k]) or score[k]!=last['sample'][k]]
    return dict(schema='lifecycle-freshness-case-v1',spec=spec,integrity_pass=not errors,failures=errors,
        primary_status=t['status'],release_reason=cause.get('reason'),release_verified=cause.get('verified'),
        first_end_observed_ns=first_end,owner_empty_ns=empty,end_to_empty_ms=None if first_end is None else (empty-first_end)/1e6,
        terminal_delivery_ns=terminal_delivery_ns,delivery_to_empty_ms=None if terminal_delivery_ns is None else (empty-terminal_delivery_ns)/1e6,
        late_admitted=bool(late_a),late_reply=late_reply,last_running_lifecycle_ns=last_running,
        late_evidence_age_ms=late_evidence_age_ms,acquisition_count=len(samples),keymap_count=len(checks),
        scorer_missed_periods=load(root/'scorer-summary.json')['scheduler']['missed_sample_periods'],historical_score_mismatch_fields=mismatch)
