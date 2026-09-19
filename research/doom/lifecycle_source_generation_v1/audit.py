"""Independent retained-file audit; never imports candidate gate/session code."""
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
    check(meta['delivery_freshness_ms']==spec['delivery_freshness_ms'],'delivery threshold metadata')
    check(meta['source_progress_freshness_ms']==spec['source_progress_freshness_ms'],'progress threshold metadata')
    check(meta['fault']==spec['fault'],'fault metadata')
    check(all(d['thread_id']==meta['owner_thread_id'] for d in diag),'game owner thread')
    check(len(samples)==len(diag),'sample diagnostic count')
    for r,d in zip(samples,diag):
        p=r['payload'];clocks=[r['scheduled_ns'],r['sample_started_ns'],p['sample_ns'],r['sample_finished_ns']]
        check(all(type(x)is int and x>=0 for x in clocks) and clocks==sorted(clocks),'acquisition bracket')
        check(d['sample']==p and d['started_ns']<=p['sample_ns']<=d['finished_ns'],'diagnostic identity/bracket')
        check(type(d['source_generation']) is int and d['source_generation']>=0,'source generation type')
    finals=[r for r in samples if r.get('direct_final_sample') is True];check(len(finals)==1 and finals[0] is samples[-1],'unique final receipt last')
    accepted=[r for r in events if r.get('event')=='accepted' and r.get('id')=='primary'];check(len(accepted)==1,'primary accepted count');a=accepted[0]
    terms=[r for r in events if r.get('event')=='terminal'];t=next(r for r in terms if r['id']=='primary')
    admissions=[r for r in events if r.get('event')=='input_admission' and r.get('intent_token')==a['intent_token']];check([r['key'] for r in admissions]==['a','d'],'exact primary chord')
    cause=(t.get('interruption') or {}).get('record') or t['release'];empty=cause.get('verified_ns');check(cause.get('verified') is True and cause.get('keys_down')==[] and cause.get('buttons_down')==[],'primary release not empty')
    for term in terms:
        rel=term.get('release') or {};check(rel.get('verified') is True and rel.get('keys_down')==[] and rel.get('buttons_down')==[],'terminal release not empty')
    keymaps=rows(root/'keymap.jsonl');check(bool(keymaps),'missing independent keymap')
    first_end=next((d['finished_ns'] for d in diag if d['sample']['episode_finished'] is True),None)
    late_submit=next(r for r in driver['sent'] if r.get('op')=='submit' and r.get('id')=='late');late_reply=driver['late']
    late_a=[r for r in events if r.get('event')=='accepted' and r.get('id')=='late']
    prior=[d for d in diag if d['finished_ns']<=late_submit['driver_sent_ns']]
    last_delivery=max((d['finished_ns'] for d in prior),default=None)
    delivery_age=None if last_delivery is None else (late_submit['driver_sent_ns']-last_delivery)/1e6
    advances=[];last_gen=-1
    for d in prior:
        if d['source_generation']>last_gen:
            advances.append(d);last_gen=d['source_generation']
    last_advance=advances[-1]['finished_ns'] if advances else None
    progress_age=None if last_advance is None else (late_submit['driver_sent_ns']-last_advance)/1e6
    false_after=[d for d in diag if d['lifecycle_delivery']=='false_running_after_terminal']
    terminal_del=[d for d in diag if d['lifecycle_delivery']=='terminal']
    expected=spec['expected'];check(t['status']==expected['primary_status'],'primary status');check(bool(late_a) is expected['late_admitted'],'late admission')
    if expected.get('late_reason_contains'):check(late_reply.get('event')=='rejected' and expected['late_reason_contains'] in late_reply.get('reason',''),'late rejection reason')
    if spec['fault']=='false_running_after_terminal':
        check(first_end is not None,'actual terminal missing');check(bool(false_after),'false-running receipt missing')
        check(not terminal_del,'real terminal unexpectedly delivered')
        check(delivery_age is not None and delivery_age <= spec['delivery_freshness_ms'],'false-running delivery not fresh at late submit')
        check(progress_age is not None and progress_age > 300,'source generation unexpectedly fresh after terminal')
        check(t['status']=='expired','silence/stall cancelled active input')
    if spec['timeout_seconds']==60:
        check(first_end is None,'running control ended');check(progress_age is not None and progress_age <= spec['source_progress_freshness_ms'],'running source progress stale')
    if spec['fault']=='none' and spec['timeout_seconds']==40:
        check(bool(terminal_del),'terminal delivery missing');check(t['status']=='cancelled','normal terminal did not cancel primary')
    score=load(root/'score.json');last=diag[-1];mismatch=[k for k in ('map_exit','episode_finished','player_dead','death_count','kill_count') if type(score[k]) is not type(last['sample'][k]) or score[k]!=last['sample'][k]]
    return dict(schema='lifecycle-source-generation-case-v1',spec=spec,integrity_pass=not errors,failures=errors,
      primary_status=t['status'],release_reason=cause.get('reason'),release_verified=cause.get('verified'),
      first_end_observed_ns=first_end,owner_empty_ns=empty,end_to_empty_ms=None if first_end is None else (empty-first_end)/1e6,
      late_admitted=bool(late_a),late_reply=late_reply,late_delivery_age_ms=delivery_age,late_source_progress_age_ms=progress_age,
      last_source_generation=last_gen,false_running_receipt_count=len(false_after),terminal_delivery_count=len(terminal_del),
      acquisition_count=len(samples),keymap_count=len(keymaps),scorer_missed_periods=load(root/'scorer-summary.json')['scheduler']['missed_sample_periods'],historical_score_mismatch_fields=mismatch)
