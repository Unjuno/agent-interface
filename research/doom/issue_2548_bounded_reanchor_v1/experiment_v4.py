from __future__ import annotations
import argparse, hashlib, json, os, queue, subprocess, threading, time, uuid
from pathlib import Path
import numpy as np
from PIL import Image

THRESHOLD = 0.015
REANCHOR_BUDGET = 1

def file_sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1<<20),b''): h.update(block)
    return h.hexdigest()

def frame_sha(path):
    with Image.open(path) as im:
        raw=np.asarray(im.convert('RGB'),dtype=np.uint8).tobytes()
    return hashlib.sha256(raw).hexdigest()

def mae(a,b):
    with Image.open(a) as ia, Image.open(b) as ib:
        aa=np.asarray(ia.convert('RGB'),dtype=np.float32); bb=np.asarray(ib.convert('RGB'),dtype=np.float32)
    if aa.shape!=bb.shape: raise ValueError('frame shape mismatch')
    return float(np.abs(aa-bb).mean()/255.0)

def evaluate_receipt(old,fresh,fresh_count):
    required=('session_id','sequence','frame_rgb_sha256','image')
    if any(not old.get(k) or not fresh.get(k) for k in required):
        return {'admission':'REJECT_PROVENANCE','reason':'MISSING_RECEIPT_FIELD','mae':None}
    old_id=f"{old['session_id']}:{old['sequence']}"; fresh_id=f"{fresh['session_id']}:{fresh['sequence']}"
    if old['session_id']!=fresh['session_id']:
        return {'admission':'REJECT_PROVENANCE','reason':'CROSS_SESSION','mae':None,'old_receipt_id':old_id,'fresh_receipt_id':fresh_id}
    if fresh['sequence']<=old['sequence'] or old_id==fresh_id:
        return {'admission':'REJECT_PROVENANCE','reason':'STALE_OR_DUPLICATE_RECEIPT','mae':None,'old_receipt_id':old_id,'fresh_receipt_id':fresh_id}
    if fresh_count<1 or fresh_count>REANCHOR_BUDGET:
        return {'admission':'REJECT_PROVENANCE','reason':'OBSERVATION_BUDGET','mae':None,'old_receipt_id':old_id,'fresh_receipt_id':fresh_id}
    if frame_sha(old['image'])!=old['frame_rgb_sha256'] or frame_sha(fresh['image'])!=fresh['frame_rgb_sha256']:
        return {'admission':'REJECT_PROVENANCE','reason':'FRAME_HASH_MISMATCH','mae':None,'old_receipt_id':old_id,'fresh_receipt_id':fresh_id}
    value=mae(old['image'],fresh['image'])
    return {'admission':'ADMIT' if value<=THRESHOLD else 'REJECT_CONTEXT_CHANGED','reason':'FRESH_PAIR_EVALUATED','mae':value,'old_receipt_id':old_id,'fresh_receipt_id':fresh_id}

def event_receipt(event,session_id,image_event):
    return {'session_id':session_id,'sequence':event.get('sequence'),'frame_rgb_sha256':event.get('frame_rgb_sha256'),'image':image_event.get('image'),'capture_ns':event.get('capture_ns')}

