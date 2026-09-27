from __future__ import annotations
import argparse, hashlib, json, os, queue, shutil, subprocess, sys, threading, time
from pathlib import Path
import numpy as np
from PIL import Image

VISIBLE_CHANGE_THRESHOLD=0.015

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def normalized_mae(a,b):
    with Image.open(a) as ia, Image.open(b) as ib:
        aa=np.asarray(ia.convert('RGB'),dtype=np.float32); bb=np.asarray(ib.convert('RGB'),dtype=np.float32)
    if aa.shape != bb.shape: raise ValueError('shape mismatch')
    return float(np.abs(aa-bb).mean()/255.0)

def wait_from(q,p,pred,timeout=35):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        try:r=q.get(timeout=.25)
        except queue.Empty:
            if p.poll() is not None: raise RuntimeError('session died: '+p.stderr.read())
            continue
        if pred(r): return r
    raise TimeoutError('expected event')

def run_case(case, out, runtime_root, python):
    out.mkdir(parents=True,exist_ok=False)
    doom=runtime_root/'research/doom'; live=runtime_root/'research/live_control'; fixture=doom/'fixtures/map01-threat-contact-v2/fixture.json'
    sys.path[:0]=[str(doom),str(live)]
    from doom_action_validity_contract_v1 import build_contract
    from doom_typed_observation_v1 import build_action_snapshot
    from action_validity_admission_v1 import evaluate_action_validity
    env=os.environ.copy(); env['PYTHONPATH']=f'{doom}:{live}'
    p=subprocess.Popen([str(python),str(doom/'session_map01_v12.py'),'--out',str(out/'runtime'),'--seed','990619','--timeout-seconds','60','--skill','1','--load-fixture-manifest',str(fixture)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1,env=env)
    q=queue.Queue(); events=[]
    def reader():
        for line in p.stdout:
            try:r=json.loads(line)
            except Exception: continue
            events.append(r); q.put(r)
    threading.Thread(target=reader,daemon=True).start()
    wait=lambda pred,timeout=35: wait_from(q,p,pred,timeout)
    ready=wait(lambda r:r.get('event')=='ready')
    source_t=wait(lambda r:r.get('event')=='typed_observation')
    source_o=wait(lambda r:r.get('event')=='observation' and r.get('sequence')==source_t.get('sequence'))
    p.stdin.write(json.dumps({'op':'clock'})+'\n'); p.stdin.flush(); clock=wait(lambda r:r.get('event')=='clock')
    if case['arm']=='coast':
        steps=[{'op':'coast','duration_ms':600,'sample_ms':50},{'op':'observe'}]
    elif case['arm']=='recovery':
        steps=([{'op':'hold','keys':['d'],'duration_ms':50},{'op':'observe'}]*5)+[{'op':'coast','duration_ms':350,'sample_ms':50},{'op':'observe'}]
    else: raise ValueError(case['arm'])
    ident=case['id']
    cmd={'op':'submit','id':ident,'expected_sequence':source_o['sequence'],'valid_until_ns':clock['runtime_ns']+5_000_000_000,'steps':steps}
    p.stdin.write(json.dumps(cmd)+'\n'); p.stdin.flush()
    accepted=wait(lambda r:r.get('event') in ('accepted','rejected') and (r.get('id')==ident or r.get('event')=='rejected'))
    if accepted.get('event')!='accepted': raise RuntimeError(('unexpected rejection',accepted))
    terminal=wait(lambda r:r.get('event')=='terminal' and r.get('id')==ident)
    post_t=[r for r in events if r.get('event')=='typed_observation' and r.get('sequence',0)>source_t['sequence']][-1]
    post_obs=[r for r in events if r.get('event')=='observation' and r.get('sequence')==post_t['sequence']]
    post_o=post_obs[-1] if post_obs else wait(lambda r:r.get('event')=='observation' and r.get('sequence')==post_t['sequence'])
    action=[{'action':'turn_right','extent':'short'}]
    authored={'critical_health_minimum':50,'maximum_health_loss':8,'minimum_ammo':0,'max_current_age_ms':700}
    contract=build_contract(action,authored,source_t['signals']['health'],source_t['signals']['ammo'])
    snap=build_action_snapshot(post_t,contract); decided=time.perf_counter_ns(); validity=evaluate_action_validity(action,contract,snap,decided)
    p.stdin.write(json.dumps({'op':'finish'})+'\n'); p.stdin.flush(); score=wait(lambda r:r.get('event')=='post_control_score')
    p.stdin.close(); p.wait(timeout=12)
    result={**case,'schema':'recovery-admission-blindspot-case-v1','source_sequence':source_t['sequence'],'post_sequence':post_t['sequence'],
      'source_health':source_t['signals']['health']['value'],'post_health':post_t['signals']['health']['value'],
      'source_ammo':source_t['signals']['ammo']['value'],'post_ammo':post_t['signals']['ammo']['value'],
      'source_frame_rgb_sha256':source_t['frame_rgb_sha256'],'post_frame_rgb_sha256':post_t['frame_rgb_sha256'],
      'source_image':source_o['image'],'post_image':post_o['image'],'viewport_normalized_mae':normalized_mae(source_o['image'],post_o['image']),
      'visible_change_threshold':VISIBLE_CHANGE_THRESHOLD,'visible_change':normalized_mae(source_o['image'],post_o['image'])>VISIBLE_CHANGE_THRESHOLD,
      'validity_status':validity['status'],'validity_reason':validity['reason'],'validity_checks':validity['checks'],'snapshot_age_ms':(decided-post_t['capture_ns'])/1e6,
      'terminal_status':terminal.get('status'),'release':terminal.get('release'),'accepted_program_sha256':accepted.get('program_sha256'),
      'score':{k:score.get(k) for k in ('kill_count','death_count','map_exit','player_dead')},
      'event_count':len(events),'runtime_sources_sha256':sha256(out/'runtime'/'sources.json')}
    (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--plan',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--runtime-root',type=Path,required=True); ap.add_argument('--python',type=Path,required=True); a=ap.parse_args()
    plan=json.loads(a.plan.read_text()); a.out.mkdir(parents=True,exist_ok=False)
    results=[]
    for case in plan['cases']:
        results.append(run_case(case,a.out/case['id'],a.runtime_root,a.python))
    by_pair={}
    for r in results: by_pair.setdefault(r['pair'],{})[r['arm']]=r
    pairs=[]
    for pair,arms in sorted(by_pair.items()):
        c=arms['coast']; rec=arms['recovery']; pairs.append({'pair':pair,'coast_mae':c['viewport_normalized_mae'],'recovery_mae':rec['viewport_normalized_mae'],'recovery_over_coast_ratio':rec['viewport_normalized_mae']/max(c['viewport_normalized_mae'],1e-12),'coast_valid':c['validity_status']=='VALID_CURRENT','recovery_valid':rec['validity_status']=='VALID_CURRENT','recovery_visible_change':rec['visible_change']})
    summary={'schema':'recovery-admission-blindspot-summary-v1','cases':results,'pairs':pairs}
    (a.out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
