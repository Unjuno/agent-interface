"""Offline replay: value correctness, acquisition ordering and source freshness differ."""
from __future__ import annotations
import argparse, hashlib, json, statistics
from pathlib import Path
from acquisition import validate_receipt

FIELDS=('map_exit','episode_finished','player_dead','death_count','kill_count')
def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
def obj(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def stats(xs):
    return {'n':len(xs),'median':statistics.median(xs),'min':min(xs),'max':max(xs)} if xs else None

def analyze(out, runtime=None, candidate=None):
    out=Path(out);rt=out/'runtime';spec=obj(out/'launch.json')['spec'];events=rows(rt/'events.jsonl')
    samples=rows(rt/'scorer-samples.jsonl');diag=rows(rt/'acquisitions.jsonl');summary=obj(rt/'scorer-summary.json')
    score=obj(rt/'score.json');fail=[]
    def check(ok,label):
        if not ok:fail.append(label)
    check((rt/'events.jsonl').read_bytes()==(rt/'delivered.jsonl').read_bytes(),'delivery streams differ')
    accepted=[r for r in events if r.get('event')=='accepted'];terminal=[r for r in events if r.get('event')=='terminal']
    if len(accepted)!=1 or len(terminal)!=1:raise ValueError('expected one accepted/terminal')
    a,t=accepted[0],terminal[0];deadline=a['valid_until_ns']
    check(a['id']==t['id']==spec['id'],'program id')
    program=[{'op':'hold','keys':spec['keys'],'duration_ms':5000}]
    digest=hashlib.sha256(json.dumps(program,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    check(a.get('program_sha256')==digest,'exact program attestation')
    check(t['status']=='expired','expected expiry')
    admissions=[r for r in events if r.get('event')=='input_admission']
    check([r['key'] for r in admissions]==spec['keys'],'exact keys')
    check(all(r['intent_token']==a['intent_token'] for r in admissions),'intent association')
    check(all(r['valid_until_ns']==deadline for r in admissions),'admission deadline')
    cause=(t.get('interruption') or {}).get('record') or {}
    for release in [cause,t.get('release') or {}]:
        check(release.get('verified') is True and release.get('keys_down')==[] and release.get('buttons_down',[])==[],'release empty')
    check(cause.get('reason')=='expired','expiry cause')
    check((t.get('interruption') or {}).get('intent_token')==a['intent_token'],'cause intent')
    check(cause.get('valid_until_ns')==deadline,'cause deadline')
    valid=0
    for s in samples:
        try:validate_receipt(s);valid+=1
        except (ValueError,TypeError,KeyError) as e:fail.append('receipt '+str(e))
        check(s.get('controller_visible') is False,'scorer visibility')
    final=[r for r in samples if r.get('direct_final_sample') is True]
    check(len(final)==1 and final[0] is samples[-1],'unique final last')
    if final:
        check(all(type(score[k]) is type(final[0]['payload'][k]) and score[k]==final[0]['payload'][k] for k in FIELDS),'terminal value agreement')
    check(len(diag)==len(samples),'diagnostic sample bijection')
    prov=obj(rt/'candidate-sources.json')
    for d,s in zip(diag,samples):
        check(d['sample']==s['payload'],'diagnostic payload match')
        check(s['sample_started_ns']<=d['started_ns']<=d['sample']['sample_ns']<=d['finished_ns']<=s['sample_finished_ns'],'nested acquisition')
        check(d['started_ns']<=d['refresh_started_ns']<=d['refresh_finished_ns']<=d['finished_ns'],'refresh bracket')
        check(d['thread_id']==prov['owner_thread_id']==summary['scheduler']['owner_thread_id'],'owner thread')
    leak=[r for r in events if r.get('event')!='post_control_score' and
          any(k in r for k in ('kill_count','death_count','episode_tic_after','state_tic'))]
    check(not leak,'privileged scorer leakage')
    if runtime:
        for n,h in obj(rt/'sources.json').items():check(sha(Path(runtime)/'research'/n)==h,'runtime hash '+n)
    if candidate:
        for n,h in {**obj(out/'launch.json')['sources'],**prov['sources']}.items():check(sha(Path(candidate)/n)==h,'candidate hash '+n)
    scored=rows(rt/'scorer-events.jsonl') if (rt/'scorer-events.jsonl').exists() else []
    # Re-derive positive kill edges from samples, not claimed first-useful fields.
    positive=[];last=None
    for s in samples:
        v=s['payload']
        if last and v['kill_count']>last['kill_count']:positive.append(v['sample_ns'])
        last=v
    event_positive=[r['observed_ns'] for r in scored if r.get('kind')=='KILL_COUNT_INCREASE']
    check(positive==event_positive,'kill event replay')
    before=[d for d in diag if d['sample']['sample_ns']<=deadline]
    refresh_durations=[(d['refresh_finished_ns']-d['refresh_started_ns'])/1e6 for d in before if d['refresh_called']]
    dispatch=[(r['received_ns']-r['command']['sent_ns'])/1e6 for r in events
              if r.get('event')=='command' and 'heartbeat' in r.get('command',{})]
    sent=obj(out/'driver.json')['heartbeats_sent']
    check(len(dispatch)==len(sent),'all heartbeat commands dispatched')
    check(all(x>=0 for x in dispatch),'negative command latency')
    first=min(r['admitted_ns'] for r in admissions)
    prefinal=final[0] if final else None
    health=[r['signals']['health']['value'] for r in events if r.get('event')=='typed_observation' and r.get('signals',{}).get('health',{}).get('status')=='observed']
    ammo=[r['signals']['ammo']['value'] for r in events if r.get('event')=='typed_observation' and r.get('signals',{}).get('ammo',{}).get('status')=='observed']
    return dict(id=spec['id'],mode=spec['mode'],rep=spec['rep'],hard_pass=not fail,failures=fail,
        score={k:score[k] for k in FIELDS},health_first_last=[health[0],health[-1]] if health else None,
        ammo_first_last=[ammo[0],ammo[-1]] if ammo else None,
        acquisition_count=len(samples),valid_acquisitions=valid,
        final_acquisition_ms=(prefinal['sample_finished_ns']-prefinal['sample_started_ns'])/1e6 if prefinal else None,
        final_payload_within_bracket=bool(prefinal and prefinal['sample_started_ns']<=prefinal['payload']['sample_ns']<=prefinal['sample_finished_ns']),
        distinct_source_tics_before_deadline=len({d['episode_tic_after'] for d in before}),
        positive_before_deadline=any(v<=deadline for v in positive),
        first_positive_after_admission_ms=(min(positive)-first)/1e6 if positive else None,
        refresh_before_deadline_count=len(refresh_durations),refresh_call_ms=stats(refresh_durations),
        refresh_blocking_before_deadline_ms=sum(refresh_durations),command_dispatch_ms=stats(dispatch),
        missed_periods=summary['scheduler']['missed_sample_periods'],
        deadline_to_empty_ms=(cause['verified_ns']-deadline)/1e6,
        physical_occupancy_upper_ms=(cause['verified_ns']-first)/1e6,
        planned_cutoff_ms=spec['cutoff_ms'],heartbeat_count=len(dispatch),controller_leak_count=len(leak))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);ap.add_argument('--runtime',type=Path);ap.add_argument('--candidate',type=Path);a=ap.parse_args()
    print(json.dumps(analyze(a.out,a.runtime,a.candidate),indent=2))
if __name__=='__main__':main()
