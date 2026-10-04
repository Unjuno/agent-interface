from __future__ import annotations
import base64, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
PKG=Path(__file__).resolve().parent
RAW=PKG/'replay_raw'/'a01_20261005'
SOURCE=ROOT/'research'/'live_control'/'results'/'recovery-assistant-01'
TOOLS=['interface_guarded_input','interface_guarded_observe',
       'interface_guarded_input','interface_guarded_observe']

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):
            h.update(block)
    return h.hexdigest()

def main():
    manifest=PKG/'SHA256SUMS'
    for line in manifest.read_text(encoding='ascii').splitlines():
        expected,rel=line.split('  ',1)
        assert digest(manifest.parent/rel)==expected, f'original evidence hash mismatch: {rel}'
    raw_files=sorted(p for p in RAW.iterdir() if p.is_file())
    hashes={p.name:digest(p) for p in raw_files}
    for line in (PKG/'REPLAY_SHA256SUMS').read_text(encoding='ascii').splitlines():
        expected,name=line.split('  ',1)
        assert digest(RAW/name)==expected, f'replay evidence hash mismatch: {name}'
    rows=[json.loads(line) for line in (RAW/'host-events.jsonl').read_text(encoding='utf-8').splitlines()]
    sends=[r for r in rows if r['kind']=='send_requested']
    assert [r['tool'] for r in sends]==TOOLS
    assert [r['attempt'] for r in sends]==[1,2,3,4]
    frames=['006.png','007.png','008.png','009.png']
    frame_sequences=[6,7,8,9]
    for i,(tool,frame,sequence) in enumerate(zip(TOOLS,frames,frame_sequences),1):
        request=json.loads((RAW/f'request-{i}.json').read_text(encoding='utf-8'))
        reply=json.loads((RAW/f'reply-{i}.json').read_text(encoding='utf-8'))
        review=json.loads((RAW/f'review-{i}.json').read_text(encoding='utf-8'))
        assert request['tool']==tool and reply['tool']==tool and reply['status']=='returned'
        text=[b['text'] for b in reply['result']['content'] if b.get('type')=='text']
        images=[b for b in reply['result']['content'] if b.get('type')=='image']
        assert len(text)==1 and len(images)==1
        meta=json.loads(text[0])
        image_bytes=base64.b64decode(images[0]['data'],validate=True)
        assert image_bytes==(SOURCE/frame).read_bytes(), f'image bytes mismatch: {frame}'
        assert meta['task_success'] is None
        assert meta['source']=={'sequence':sequence,'observation_id':f'o{sequence}'}
        assert review['source_sequence']==sequence and review['observation_id']==f'o{sequence}'
        if tool=='interface_guarded_input':
            releases=meta['result']['execution']['releases']
            assert releases and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases)
        matching=[r for r in rows if r['kind']=='presentation_callbacks_completed' and r['attempt']==i]
        assert len(matching)==1 and matching[0]['reply_sha256']==digest(RAW/f'reply-{i}.json')
        review_events=[r for r in rows if r['kind']=='review_recorded' and r['attempt']==i]
        assert len(review_events)==1 and review_events[0]['source_sequence']==sequence
    exit_state=json.loads((RAW/'exit.json').read_text(encoding='utf-8'))
    assert exit_state=={'code':0,'signal':None}
    historical=json.loads((SOURCE/'audit.json').read_text(encoding='utf-8'))
    assert historical['task_success'] is True and historical['actual']==[222,440]
    result={'status':'PASS','classification':'offline current-primary-host composition replay',
      'attempts':4,'tool_sequence':TOOLS,'input_dispatches':2,'observations':2,
      'source_frames':frame_sequences,'source_bound_reviews':4,
      'fixture_input_release_receipts_verified':True,'task_success_from_interface':None,
      'historical_independent_task_audit':{'success':historical['task_success'],'actual':historical['actual']},
      'relay_exit':exit_state,'raw_sha256':hashes,
      'scope':'Retained-image transport and caller choreography only; no GUI, model/provider, independent perception judgment, live allocation, or causal benefit.'}
    (PKG/'REPLAY_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
