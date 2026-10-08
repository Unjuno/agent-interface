import base64,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_bytes())
for name,h in manifest.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==h,name
plan=json.loads((root/'PLAN.json').read_bytes());hashes=[];images=0
for i,mode in enumerate(plan['order'],1):
    folder=root/str(i);run=folder/'allocation/run'
    rows=[json.loads(x) for x in (folder/'responses.jsonl').read_bytes().splitlines()]
    assert [r['id'] for r in rows]==list(range(1,len(rows)+1))
    assert all(not r['result']['isError'] for r in rows)
    meta=[json.loads(r['result']['content'][0]['text']) for r in rows]
    hashes.append(meta[0]['image_reference']['sha256'])
    for row,m in zip(rows,meta):
        for b in row['result']['content']:
            if b['type']=='image':
                raw=base64.b64decode(b['data'],validate=True);ref=m['image_reference']
                assert raw==(run/ref['relative_path']).read_bytes()
                assert hashlib.sha256(raw).hexdigest()==ref['sha256'];images+=1
    stages=1 if mode=='combined' else 2
    for stage in range(1,stages+1):
        raw=(run/f'request-{stage}.json').read_bytes();request=json.loads(raw)
        reply=json.loads((run/f'reply-{stage}.json').read_bytes())
        source=json.loads((run/f'source-{stage}.json').read_bytes())
        assert request['source_sequence']==source['sequence']
        assert reply['decision_sha256']==hashlib.sha256(raw).hexdigest()
        assert request['point']==plan['point']
    assert request['finish_after'] is True
    assert request['tail']==[{'op':'key_chord','keys':['Right'],'repeat':6},{'op':'key_chord','keys':['CTRL','s']}]
    assert request['interaction']==('click' if stages==1 else 'keyboard')
    if stages==2:
        first=json.loads((run/'request-1.json').read_bytes())
        assert first['tail']==[] and first['interaction']=='click'
        assert meta[1]['continuation']['source_sequence']==json.loads((run/'source-2.json').read_bytes())['sequence']
    assert reply['evaluation']['success'] is True and reply['cleanup']['status']=='completed'
    owner=meta[-1]['allocation'];assert owner['status']=='terminal' and owner['returncode']==0
    assert len({m['allocation']['pid'] for m in meta})==1
    rect=next(n for n in ET.parse(run/'shape.svg').iter() if n.tag.endswith('}rect'))
    assert [float(rect.get(k)) for k in ('x','y','width','height')]==[62,50,40,30]
    assert rect.get('transform') is None
assert len(set(hashes))==1 and images==10
print(json.dumps({'status':'ABBA_FOUR_PASSES_DISCREPANCY_NOT_REPRODUCED','images':images,'manifest_files':len(manifest)}))
