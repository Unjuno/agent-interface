import base64,hashlib,importlib.util,json,sys,zipfile
from pathlib import Path
def require(value,message):
 if not value:raise ValueError(message)
def read(path):return json.loads(path.read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def audit(root):
 trials=root/'results-local';trial=trials/'primary-combined-main-02';host=trial/'host';plan=read(trial/'PLAN.json')
 require(plan['source']=='ddc9bf5c438520baae4eac391e7c0f5e0f4af578','source')
 for name,digest in plan['hashes'].items():require(sha((trial/name).read_bytes())==digest,'frozen '+name)
 with zipfile.ZipFile(trial/'runtime.pyz') as archive:
  build=json.loads(archive.read('BUILD.json'));require(build['source_revision']==plan['source'],'portable source')
  for entry in build['source_files']:require(sha(archive.read(entry['path']))==entry['sha256'],'portable module '+entry['path'])
 require((trial/'host-bundle/relay_host.mjs').read_bytes()==(root/'runtime/host_v1/relay_host.mjs').read_bytes(),'host source')
 before=trials/'primary-combined-main-01'
 require(read(before/'session/primary-terminal.json')['outcome']=='STOP_MERGED_HOST_PRESENTATION_API_MISSING','first failure preserved')
 require(not list((before/'host').glob('request-*.json')),'first failure no dispatch')
 require(read(before/'session/independent-effect.json')['events']==[],'first failure no effects')
 for name,digest in read(before/'PLAN.json')['hashes'].items():require(sha((before/name).read_bytes())==digest,'predecessor frozen '+name)
 expected=['interface_guarded_observe','interface_guarded_mint','interface_guarded_input','interface_clock','interface_clock','interface_guarded_activate_window','interface_guarded_mint','interface_guarded_input','interface_close']
 require(len(list(host.glob('request-*.json')))==9 and len(list(host.glob('reply-*.json')))==9,'call inventory')
 requests=[read(host/f'request-{i}.json') for i in range(1,10)]
 replies=[read(host/f'reply-{i}.json') for i in range(1,10)]
 require([r['tool'] for r in requests]==expected,'call order')
 for r in replies:require(r['status']=='returned' and r['result']['isError'] is False,'returned reply')
 rows=[json.loads(next(c['text'] for c in r['result']['content'] if c['type']=='text')) for r in replies]
 failed=rows[2]['result']['execution'];require(rows[2]['status']=='execution_failed' and failed['failed_op']==5 and 'focused window is outside guarded target' in failed['error'],'focus stop')
 for row in [rows[2],rows[5],rows[7]]:
  releases=row['result']['execution']['releases'];require(releases and all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in releases),'neutral releases')
 activation=rows[5];require(activation['status']=='reviewed' and activation['feedback_status']=='review_returned' and activation['review']['binding_revision']==1,'activation review')
 args=requests[5]['arguments'];require(args['source_sequence']==6 and args['current_binding_revision']==0 and args['review_after_activation'] is True and args['window_id']==read(trial/'session/allocation.json')['target'],'activation binding')
 require(args['expires_at_ns']==rows[4]['monotonic_ns']+5_000_000_000,'fresh expiry')
 require(rows[6]['source_sequence']==7 and rows[7]['status']=='completed' and rows[7]['source']['binding_revision']==1,'fresh input')
 require(rows[8]['status']=='closed' and rows[8]['release']['verified'] is True and rows[8]['release']['keys_down']==[] and rows[8]['release']['buttons_down']==[],'public close')
 images=0
 for index,row in enumerate(rows,1):
  blocks=[c for c in replies[index-1]['result']['content'] if c['type']=='image']
  if index in [1,3,6,8]:
   require(len(blocks)==1,'image count');images+=1;data=base64.b64decode(blocks[0]['data'],validate=True)
   artifact=row['source']['native']['artifact'];relative=artifact['path'].split('/session/',1)[1]
   require(data==(trial/'session'/relative).read_bytes() and sha(data)==artifact['sha256'] and len(data)==artifact['bytes'],'original image bytes')
   receipt=read(host/f'review-{index}.json');require(receipt['source_sequence']==row['source']['sequence'] and receipt['reply_sha256']==sha((host/f'reply-{index}.json').read_bytes()) and receipt['images'][0]['sha256']==sha(data),'image review binding')
  else:require(not blocks,'text only')
 effects=read(trial/'session/independent-effect.json')
 raw_events=[json.loads(line) for line in (trial/'session/fixture/events.jsonl').read_text().splitlines()]
 require(effects['events']==raw_events,'independent effects raw journal')
 keys=[e for e in raw_events if e.get('kind')=='key']
 require(len(keys)==1 and keys[0]['role']=='A' and keys[0]['char']=='z' and effects['A_text']=='z' and effects['B_text']=='','independent effects')
 require(read(host/'exit.json')=={'code':0,'signal':None},'transport exit')
 require(all(p['returncode'] is not None for p in read(trial/'session/cleanup.json')),'owned processes terminal')
 terminal=read(trial/'session/primary-terminal.json');require(terminal['public_requests']==9 and terminal['extra_disk_previews']==1 and len(terminal['deviations'])==2,'deviations retained')
 require(plan['calls_expected']==8,'original planned count unchanged')
 test=trials/'presented-host-main-01';require(read(test/'red.json')['returncode']!=0 and read(test/'green.json')['returncode']==0 and read(test/'native-exit.json')['returncode']==0,'test exits')
 require('tests 40' in (test/'green.stdout').read_text() and 'fail 0' in (test/'green.stdout').read_text(),'host tests')
 log=(test/'native.stdout').read_text();require('Ran 335 tests' in log and 'Ran 148 tests' in log and log.count('\nOK')>=2,'native suites')
 spec=importlib.util.spec_from_file_location('retained_timing',root/'runtime/integration_checks/host_timing.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 timing=module.summarize(host);require(timing['timeline_status']=='complete' and timing['call_count']==9,'timing boundaries')
 return {'source':plan['source'],'first_failure':'STOP_MERGED_HOST_PRESENTATION_API_MISSING','scoped_task_effect':'A=z; B empty','personal_trial':True,'planned_calls':8,'actual_calls':9,'images':images,'extra_original_disk_previews':1,'host_tests':40,'native_protocol':335,'native_harness':148,'time_partition':timing['time_partition'],'claims_excluded':plan['claims_excluded'],'scope':'One known-fixture personal replication with declared deviations; no matched performance or human-tempo result.'}
if __name__=='__main__':print(json.dumps(audit(Path(sys.argv[1])),indent=2))
