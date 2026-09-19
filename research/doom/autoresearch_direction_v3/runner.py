#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, queue, shutil, statistics, subprocess, sys, threading, time
from pathlib import Path

SCHEMA='map01-direction-source-closed-v3'
RUNTIME_BASE='9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245'
ARTIFACT_SHA256='522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b'
SESSION='research/doom/session_map01_v13.py'

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()

def read_jsonl(path:Path):
    if not path.exists(): return []
    rows=[]
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.strip(): rows.append(json.loads(line))
    return rows

def verify_runtime(runtime_root:Path,manifest_path:Path,full=False):
    manifest=json.loads(manifest_path.read_text())
    if manifest.get('base_commit')!=RUNTIME_BASE: raise RuntimeError('runtime base mismatch')
    files=manifest['files']; errors=[]
    keys=list(files) if full else [SESSION]
    for rel in keys:
        p=runtime_root/rel
        got=sha256(p) if p.is_file() else None
        want=files.get(rel,{}).get('sha256')
        if got!=want: errors.append({'path':rel,'got':got,'want':want})
    if errors: raise RuntimeError('runtime source mismatch: '+json.dumps(errors[:5]))
    return {'base_commit':manifest['base_commit'],'files_checked':len(keys)}

def verify_case_sources(session_out:Path,manifest:dict):
    sources=json.loads((session_out/'sources.json').read_text())
    bad=[]
    for rel,got in sources.items():
        key='research/'+rel
        want=manifest.get('files',{}).get(key,{}).get('sha256')
        if got!=want: bad.append({'path':key,'got':got,'want':want})
    return {'ok':not bad,'count':len(sources),'bad':bad}

def verify_freeze(exp_root:Path, fixtures:dict):
    fr=json.loads((exp_root/'FREEZE.json').read_text())
    for name,want in fr['source_sha256'].items():
        got=sha256(exp_root/name)
        if got!=want: raise RuntimeError(f'frozen source mismatch {name}: {got} != {want}')
    meta=fr['fixture']
    m=fixtures['original']
    for name,want in (('manifest',meta['manifest_sha256']),('save',meta['save_sha256']),('source',meta['source_frame_sha256'])):
        got=sha256(m[name])
        if got!=want: raise RuntimeError(f'frozen original fixture mismatch {name}')
    return fr

def _send(p,row):
    p.stdin.write(json.dumps(row,separators=(',',':'))+'\n'); p.stdin.flush()

def attach_stdout_reader(p):
    q=queue.Queue()
    def pump():
        try:
            for line in p.stdout:
                q.put(line)
        finally:
            q.put(None)
    threading.Thread(target=pump,name='child-stdout-reader',daemon=True).start()
    p._event_q=q
    return p

def _next_json(p,timeout_s):
    try:
        line=p._event_q.get(timeout=timeout_s)
    except queue.Empty:
        raise TimeoutError(f'session event timeout; rc={p.poll()}')
    if line is None:
        raise EOFError(f'session stdout closed; rc={p.poll()}')
    try:return json.loads(line),line
    except json.JSONDecodeError:return {'event':'nonjson_stdout','line':line.rstrip('\n')},line

def _until(p,event,pred=lambda r:True,timeout_s=30,transcript=None):
    deadline=time.monotonic()+timeout_s
    while time.monotonic()<deadline:
        row,raw=_next_json(p,max(0.1,deadline-time.monotonic()))
        if transcript is not None:
            transcript.write(raw if raw.endswith('\n') else raw+'\n'); transcript.flush()
        if row.get('event')==event and pred(row): return row
    raise TimeoutError('waiting '+event)

def latest_typed_before(events,case_id,deadline_ns):
    rows=[r for r in events if r.get('event')=='typed_observation' and r.get('id')==case_id and isinstance(r.get('capture_ns'),int) and r['capture_ns']<=deadline_ns]
    if not rows:return None
    r=max(rows,key=lambda x:x['capture_ns']); sig=r.get('signals',{})
    def val(name):
        x=sig.get(name,{})
        return x.get('value') if x.get('status')=='observed' else None
    return {'capture_ns':r['capture_ns'],'sequence':r.get('sequence'),'health':val('health'),'ammo':val('ammo')}

