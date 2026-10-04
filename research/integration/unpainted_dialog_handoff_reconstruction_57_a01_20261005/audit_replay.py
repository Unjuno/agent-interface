from __future__ import annotations
import base64, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
PKG=Path(__file__).resolve().parent
RAW_ROOT=PKG/'replay_raw'
SOURCE=ROOT/'research'/'live_control'/'results'/'recovery-assistant-01'
TOOLS=['interface_guarded_input','interface_guarded_observe',
       'interface_guarded_input','interface_guarded_observe']
FRAMES=['006.png','007.png','008.png','009.png']
SEQUENCES=[6,7,8,9]
RUNS=['a01_20261005','a02_20261005']

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):
            h.update(block)
    return h.hexdigest()

def audit_run(run_id):
    raw=RAW_ROOT/run_id
    files=sorted(p for p in raw.iterdir() if p.is_file())
    hashes={p.name:digest(p) for p in files}
    rows=[json.loads(line) for line in (raw/'host-events.jsonl').read_text(encoding='utf-8').splitlines()]
    sends=[row for row in rows if row['kind']=='send_requested']
    assert [row['tool'] for row in sends]==TOOLS
    assert [row['attempt'] for row in sends]==[1,2,3,4]
    for i,(tool,frame,sequence) in enumerate(zip(TOOLS,FRAMES,SEQUENCES),1):
        request=json.loads((raw/f'request-{i}.json').read_text(encoding='utf-8'))
        reply=json.loads((raw/f'reply-{i}.json').read_text(encoding='utf-8'))
        review=json.loads((raw/f'review-{i}.json').read_text(encoding='utf-8'))
        assert request['tool']==tool and reply['tool']==tool and reply['status']=='returned'
        texts=[block['text'] for block in reply['result']['content'] if block.get('type')=='text']
        images=[block for block in reply['result']['content'] if block.get('type')=='image']
        assert len(texts)==1 and len(images)==1
        meta=json.loads(texts[0])
        image_bytes=base64.b64decode(images[0]['data'],validate=True)
        assert image_bytes==(SOURCE/frame).read_bytes(),f'image bytes mismatch: {frame}'
        assert meta['task_success'] is None
        assert meta['source']=={'sequence':sequence,'observation_id':f'o{sequence}'}
        assert review['source_sequence']==sequence and review['observation_id']==f'o{sequence}'
        if tool=='interface_guarded_input':
            releases=meta['result']['execution']['releases']
            assert releases and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases)
        presented=[row for row in rows if row['kind']=='presentation_callbacks_completed' and row['attempt']==i]
        assert len(presented)==1 and presented[0]['reply_sha256']==digest(raw/f'reply-{i}.json')
        reviewed=[row for row in rows if row['kind']=='review_recorded' and row['attempt']==i]
        assert len(reviewed)==1 and reviewed[0]['source_sequence']==sequence
    exit_state=json.loads((raw/'exit.json').read_text(encoding='utf-8'))
    assert exit_state=={'code':0,'signal':None}
    run={'id':run_id,'status':'PASS','attempts':4,'tool_sequence':TOOLS,
         'input_dispatches':2,'observations':2,'source_frames':SEQUENCES,
         'source_bound_reviews':4,'fixture_release_receipts_verified':True,
         'task_success_from_interface':None,'relay_exit':exit_state,'raw_sha256':hashes}
    if run_id=='a02_20261005':
        policy=json.loads((raw/'caller-policy.json').read_text(encoding='utf-8'))
        assert policy=={'max_explicit_observations':2,'explicit_observe_calls':3,
          'accepted_explicit_observations':2,'refused_locally':1,
          'host_attempts_after_refusal':4,'stopped':'explicit observation budget exhausted'}
        run['explicit_observation_budget']=policy
    else:
        assert not (raw/'caller-policy.json').exists()
        run['explicit_observation_budget']='not configured in baseline A01'
    return run

def main():
    manifest=PKG/'SHA256SUMS'
    for line in manifest.read_text(encoding='ascii').splitlines():
        expected,rel=line.split('  ',1)
        assert digest(manifest.parent/rel)==expected,f'source/code hash mismatch: {rel}'
    for line in (PKG/'REPLAY_SHA256SUMS').read_text(encoding='ascii').splitlines():
        expected,rel=line.split('  ',1)
        assert digest(RAW_ROOT/rel)==expected,f'replay evidence hash mismatch: {rel}'
    runs=[audit_run(run_id) for run_id in RUNS]
    historical=json.loads((SOURCE/'audit.json').read_text(encoding='utf-8'))
    assert historical['task_success'] is True and historical['actual']==[222,440]
    result={'status':'PASS','classification':'offline current-primary-host composition replay',
      'runs':runs,'historical_independent_task_audit':{'success':historical['task_success'],'actual':historical['actual']},
      'scope':'Retained-image transport, caller choreography and a caller-selected observation-count cap only; no GUI, model/provider, independent perception judgment, live allocation, or causal benefit.'}
    (PKG/'REPLAY_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
