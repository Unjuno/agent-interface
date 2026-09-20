import base64,hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
from openpyxl import load_workbook
root=Path(__file__).resolve().parent;run=root/'allocation/run'
manifest=json.loads((root/'manifest.json').read_bytes())
for name,digest in manifest.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
rows=[json.loads(x) for x in (root/'responses.jsonl').read_bytes().splitlines()]
assert [r['id'] for r in rows]==list(range(1,10))
assert all(r['status']=='returned' and not r['result']['isError'] for r in rows)
meta=[json.loads(r['result']['content'][0]['text']) for r in rows];images=0
for row,m in zip(rows,meta):
    for b in row['result']['content']:
        if b['type']=='image':
            raw=base64.b64decode(b['data'],validate=True);ref=m['image_reference']
            assert raw==(run/ref['relative_path']).read_bytes()
            assert hashlib.sha256(raw).hexdigest()==ref['sha256'];images+=1
assert images==7
for stage in range(1,8):
    raw=(run/f'request-{stage}.json').read_bytes();request=json.loads(raw)
    source=json.loads((run/f'source-{stage}.json').read_bytes())
    reply=json.loads((run/f'reply-{stage}.json').read_bytes())
    assert request['source_sequence']==source['sequence']
    assert reply['decision_sha256']==hashlib.sha256(raw).hexdigest()
    if stage<7:
        cont=meta[stage]['continuation'];next_source=(run/f'source-{stage+1}.json').read_bytes()
        assert cont['stage']==stage+1 and cont['status']=='source_available'
        assert cont['source_sha256']==hashlib.sha256(next_source).hexdigest()
        assert cont['source_sequence']==meta[stage]['image_reference']['sequence']
actions=json.loads((run/'actions.json').read_bytes())
assert [a['stage'] for a in actions]==[1,2,3,5]
assert actions[1]['feedback']['status']=='needs_review'
review=actions[1]['window_review']
assert review['status']=='reviewed' and review['previous_window_id']!=review['requested_window_id']
for stage in (4,6):
    observation=json.loads((run/f'reply-{stage}.json').read_bytes())['observation_only']
    assert observation['input_dispatched'] is False and observation['captures']==1
final=meta[7]['receipt']['native_result']
assert final['status']=='finished' and final['evaluation']['success'] is True
assert all(v['success'] for v in final['evaluation']['applications'].values())
assert final['cleanup']['status']=='completed'
assert meta[8]['allocation']['status']=='terminal' and meta[8]['allocation']['returncode']==0
assert all(m['allocation']['pid']==21707 for m in meta)
rect=next(n for n in ET.parse(run/'shape.svg').iter() if n.tag.endswith('}rect'))
assert [float(rect.get(k)) for k in ('x','y','width','height')]==[62,50,40,30]
assert rect.get('transform') is None
workbook=load_workbook(run/'sheet.xlsx',data_only=True)
assert [workbook.active['A1'].value,workbook.active['A2'].value]==[244,185]
workbook.close()
assert not (run/'error.txt').exists()
print(json.dumps({'status':'TWO_APP_TASK_PASS','images':images,'input_programs':len(actions),'manifest_files':len(manifest)}))