def initial_typed(events):
    rows=[r for r in events if r.get('event')=='typed_observation' and r.get('id')=='initial']
    if not rows:return None
    r=rows[0];sig=r.get('signals',{})
    def val(name):
        x=sig.get(name,{})
        return x.get('value') if x.get('status')=='observed' else None
    return {'capture_ns':r.get('capture_ns'),'health':val('health'),'ammo':val('ammo')}

def scorer_metrics(session_out:Path,accepted_ns:int,deadline_ns:int,score:dict):
    rows=read_jsonl(session_out/'scorer-samples.jsonl')
    payloads=[r['payload'] for r in rows if isinstance(r.get('payload'),dict)]
    pre=[p for p in payloads if p.get('sample_ns',10**30)<=deadline_ns]
    before=[p for p in payloads if p.get('sample_ns',10**30)<=accepted_ns]
    if not pre: raise RuntimeError('no scorer sample before authority deadline')
    base=max(before,key=lambda p:p['sample_ns']) if before else min(pre,key=lambda p:p['sample_ns'])
    last=max(pre,key=lambda p:p['sample_ns'])
    final_rows=[r for r in rows if r.get('direct_final_sample')]
    if len(final_rows)!=1: raise RuntimeError(f'direct final scorer count {len(final_rows)}')
    final=final_rows[0]['payload']
    fields=['map_exit','episode_finished','player_dead','death_count','kill_count']
    agree=all(final.get(k)==score.get(k) for k in fields)
    events=read_jsonl(session_out/'scorer-events.jsonl')
    useful=[e for e in events if e.get('useful') is True and isinstance(e.get('observed_ns'),int) and e['observed_ns']<=deadline_ns]
    summary=json.loads((session_out/'scorer-summary.json').read_text())
    return {
      'baseline':base,'latest_predeadline':last,
      'kill_delta_predeadline':last['kill_count']-base['kill_count'],
      'death_delta_predeadline':last['death_count']-base['death_count'],
      'progress_success_predeadline':last['kill_count']>base['kill_count'],
      'useful_event_count_predeadline':len(useful),
      'first_useful_event_ns':min((e['observed_ns'] for e in useful),default=None),
      'direct_final':final,'terminal_score_agreement':agree,
      'missed_sample_periods':summary.get('scheduler',{}).get('missed_sample_periods'),
      'controller_visible':summary.get('controller_visible')}

def setup_state(p,case,transcript):
    state=case['state']
    if state=='original': return {'state':'original','applied':False}
    key={'left':'a','right':'d'}[state]
    _send(p,{'op':'clock'}); clk=_until(p,'clock',timeout_s=5,transcript=transcript)
    sid='setup-'+case['case_id']
    valid_until=int(clk['runtime_ns'])+1_500_000_000
    command={'op':'submit','id':sid,'expected_sequence':clk['sequence'],'valid_until_ns':valid_until,
             'steps':[{'op':'hold','keys':[key],'duration_ms':300}]}
    _send(p,command)
    accepted=_until(p,'accepted',lambda r:r.get('id')==sid,timeout_s=10,transcript=transcript)
    term=_until(p,'terminal',lambda r:r.get('id')==sid,timeout_s=10,transcript=transcript)
    release=term.get('release') or {}
    hard={'completed':term.get('status')=='completed','release_verified':release.get('verified') is True,
          'release_empty':release.get('keys_down')==[] and release.get('buttons_down')==[]}
    if not all(hard.values()): raise RuntimeError('setup state integrity failure '+json.dumps({'case':case['case_id'],'hard':hard,'terminal':term}))
    return {'state':state,'applied':True,'key':key,'hold_ms':300,'accepted_ns':accepted.get('accepted_ns'),
            'terminal_status':term.get('status'),'release_verified':release.get('verified'),'release_keys_down':release.get('keys_down'),
            'release_buttons_down':release.get('buttons_down')}

