from pathlib import Path
import base64,hashlib,json,tarfile,xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
with tarfile.open(root/'raw.tar.gz','r:gz') as tar:
 members={m.name:m for m in tar.getmembers()}
 assert set(members)==set(manifest['files'])
 def read(n):return tar.extractfile(members[n]).read()
 def data(n):return json.loads(read(n))
 def rect(n):
  tree=ET.fromstring(read(n));rows=tree.findall('{http://www.w3.org/2000/svg}rect');assert len(rows)==1
  r=rows[0];assert r.get('transform') is None
  return [float(r.get(k)) for k in ('x','y','width','height')]
 for n,h in manifest['files'].items():assert hashlib.sha256(read(n)).hexdigest()==h,n
 for suffix,last,dispatches in [('01',10,[1,8]),('02',7,[1,5]),('03',9,[1,5,6,7])]:
  p='results-local/public-owned-inkscape-primary-'+suffix+'/'
  assert rect(p+'original.svg')==[50,50,40,30]
  ev=data(p+'evaluation.json');assert ev['success']==(suffix!='02')
  if suffix=='02':
   assert p+'saved-copy.svg' not in members
   assert rect(p+'wrong-name-saved.svg')==[56,50,40,30]
  else:assert rect(p+'saved-copy.svg')==[56,50,40,30]
  sid=data(p+'initial-metadata.json')['session']['session_id']
  for label in ['initial']+[f'action-{n}' for n in range(1,last+1)]:
   assert data(p+label+'-metadata.json')['session']['session_id']==sid
   images=[b for b in data(p+label+'-response.json')['content'] if b['type']=='image']
   if images:
    assert len(images)==1
    assert base64.b64decode(images[0]['data'])==read(p+label+'.png')
  for n in dispatches:
   r=data(p+f'action-{n}-metadata.json')['outcome_summary']
   assert r['execution_status']=='completed' and r['input_release_verified']
  end=data(p+f'action-{last}-metadata.json')
  assert end['status']=='closed' and end['release']['verified']
  assert end['release']['keys_down']==end['release']['buttons_down']==[]
  assert data(p+'primary-review.json')['runner_exit_code']==0
  assert data(p+'fixture-cleanup.json')['session_close_returned']
  if suffix=='01':
   assert data(p+'action-4-metadata.json')['input_dispatched'] is False
   assert data(p+'action-4-timing.json')['start_ns']>data(p+'action-2-metadata.json')['expires_at_ns']
  else:
   r=data(p+'action-2-metadata.json');assert r['input_dispatched'] is False and r['authority_granted'] is False
   assert r['observation_report']['input_dispatched'] is False
   artifact=r['observation_report']['observation']['artifact']
   assert hashlib.sha256(read(p+'action-2.png')).hexdigest()==artifact['sha256']
   assert r['session']['targets']==data(p+'initial-metadata.json')['session']['targets']
   assert data(p+'action-3-request.json')['arguments']['review_id']==r['review_id']
 assert data('results-local/target-image-native-check-01/result.json')['status']=='PASS'
 print('PASS:',len(members),'files; all three outcomes, delivered images, explicit selection, SVG values and lifecycle. No speed inference.')