def run_case(case,out,runtime_root,python,foreign_receipt=None):
    out.mkdir(parents=True,exist_ok=False)
    session_id=uuid.uuid4().hex
    doom=runtime_root/'research/doom'; live=runtime_root/'research/live_control'; fixture=doom/'fixtures/map01-threat-contact-v2/fixture.json'
    env=os.environ.copy(); env['PYTHONPATH']=f'{doom}:{live}'
    proc=subprocess.Popen([str(python),str(doom/'session_map01_v12.py'),'--out',str(out/'runtime'),'--seed',str(case['seed']),'--timeout-seconds','60','--skill','1','--load-fixture-manifest',str(fixture)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1,env=env)
    q=queue.Queue(); events=[]
    def reader():
        for line in proc.stdout:
            try:item=json.loads(line)
            except Exception:continue
            item['_capture_session_id']=session_id; events.append(item); q.put(item)
    threading.Thread(target=reader,daemon=True).start()
    def wait(pred,timeout=35):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            try:item=q.get(timeout=.25)
            except queue.Empty:
                if proc.poll() is not None: raise RuntimeError('session died: '+proc.stderr.read())
                continue
            if pred(item):return item
        raise TimeoutError('expected event')
    ready=wait(lambda x:x.get('event')=='ready')
    source_t=wait(lambda x:x.get('event')=='typed_observation')
    source_o=wait(lambda x:x.get('event')=='observation' and x.get('sequence')==source_t['sequence'])
    proc.stdin.write(json.dumps({'op':'clock'})+'\n');proc.stdin.flush();clock=wait(lambda x:x.get('event')=='clock')
    steps=[{'op':'coast','duration_ms':600,'sample_ms':50},{'op':'observe'}] if case['arm']=='coast' else ([{'op':'hold','keys':['d'],'duration_ms':50},{'op':'observe'}]*5)+[{'op':'coast','duration_ms':350,'sample_ms':50},{'op':'observe'}]
    if case['capture_fresh']:steps.append({'op':'observe'})
    ident=case['id']; program={'op':'submit','id':ident,'expected_sequence':source_o['sequence'],'valid_until_ns':clock['runtime_ns']+5_000_000_000,'steps':steps}
    proc.stdin.write(json.dumps(program)+'\n');proc.stdin.flush()
    accepted=wait(lambda x:x.get('event') in ('accepted','rejected') and (x.get('id')==ident or x.get('event')=='rejected'))
    if accepted.get('event')!='accepted':raise RuntimeError(('unexpected rejection',accepted))
    terminal=wait(lambda x:x.get('event')=='terminal' and x.get('id')==ident)
    typed=[x for x in events if x.get('event')=='typed_observation' and x.get('sequence',0)>source_t['sequence']]
    typed_post=typed[-2] if case['capture_fresh'] else typed[-1]
    post_o=next(x for x in events if x.get('event')=='observation' and x.get('sequence')==typed_post['sequence'])
    captured_fresh=typed[-1] if case['capture_fresh'] else None
    fresh_count=sum(1 for x in typed if x.get('sequence',0)>typed_post['sequence']) if case['capture_fresh'] else 0
    proc.stdin.write(json.dumps({'op':'finish'})+'\n');proc.stdin.flush();score=wait(lambda x:x.get('event')=='post_control_score')
    proc.stdin.close();proc.wait(timeout=12)
    old=event_receipt(typed_post,session_id,post_o)
    fresh_obs=next((x for x in events if x.get('event')=='observation' and x.get('sequence')==captured_fresh['sequence']),None) if captured_fresh else None
    same_session_fresh=event_receipt(captured_fresh,session_id,fresh_obs) if captured_fresh and fresh_obs else None
    if case['candidate']=='fresh': candidate=same_session_fresh
    elif case['candidate']=='stale': candidate=old
    elif case['candidate']=='cross_session': candidate=foreign_receipt
    elif case['candidate']=='ambiguous':
        candidate=dict(same_session_fresh) if same_session_fresh else {}
        if candidate:candidate.pop('frame_rgb_sha256',None)
    else:candidate=None
    reanchor=evaluate_receipt(old,candidate,fresh_count) if candidate is not None else {'admission':'REJECT_NO_FRESH_OBSERVATION','reason':'NO_CANDIDATE_RECEIPT','mae':None}
    guard_mae=mae(source_o['image'],post_o['image'])
    (out/'capture-events.jsonl').write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in events))
    (out/'session.json').write_text(json.dumps({'session_id':session_id,'process_id':proc.pid,'seed':case['seed'],'runtime_sources_sha256':file_sha(out/'runtime'/'sources.json')},indent=2,sort_keys=True)+'\n')
    result={**case,'schema':'bounded-fresh-reanchor-case-v2','session_id':session_id,'source_receipt':event_receipt(source_t,session_id,source_o),'old_receipt':old,'captured_fresh_receipt':same_session_fresh,'candidate_receipt':candidate,'fresh_observation_count':fresh_count,'guard_only':{'admission':'ADMIT' if guard_mae<=THRESHOLD else 'REJECT_CONTEXT_CHANGED','mae':guard_mae},'reanchor':reanchor,'terminal_status':terminal.get('status'),'release':terminal.get('release'),'score':{k:score.get(k) for k in ('kill_count','death_count','map_exit','player_dead')},'event_count':len(events),'runtime_sources_sha256':file_sha(out/'runtime'/'sources.json')}
    (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result, (same_session_fresh if same_session_fresh else old)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--runtime-root',type=Path,required=True);ap.add_argument('--python',type=Path,required=True);a=ap.parse_args()
    plan=json.loads(a.plan.read_text());rows=[];prior={}
    for case in plan['cases']:
        foreign=prior.get(case.get('foreign_from')) if case.get('foreign_from') else None
        row,receipt=run_case(case,a.out/case['id'],a.runtime_root,a.python,foreign);rows.append(row);prior[case['id']]=receipt
    (a.out/'results.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'case_count':len(rows),'case_ids':[r['id'] for r in rows]},sort_keys=True))
if __name__=='__main__':main()