def run_case(runtime_root:Path, manifest:dict, fixture_manifest:Path, case:dict, out_dir:Path, timeout_seconds=60):
    if out_dir.exists(): raise RuntimeError(f'case output already exists: {out_dir}')
    out_dir.mkdir(parents=True)
    session_out=out_dir/'session'
    cmd=[sys.executable,str(runtime_root/SESSION),'--out',str(session_out),'--seed',str(case['seed']),'--timeout-seconds',str(timeout_seconds),'--skill','1','--load-fixture-manifest',str(fixture_manifest)]
    p=attach_stdout_reader(subprocess.Popen(cmd,cwd=runtime_root/'research/doom',stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1,env=os.environ.copy()))
    transcript=(out_dir/'controller-stdout.jsonl').open('w',encoding='utf-8')
    try:
        _until(p,'ready',timeout_s=20,transcript=transcript)
        _until(p,'observation',lambda r:r.get('id')=='initial',timeout_s=20,transcript=transcript)
        setup=setup_state(p,case,transcript)
        _send(p,{'op':'clock'});clk=_until(p,'clock',timeout_s=5,transcript=transcript)
        valid_until=int(clk['runtime_ns'])+int(case['deadline_ms']*1_000_000)
        command={'op':'submit','id':case['case_id'],'expected_sequence':clk['sequence'],'valid_until_ns':valid_until,'steps':[{'op':'hold','keys':case['keys'],'duration_ms':case['requested_hold_ms']},{'op':'observe'}]}
        _send(p,command)
        accepted=_until(p,'accepted',lambda r:r.get('id')==case['case_id'],timeout_s=10,transcript=transcript)
        term=_until(p,'terminal',lambda r:r.get('id')==case['case_id'],timeout_s=15,transcript=transcript)
        _send(p,{'op':'finish'});score_evt=_until(p,'post_control_score',timeout_s=10,transcript=transcript)
        p.stdin.close();rc=p.wait(timeout=15);stderr=p.stderr.read();(out_dir/'stderr.txt').write_text(stderr)
    except Exception:
        try:p.stdin.close()
        except Exception:pass
        try:p.terminate();p.wait(timeout=3)
        except Exception:
            try:p.kill()
            except Exception:pass
        raise
    finally: transcript.close()
    if rc!=0: raise RuntimeError(f'session rc={rc}; {stderr[-2000:]}')
    events=read_jsonl(session_out/'events.jsonl');score=json.loads((session_out/'score.json').read_text())
    src=verify_case_sources(session_out,manifest)
    interruption=(term.get('interruption') or {}).get('record') or {}
    release=term.get('release') or {}
    hard={
      'terminal_expired':term.get('status')=='expired',
      'interruption_expired':interruption.get('reason')=='expired',
      'interruption_verified':interruption.get('verified') is True,
      'interruption_empty':interruption.get('keys_down')==[] and interruption.get('buttons_down')==[],
      'terminal_release_verified':release.get('verified') is True,
      'terminal_release_empty':release.get('keys_down')==[] and release.get('buttons_down')==[],
      'source_closure':src['ok'],
    }
    sm=scorer_metrics(session_out,int(accepted['accepted_ns']),valid_until,score)
    hard['terminal_score_agreement']=sm['terminal_score_agreement']
    hard['scorer_hidden']=sm['controller_visible'] is False
    t0=initial_typed(events);t1=latest_typed_before(events,case['case_id'],valid_until)
    deadline_late_ms=(interruption.get('verified_ns')-valid_until)/1e6 if isinstance(interruption.get('verified_ns'),int) else None
    result={
      'schema':SCHEMA+'-case','case':case,'setup_state':setup,'returncode':rc,'accepted_ns':accepted['accepted_ns'],'valid_until_ns':valid_until,
      'terminal_status':term.get('status'),'hard_gates':hard,'hard_pass':all(hard.values()),'source_closure':src,
      'owner_deadline_to_verified_empty_ms':deadline_late_ms,'scorer':sm,'score':score,
      'typed_initial':t0,'typed_latest_predeadline':t1,
      'health_delta_predeadline':(t1['health']-t0['health']) if t0 and t1 and t0['health'] is not None and t1['health'] is not None else None,
      'ammo_delta_predeadline':(t1['ammo']-t0['ammo']) if t0 and t1 and t0['ammo'] is not None and t1['ammo'] is not None else None,
      'session_sources_sha256':sha256(session_out/'sources.json')}
    (out_dir/'case-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result

def decide(results:list[dict]):
    if any(not r['hard_pass'] for r in results):
        return {'decision':'FAIL_MEASUREMENT_INTEGRITY','states':{},'hard_failures':[r['case']['case_id'] for r in results if not r['hard_pass']]}
    by={(r['case']['pair_id'],r['case']['policy']):r for r in results}
    states={}
    for state in ('original','left','right'):
        pairs=sorted({r['case']['pair_id'] for r in results if r['case']['state']==state})
        deltas=[];cand_success=base_success=0;cand_deaths=base_deaths=0
        for pid in pairs:
            b=by[(pid,'attack_only')];c=by[(pid,'back_left_attack')]
            bs=int(b['scorer']['progress_success_predeadline']);cs=int(c['scorer']['progress_success_predeadline'])
            base_success+=bs;cand_success+=cs
            bd=b['scorer']['death_delta_predeadline'];cd=c['scorer']['death_delta_predeadline'];base_deaths+=bd;cand_deaths+=cd
            deltas.append({'pair_id':pid,'success_delta':cs-bs,'kill_delta':c['scorer']['kill_delta_predeadline']-b['scorer']['kill_delta_predeadline'],'death_delta':cd-bd})
        states[state]={'candidate_progress_successes':cand_success,'baseline_progress_successes':base_success,'candidate_deaths':cand_deaths,'baseline_deaths':base_deaths,'pairs':deltas}
    if any(v['candidate_deaths']>v['baseline_deaths'] or v['candidate_progress_successes']<v['baseline_progress_successes'] for v in states.values()): dec='FAIL_FIXED_DIRECTION_GENERALITY'
    elif all(v['candidate_progress_successes']>v['baseline_progress_successes'] and v['candidate_deaths']<=v['baseline_deaths'] for v in states.values()): dec='PASS_SCOPED_DIRECTION_TRANSFER'
    else: dec='HOLD_INSUFFICIENT_DISCRIMINATION'
    return {'decision':dec,'states':states,'hard_failures':[]}

def fixture_paths(runtime_root:Path, exp_root:Path):
    orig=runtime_root/'research/doom/fixtures/map01-threat-contact-v2'
    return {'original':{'manifest':orig/'fixture.json','save':orig/'save.png','source':orig/'source.png'}}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--runtime-root',type=Path,required=True);ap.add_argument('--bundle-manifest',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--full-runtime-verify',action='store_true');a=ap.parse_args()
    exp=Path(__file__).resolve().parent;fixtures=fixture_paths(a.runtime_root,exp);freeze=verify_freeze(exp,fixtures)
    rv=verify_runtime(a.runtime_root,a.bundle_manifest,full=a.full_runtime_verify);manifest=json.loads(a.bundle_manifest.read_text());plan=json.loads((exp/'preregistration.json').read_text())
    if a.out.exists(): raise RuntimeError('formal output path already exists')
    a.out.mkdir(parents=True);(a.out/'preflight.json').write_text(json.dumps({'schema':SCHEMA+'-preflight','runtime':rv,'freeze':freeze,'started_ns':time.perf_counter_ns()},indent=2,sort_keys=True)+'\n')
    results=[]
    for case in plan['cases']:
        r=run_case(a.runtime_root,manifest,fixtures['original']['manifest'],case,a.out/'cases'/case['case_id'],timeout_seconds=plan['timeout_seconds']);results.append(r)
        if not r['hard_pass']:
            summary={'schema':SCHEMA+'-summary','decision':'FAIL_MEASUREMENT_INTEGRITY_STOPPED','completed_cases':len(results),'results':results,'decision_detail':decide(results)}
            (a.out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary['decision_detail'],indent=2));return 2
    d=decide(results);summary={'schema':SCHEMA+'-summary','completed_cases':len(results),'decision':d['decision'],'decision_detail':d,'deadline_lateness_ms':[r['owner_deadline_to_verified_empty_ms'] for r in results],'missed_sample_periods':[r['scorer']['missed_sample_periods'] for r in results],'results':[str(Path('cases')/r['case']['case_id']/'case-result.json') for r in results]}
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,indent=2,sort_keys=True));return 0
if __name__=='__main__': raise SystemExit(main())
