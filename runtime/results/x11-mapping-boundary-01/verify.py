"""Check retained engineering bytes/data, without extraction, imports or GUI replay."""
from pathlib import Path
import hashlib,json,re,zipfile,io
p=Path(__file__).resolve().parent
m=json.loads((p/'manifest.json').read_text());metrics=json.loads((p/'metrics.json').read_text())
def need(condition,message):
 if not condition:raise SystemExit('FAIL: '+message)
raw=(p/m['archive']).read_bytes();need(hashlib.sha256(raw).hexdigest()==m['archive_sha256'],'archive hash')
z=zipfile.ZipFile(io.BytesIO(raw)); names=z.namelist()
need(len(names)==len(set(names)) and set(names)=={x['path'] for x in m['files']},'exact archive closure')
for x in m['files']:
 data=z.read(x['path']);need(len(data)==x['bytes'] and hashlib.sha256(data).hexdigest()==x['sha256'],'member '+x['path'])
load=lambda name:json.loads(z.read(name))
old=load('red/rows.json');need([x['effect']['text'] for x in old]==['a_','a','a='] and all(x['result']['status']=='completed' for x in old),'baseline wrong native effects')
need(not load('green/decision.json')['candidate_boundary_pass'] and all(x['result']['status']=='execution_failed' for x in load('green/rows.json')),'rejected notification-only candidate')
for trial in ('green-02','packaged-green-01'):
 rows=load(trial+'/rows.json');need(load(trial+'/decision.json')['candidate_boundary_pass'],'matrix decision')
 need(rows[0]['effect']=={'saved':True,'text':'a_'} and rows[0]['result']['status']=='completed','stable exact effect')
 for row in rows[1:]:
  ex=row['result']['execution'];need(row['result']['status']=='execution_failed' and ex['failed_op']==7 and ex['completed_ops']==list(range(7)) and row['effect'] is None,'stopped suffix')
 for row in rows:
  ex=row['result']['execution'];rel=ex['releases'][-1];need(rel['verified'] and not rel['keys_down'] and not rel['buttons_down'],'release receipt')
  cleanup=load(trial+'/'+row['name']+'/cleanup.json');need(cleanup['app_exit'] is not None and all(x is not None for x in cleanup['children']),'actual cleanup exits')
  if trial=='packaged-green-01':need(len(row['independent_keymap'])==32 and not any(row['independent_keymap']) and not row['independent_buttons'] & ((1<<8)|(1<<9)|(1<<10)),'independent neutral input')
env=load('packaged-green-01/environment.json');need('agent-interface-runtime.pyz/runtime/backends/x11_v1/backend.py' in env['backend_file'],'actual packaged import')
artifact=z.read('packaged/agent-interface-runtime.pyz');build=json.loads(zipfile.ZipFile(io.BytesIO(artifact)).read('BUILD.json'));need(build['source_revision']==metrics['packaged_revision'],'packaged revision')
for suite,n in [('protocol',324),('harness',141)]:
 text=z.read('native-checks-02/'+suite+'.stderr.log').decode();need(re.search(r'Ran '+str(n)+r' tests',text) is not None and text.rstrip().endswith('OK'),'native '+suite)
need(load('native-checks-02/result.json')['status']=='PASS' and load('native-checks-01/result.json')['status']=='FAIL','retained failed/final native checks')
final=load('live-final-01/result.json');need(final['tests']==54 and final['passed'] and final==metrics['live_final'],'final GUI counts')
for i in range(1,4):need(load(f'control-candidate-v2-{i:02}/result.json')['passed'],'candidate control')
need(not load('control-baseline-v2-02/result.json')['passed'] and load('control-baseline-v2-02/result.json')['failures']==1,'baseline instability retained')
for label in ('live-green','live-green-02','live-green-03'):need(not load(label+'/result.json')['passed'],'prior GUI failure retained')
print(json.dumps({'status':'PASS_RETAINED_MAPPING_BOUNDARY_ENGINEERING','files':len(names),'packaged_revision':metrics['packaged_revision'],'scope':'Exact bytes and selected data; not GUI replay, frozen formal result, speed, tokens or general XKB/IME support.'}))
