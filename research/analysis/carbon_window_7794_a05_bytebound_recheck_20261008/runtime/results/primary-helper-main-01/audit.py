import base64,hashlib,importlib.util,json,sys,zipfile
from pathlib import Path
def require(value,message):
 if not value:raise ValueError(message)
def read(path):return json.loads(path.read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def audit(root):
 trial=root/'results-local/primary-helper-use-main-01';host=trial/'host';plan=read(trial/'PLAN.json')
 require(plan['source']=='d8ec4e2add9ba3aa9688486c175e003c73e54532','source')
 for name,digest in plan['hashes'].items():require(sha((trial/name).read_bytes())==digest,'frozen '+name)
 require((trial/'host-bundle/primary_caller.mjs').read_bytes()==(root/'runtime/host_v1/primary_caller.mjs').read_bytes(),'exact exported helper')
 manifest=read(trial/'host-bundle/HOST_MANIFEST.json')
 for entry in manifest['files']:require(sha((trial/'host-bundle'/entry['path']).read_bytes())==entry['sha256'],'host export bytes')
 with zipfile.ZipFile(trial/'runtime.pyz') as archive:
  build=json.loads(archive.read('BUILD.json'));require(build['source_revision']==plan['source'],'portable source')
  for entry in build['source_files']:require(sha(archive.read(entry['path']))==entry['sha256'],'portable module')
 require(len(list(host.glob('request-*.json')))==len(list(host.glob('reply-*.json')))==6,'inventory')
 requests=[read(host/f'request-{i}.json') for i in range(1,7)];replies=[read(host/f'reply-{i}.json') for i in range(1,7)]
 require([r['tool'] for r in requests]==['interface_guarded_observe','interface_guarded_mint','interface_guarded_input','interface_guarded_mint','interface_guarded_input','interface_close'],'call order')
 for reply in replies:require(reply['status']=='returned' and reply['result']['isError'] is False,'no refusal')
 rows=[json.loads(next(c['text'] for c in reply['result']['content'] if c['type']=='text')) for reply in replies]
 require(requests[0]['arguments']=={},'guarded observation shape')
 for i in [1,3]:require(set(requests[i]['arguments'])=={'alias','source_sequence','point','region_size'} and rows[i]['status']=='minted','mint public shape')
 for i,interaction in [(2,'move'),(4,'click')]:
  args=requests[i]['arguments'];require(set(args)=={'alias','offset','interaction','tail','detail','observation_refs'} and args['interaction']==interaction and args['offset']==[12,19] and args['detail']=='brief' and args['observation_refs'] is True,'input public shape')
  require(rows[i]['status']=='completed','completed input');release=rows[i]['result']['execution']['releases'];require(release and all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in release),'neutral input')
 require(requests[3]['arguments']['source_sequence']==rows[2]['source']['sequence'] and requests[4]['arguments']['alias']==rows[3]['alias'],'explicit fresh grounding')
 programs=[read(p) for p in (trial/'session/server').glob('guarded-session-*/program-*.json')];require(len(programs)==2,'two programs')
 motion=next(p for p in programs if not any(op['op']=='pointer_button' for op in p['ops']));require([op['op'] for op in motion['ops']]==['focus','pointer_move','wait_update','release_all'],'pointer only')
 click=next(p for p in programs if any(op['op']=='pointer_button' for op in p['ops']));require(sum(op['op']=='pointer_button' and op['down'] is True for op in click['ops'])==1,'one press')
 for index in [1,3,5]:
  row=rows[index-1];blocks=[c for c in replies[index-1]['result']['content'] if c['type']=='image'];require(len(blocks)==1,'original image');data=base64.b64decode(blocks[0]['data'],validate=True);artifact=row['source']['native']['artifact'];relative=artifact['path'].split('/session/',1)[1]
  require(data==(trial/'session'/relative).read_bytes() and sha(data)==artifact['sha256'],'PNG byte identity');review=read(host/f'review-{index}.json');require(review['source_sequence']==row['source']['sequence'] and review['reply_sha256']==sha((host/f'reply-{index}.json').read_bytes()) and review['images'][0]['sha256']==sha(data),'review binding')
 events=[json.loads(line) for line in (trial/'session/fixture/events.jsonl').read_text().splitlines()];effect=read(trial/'session/independent-effect.json');saves=[e for e in events if e['kind']=='save']
 require(effect['events']==events and effect['save_count']==len(saves)==1 and saves[0]['count']==1 and saves[0]['monotonic_ns']>rows[2]['result']['execution']['ended_ns'],'independent save count')
 require(rows[5]['status']=='closed' and rows[5]['release']['verified'] is True and rows[5]['release']['keys_down']==[] and rows[5]['release']['buttons_down']==[],'neutral close')
 terminal=read(trial/'session/primary-terminal.json');require(terminal['primary_state']=={'stopped':None} and terminal['public_requests']==plan['calls_expected']==6 and terminal['extra_disk_previews']==0,'primary policy terminal')
 require(read(host/'exit.json')=={'code':0,'signal':None} and all(p['returncode'] is not None for p in read(trial/'session/cleanup.json')),'owned cleanup')
 check=root/'results-local/primary-caller-main-01';require(read(check/'red.json')['returncode']!=0 and read(check/'green.json')['returncode']==0 and 'pass 86' in (check/'green.stdout').read_text(),'host RED/green')
 require(read(check/'native.json')['returncode']!=0 and 'exists on disk, but not in' in (check/'native.stdout').read_text(),'precommit distribution failure retained')
 require(read(check/'native02.json')['returncode']==0 and read(check/'native02.json')['source']==plan['source'],'committed native exit');log=(check/'native02.stdout').read_text();require('Ran 337 tests' in log and 'Ran 156 tests' in log and log.count('\nOK')>=2,'native suites')
 spec=importlib.util.spec_from_file_location('retained_timing',root/'runtime/integration_checks/host_timing.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);timing=module.summarize(host);require(timing['timeline_status']=='complete','host timing')
 return {'source':plan['source'],'scoped_result':'PASS exported optional primary helpers; one Apply','calls':6,'images':3,'extra_disk_previews':0,'primary_stopped':False,'independent_save_count':1,'host_tests':86,'protocol_tests':337,'harness_tests':156,'time_partition':timing['time_partition'],'scope':'Main-specific known fixture usability; original six-task candidate evidence retained, no main six-task, speed, semantic latency, human tempo or token/cost claim.'}
if __name__=='__main__':print(json.dumps(audit(Path(sys.argv[1])),indent=2))
