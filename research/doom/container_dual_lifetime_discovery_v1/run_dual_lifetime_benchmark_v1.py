from __future__ import annotations
import json, pathlib, shutil, subprocess, time, statistics, os, sys

ROOT=pathlib.Path('/tmp/lab/src')
DOOM=ROOT/'research/doom'
PYTHON='/tmp/lab/venv/bin/python'
DUAL=pathlib.Path('/tmp/lab/dual_lifetime')
FIXTURE=DOOM/'fixtures/map01-threat-contact-v2/fixture.json'
OUTROOT=DUAL/'runs'
AUTHORITY_MS=600


def send(proc,obj):
    proc.stdin.write(json.dumps(obj,separators=(',',':'))+'\n');proc.stdin.flush()

def sig(row,name):
    try:
        x=row['signals'][name]
        return x['value'] if x.get('status')=='observed' else None
    except Exception:return None

def read_json_line(proc, deadline):
    while time.monotonic()<deadline:
        line=proc.stdout.readline()
        if not line:
            if proc.poll() is not None:return None
            continue
        try:return json.loads(line)
        except json.JSONDecodeError:continue
    return None

def direct_final(out):
    rows=[]
    p=out/'scorer-samples.jsonl'
    if p.exists():
        for line in p.read_text().splitlines():
            try: rows.append(json.loads(line))
            except Exception: pass
    return next((r['payload'] for r in reversed(rows) if r.get('direct_final_sample') is True),None)

def score_agrees(out):
    if not (out/'score.json').exists():return False
    s=json.loads((out/'score.json').read_text());d=direct_final(out)
    if d is None:return False
    return all(s[k]==d[k] for k in ('map_exit','episode_finished','player_dead','death_count','kill_count'))

