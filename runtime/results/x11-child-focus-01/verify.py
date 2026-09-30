from pathlib import Path
import base64,hashlib,json,tarfile,xml.etree.ElementTree as ET
root=Path(__file__).resolve().parent
manifest=json.loads((root/'manifest.json').read_text())
with tarfile.open(root/'raw.tar.gz','r:gz') as tar:
 members={m.name:m for m in tar.getmembers()}
 assert set(members)==set(manifest['files'])
 def read(n):return tar.extractfile(members[n]).read()
 def data(n):return json.loads(read(n))
 for n,h in manifest['files'].items():assert hashlib.sha256(read(n)).hexdigest()==h,n
 assert data('results-local/x11-child-focus-live-01/disposition.json')['status']=='INCONCLUSIVE_SETUP_TRANSITION'
 for run in ('x11-child-focus-live-01','x11-child-focus-live-02'):
  rows=data('results-local/'+run+'/results.json');assert len(rows)==4
  for r in rows:
   assert 'error' not in r
   assert r['release']['verified'] and r['release']['keys_down']==r['release']['buttons_down']==[]
   assert r['fixture_close_returned']
 rows=data('results-local/x11-child-focus-live-02/results.json')
 for r in rows:
  if r['app']=='inkscape':
   assert r['before_focus']!=r['inspection']['window_id']
   assert r['inspection']['focus_path'][0]==r['before_focus']
   if r['route']=='baseline':assert r['after_focus']==r['inspection']['window_id']
   else:assert r['after_focus']==r['before_focus']
  else:assert r['before_focus']==r['after_focus']==r['inspection']['window_id']
 p='results-local/x11-child-focus-primary-01/'
 def rect(n):
  rows=ET.fromstring(read(p+n)).findall('{http://www.w3.org/2000/svg}rect');assert len(rows)==1
  r=rows[0];assert r.get('transform') is None
  return [float(r.get(k)) for k in ('x','y','width','height')]
 assert rect('original.svg')==[50,50,40,30]
 assert rect('saved-copy.svg')==[56,50,40,30]
 assert data(p+'evaluation.json')['success']
 sid=data(p+'initial-metadata.json')['session']['session_id']
 for label in ['initial']+[f'action-{i}' for i in range(1,10)]:
  assert data(p+label+'-metadata.json')['session']['session_id']==sid
  images=[x for x in data(p+label+'-response.json')['content'] if x['type']=='image']
  if images:assert len(images)==1 and base64.b64decode(images[0]['data'])==read(p+label+'.png')
 for n in (1,5,6,7):
  row=data(p+f'action-{n}-metadata.json')['outcome_summary']
  assert row['execution_status']=='completed' and row['input_release_verified']
 close=data(p+'action-9-metadata.json')
 assert close['status']=='closed' and close['release']['verified']
 assert close['release']['keys_down']==close['release']['buttons_down']==[]
 assert data(p+'primary-review.json')['runner_exit_code']==0
 assert data('results-local/x11-child-focus-check-01/result.json')['status']=='PASS'
 print('PASS:',len(members),'files; transitional results retained, child-focus distinction and saved SVG verified. No speed inference.')