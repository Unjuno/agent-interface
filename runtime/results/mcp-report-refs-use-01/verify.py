"""Read saved evidence only, without extraction or running archived code."""
import copy
import hashlib
import json
from pathlib import Path
import tarfile

root = Path(__file__).resolve().parent
manifest = json.loads((root/'manifest.json').read_text())
with tarfile.open(root/'evidence.tar.gz', 'r:gz') as archive:
    members = archive.getmembers()
    assert all(m.isfile() for m in members)
    assert len(members) == len(manifest)
    assert {m.name for m in members} == set(manifest)
    data = {m.name: archive.extractfile(m).read() for m in members}
for name, expected in manifest.items():
    assert hashlib.sha256(data[name]).hexdigest() == expected, name
read = lambda name: json.loads(data[name].decode('utf-8-sig'))
freeze = read('live/FREEZE.json')
for name, expected in freeze['sources'].items():
    assert hashlib.sha256(data['live/source/'+name]).hexdigest() == expected
assert hashlib.sha256(data['live/owner.py']).hexdigest() == freeze['owner_sha256']
first, plain = read('live/action-1-metadata.json'), read('live/action-2-metadata.json')
receipt = copy.deepcopy(first['receipt'])
assert receipt['schema'] == 'agent-interface/receipt-view-v3-report-ref'
assert receipt['report_reference'] == '/source/raw_report'
assert receipt['report'] == {'report_ref':'/source/raw_report'}
receipt['report'] = copy.deepcopy(receipt['source']['raw_report'])
receipt['schema'] = 'agent-interface/receipt-view-v1'
receipt.pop('report_reference')
receipt.pop('reference_scope')
assert receipt == plain['receipt']
assert first['outcome_summary'] == plain['outcome_summary']
assert first['outcome_summary']['input_release_verified'] is True
assert plain['operation_invoked'] is False
assert data['live/action-1.png'] == data['live/action-2.png']
before = {r['path'].replace('\\','/'):r['sha256'].lower() for r in read('live/before-lookup-hashes.json')}
after = {n.removeprefix('live/calls/'):hashlib.sha256(v).hexdigest()
         for n,v in data.items() if n.startswith('live/calls/')}
assert before == after and len(after) == 6
assert read('live/effect.json') == {'saved':True,'text':'refs-83'}
assert read('live/primary-declaration.json')['primary_complete'] is True
print(json.dumps({'status':'PASS_SAVED_EVIDENCE_CONSISTENCY','files':len(data),
                  'scope':'archive only; no GUI execution or independent adoption audit'}))