def run_one(seed,arm,label):
    out=OUTROOT/label;shutil.rmtree(out,ignore_errors=True)
    script='session_map01_v13.py' if arm=='baseline' else str(DUAL/'session_map01_dual_lifetime_v1.py')
    cmd=[PYTHON,script,'--out',str(out),'--seed',str(seed),'--timeout-seconds','60','--skill','1','--load-fixture-manifest',str(FIXTURE)]
    env=os.environ.copy()
    if arm=='candidate':
        env['PYTHONPATH']=str(DUAL)+os.pathsep+str(DOOM)+os.pathsep+str(ROOT/'research/live_control')+os.pathsep+env.get('PYTHONPATH','')
        cwd=str(DOOM)
    else: cwd=str(DOOM)
    proc=subprocess.Popen(cmd,cwd=cwd,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    events=[];last_seq=None;initial_health=None;terminal=None;clock=None;post_terminal=None
    compare_id=f'{label}-cmp'; post_id=f'{label}-post'
    try:
        deadline=time.monotonic()+20
        while time.monotonic()<deadline and last_seq is None:
            row=read_json_line(proc,deadline)
            if row is None:break
            events.append(row)
            if row.get('event')=='typed_observation' and initial_health is None: initial_health=sig(row,'health')
            if row.get('event')=='observation':last_seq=row['sequence']
        if last_seq is None:raise RuntimeError('initial observation unavailable')

        send(proc,{'op':'clock'})
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            row=read_json_line(proc,deadline)
            if row is None:break
            events.append(row)
            if row.get('event')=='observation':last_seq=row['sequence']
            if row.get('event')=='clock':clock=row;break
        if clock is None:raise RuntimeError('clock unavailable')
        valid_until=int(clock['runtime_ns'])+AUTHORITY_MS*1_000_000
        send(proc,{'op':'submit','id':compare_id,'expected_sequence':last_seq,'valid_until_ns':valid_until,
                   'steps':[{'op':'hold','keys':['Shift_L'],'duration_ms':2000}]})

        deadline=time.monotonic()+8
        compare_obs=[];typed=[]
        while time.monotonic()<deadline:
            row=read_json_line(proc,deadline)
            if row is None:break
            events.append(row)
            if row.get('event')=='typed_observation' and row.get('id')==compare_id: typed.append(row)
            if row.get('event')=='observation':
                last_seq=row['sequence']
                if row.get('id')==compare_id:compare_obs.append(row)
            if row.get('event')=='terminal' and row.get('id')==compare_id:
                terminal=row;break
        if terminal is None:raise RuntimeError('comparison terminal unavailable')

        if arm=='baseline':
            send(proc,{'op':'clock'})
            deadline=time.monotonic()+2;postclock=None
            while time.monotonic()<deadline:
                row=read_json_line(proc,deadline)
                if row is None:break
                events.append(row)
                if row.get('event')=='observation':last_seq=row['sequence']
                if row.get('event')=='clock':postclock=row;break
            if postclock is None:raise RuntimeError('post clock unavailable')
            send(proc,{'op':'submit','id':post_id,'expected_sequence':last_seq,
                       'valid_until_ns':int(postclock['runtime_ns'])+2_000_000_000,
                       'steps':[{'op':'observe'}]})
            deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                row=read_json_line(proc,deadline)
                if row is None:break
                events.append(row)
                if row.get('event')=='typed_observation' and row.get('id')==post_id: typed.append(row)
                if row.get('event')=='observation':
                    last_seq=row['sequence']
                    if row.get('id')==post_id:compare_obs.append(row)
                if row.get('event')=='terminal' and row.get('id')==post_id:
                    post_terminal=row;break
            if post_terminal is None:raise RuntimeError('baseline post terminal unavailable')

        send(proc,{'op':'finish'})
        try:proc.wait(timeout=8)
        except subprocess.TimeoutExpired:proc.kill();proc.wait()
        stderr=proc.stderr.read();(out/'harness-stderr.txt').write_text(stderr)
        owner=json.loads((out/'owner-events.json').read_text())
        release=next((r for r in owner if r.get('event')=='owner_release' and r.get('reason')=='expired'),None)
        if release is None:raise RuntimeError('scheduled expiry owner release missing')
        verified_ns=release['verified_ns']
        if arm=='baseline':
            eligible=[o for o in compare_obs if o.get('id')==post_id and type(o.get('capture_ns')) is int and o['capture_ns']>=verified_ns]
        else:
            post_meta=terminal.get('post_authority_observation') or {}
            post_sequence=post_meta.get('sequence')
            eligible=[o for o in compare_obs if o.get('id')==compare_id and o.get('sequence')==post_sequence and type(o.get('capture_ns')) is int and o['capture_ns']>=verified_ns]
        if not eligible:raise RuntimeError('declared post-release full observation missing')
        fresh=min(eligible,key=lambda o:o['capture_ns'])
        admissions=[e for e in events if e.get('event') in ('input_admission','pointer_admission')]
        after_adm=[e for e in admissions if (e.get('admitted_ns') or 0)>verified_ns]
        candidate_post=terminal.get('post_authority_observation') if arm=='candidate' else None
        score=json.loads((out/'score.json').read_text())
        post_typed=next((t for t in typed if type(t.get('capture_ns')) is int and t['capture_ns']>=verified_ns),None)
        result={
          'seed':seed,'arm':arm,'label':label,'valid_until_ns':valid_until,
          'terminal_status':terminal.get('status'),'steps_completed':terminal.get('steps_completed'),
          'release_reason':release.get('reason'),'release_verified':release.get('verified'),
          'release_keys_down':release.get('keys_down'),'release_buttons_down':release.get('buttons_down'),
          'deadline_to_verified_empty_ms':(verified_ns-valid_until)/1e6,
          'release_to_fresh_capture_ms':(fresh['capture_ns']-verified_ns)/1e6,
          'fresh_sequence':fresh.get('sequence'),'post_release_input_admissions':len(after_adm),
          'candidate_post_authority':candidate_post,
          'baseline_post_terminal_status':post_terminal.get('status') if post_terminal else None,
          'initial_health':initial_health,'post_health':sig(post_typed,'health') if post_typed else None,
          'score':{k:score.get(k) for k in ('map_exit','episode_finished','player_dead','death_count','kill_count')},
          'score_agreement':score_agrees(out),'process_returncode':proc.returncode
        }
        (out/'harness-result.json').write_text(json.dumps(result,indent=2)+'\n')
        return result
    finally:
        if proc.poll() is None:
            try:send(proc,{'op':'finish'})
            except Exception:pass
            try:proc.wait(timeout=2)
            except Exception:proc.kill();proc.wait()

def aggregate(results):
    b=[r for r in results if r['arm']=='baseline'];c=[r for r in results if r['arm']=='candidate']
    med=lambda rows,k:statistics.median(r[k] for r in rows)
    hard={
      'all_release_verified':all(r['release_verified'] is True and r['release_keys_down']==[] and r['release_buttons_down']==[] for r in results),
      'all_score_agreement':all(r['score_agreement'] for r in results),
      'candidate_zero_post_release_input':all(r['post_release_input_admissions']==0 for r in c),
      'candidate_status_authority_ended':all(r['terminal_status']=='authority_ended' and r['release_reason']=='expired' for r in c),
      'candidate_one_capture':all(isinstance(r['candidate_post_authority'],dict) and r['candidate_post_authority'].get('captures')==1 and r['candidate_post_authority'].get('within_lifecycle_deadline') is True for r in c),
      'baseline_expired_then_observe':all(r['terminal_status']=='expired' and r['baseline_post_terminal_status']=='completed' for r in b)
    }
    summary={
      'baseline_release_to_fresh_capture_median_ms':med(b,'release_to_fresh_capture_ms'),
      'candidate_release_to_fresh_capture_median_ms':med(c,'release_to_fresh_capture_ms'),
      'baseline_deadline_to_empty_median_ms':med(b,'deadline_to_verified_empty_ms'),
      'candidate_deadline_to_empty_median_ms':med(c,'deadline_to_verified_empty_ms'),
    }
    summary['fresh_capture_improvement_ms']=summary['baseline_release_to_fresh_capture_median_ms']-summary['candidate_release_to_fresh_capture_median_ms']
    summary['release_regression_ms']=summary['candidate_deadline_to_empty_median_ms']-summary['baseline_deadline_to_empty_median_ms']
    if not all(hard.values()): decision='REJECT'
    elif summary['fresh_capture_improvement_ms']>=20 or summary['release_regression_ms']<=2:
        decision='PROMOTE_MECHANISM_CANDIDATE'
    else:decision='HOLD'
    return {'schema':'dual-lifetime-map01-development-result-v1','results':results,'hard_gates':hard,'summary':summary,'decision':decision}

def main():
    OUTROOT.mkdir(parents=True,exist_ok=True)
    schedule=[(993100,'baseline'),(993100,'candidate'),(993101,'candidate'),(993101,'baseline'),(993102,'baseline'),(993102,'candidate')]
    results=[]
    for i,(seed,arm) in enumerate(schedule,1):
        label=f'{i:02d}-{seed}-{arm}'
        r=run_one(seed,arm,label);results.append(r)
        print(json.dumps({k:r[k] for k in ('label','arm','terminal_status','deadline_to_verified_empty_ms','release_to_fresh_capture_ms','post_release_input_admissions','score_agreement')},sort_keys=True),flush=True)
    agg=aggregate(results)
    (DUAL/'result.json').write_text(json.dumps(agg,indent=2)+'\n')
    print(json.dumps({'decision':agg['decision'],**agg['summary'],'hard_gates':agg['hard_gates']},sort_keys=True),flush=True)
if __name__=='__main__':main()
