"""Read retained bytes only; no extraction, process launch, or GUI input."""
import hashlib,json,tarfile,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
with tarfile.open(root/'evidence.tar.gz') as t:
    members=t.getmembers()
    assert all(m.isfile() for m in members)
    assert len(members)==len(manifest)==len({m.name for m in members})
    data={m.name:t.extractfile(m).read() for m in members}
assert {k:hashlib.sha256(v).hexdigest() for k,v in data.items()}==manifest
prefix='integrated-inkscape-02/'
def read(name):return json.loads(data[prefix+name])
failed=json.loads(data['integrated-inkscape-01/initial-metadata.json'])
assert failed['allocation']['returncode']==1
assert b'ModuleNotFoundError' in data['integrated-inkscape-01/allocation/stderr.log']
request=read('action-2-request.json')['arguments']['decision']
assert request['finish_after'] is True
receipt=read('action-2-metadata.json')['receipt']['native_result']
assert receipt['status']=='finished' and receipt['evaluation']['success'] is True
assert receipt['action']['feedback']['status']=='matched'
assert receipt['action']['result']['execution']['releases'][-1]['verified'] is True
assert read('action-3-metadata.json')['allocation']['returncode']==0
rect=ET.fromstring(data[prefix+'allocation/run/shape.svg']).find('.//{http://www.w3.org/2000/svg}rect')
assert rect is not None
assert [float(rect.get(k)) for k in ('x','y','width','height')]==[54,50,40,30]
assert rect.get('transform') is None
m=read('measurements.json'); a=read('action-1-timing.json'); b=read('action-2-timing.json')
assert m['observe_to_finish_seconds']==(b['end_ns']-a['start_ns'])/1e9
assert m['input_finish_sdk_ms']==(b['end_ns']-b['start_ns'])/1e6
ci=json.loads(data['integrated-main-ci-01/result.json'])
assert ci['status']=='PASS' and all(s['returncode']==0 for s in ci['suites'])
print(f'PASS: {len(data)} member hashes, retained startup failure, terminal outcome, SVG and timings. Not a performance replication.')
