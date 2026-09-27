from pathlib import Path
import json,hashlib,tarfile
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
with tarfile.open(root/'raw.tar.gz','r:gz') as tar:
 members={m.name:m for m in tar.getmembers()};assert set(members)==set(manifest['files'])
 def read(n): return tar.extractfile(members[n]).read()
 def data(n): return json.loads(read(n))
 for n,h in manifest['files'].items(): assert hashlib.sha256(read(n)).hexdigest()==h
 decision=data('decision-3.json')['arguments']['decision'];assert decision=={'source_sequence':10,'interaction':'observe'}
 reply=data('allocation/run/reply-3.json');o=reply['observation_only']
 assert o['captures']==1 and o['input_dispatched'] is False and reply['authority_granted'] is False
 assert reply['observation']['sequence']==11
 names=[n for n in members if n.startswith('allocation/run/bridge/public-dispatch-')];assert len(names)==2
 for n in names:
  r=data(n)['result'];assert r['status']=='completed' and r['execution']['releases']
  assert all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in r['execution']['releases'])
 assert data('allocation/run/evaluation.json')['actual']==[839,862]
 assert data('allocation/run/evaluation.json')['success'] is True
 assert data('action-5-metadata.json')['allocation']['returncode']==0
 tools=read('tools.json').decode();assert 'To request a new frame' in tools
 print('PASS:',len(members),'files, one no-input fresh capture and two released dispatches')
