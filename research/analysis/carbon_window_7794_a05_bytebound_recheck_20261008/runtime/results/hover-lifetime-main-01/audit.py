import base64,hashlib,importlib.util,json,sys,zipfile
from pathlib import Path
def require(value,message):
 if not value:raise ValueError(message)
def read(path):return json.loads(path.read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def audit(root):
 trial=root/'results-local/hover-lifetime-primary-01';host=trial/'host';plan=read(trial/'PLAN.json')
 require(plan['source']=='659177b7fab93fe00248516beabaa53c2836d8f2','source')
 for name,digest in plan['hashes'].items():require(sha((trial/name).read_bytes())==digest,'frozen '+name)
 with zipfile.ZipFile(trial/'runtime.pyz') as archive:
  build=json.loads(archive.read('BUILD.json'));require(build['source_revision']==plan['source'],'portable source')
  for entry in build['source_files']:require(sha(archive.read(entry['path']))==entry['sha256'],'portable module')
  for name in ['runtime/cli_v1/mcp_guarded.py','runtime/guarded_x11_v1/bridge.py']:require(archive.read(name)==(root/name).read_bytes(),'exact port source')
 expected=['interface_guarded_observe','interface_guarded_mint','interface_guarded_input','interface_guarded_input','interface_guarded_mint','interface_guarded_input','interface_close']
 require(len(list(host.glob('request-*.json')))==len(list(host.glob('reply-*.json')))==7,'inventory')
 requests=[read(host/f'request-{i}.json') for i in range(1,8)];replies=[read(host/f'reply-{i}.json') for i in range(1,8)]
 require([r['tool'] for r in requests]==expected,'call order')
 for index,reply in enumerate(replies):require(reply['status']=='returned' and reply['result']['isError']==(index==3),'expected refusal only')
 rows=[json.loads(next(c['text'] for c in reply['result']['content'] if c['type']=='text')) for reply in replies]
 for i in [1,4]:
  lifetime=rows[i]['lifetime'];require(lifetime['clock']=='time.monotonic_ns' and lifetime['authority_granted'] is False and lifetime['expires_ns']-lifetime['minted_ns']==300_000_000_000 and lifetime['capture_freshness_ms']==1500,'actual finite lifetime')
  mint=next((trial/'session/server').glob('guarded-session-*/mint-'+rows[i]['alias']+'.json'));require(read(mint)['expires_ns']==lifetime['expires_ns'],'stored expiry')
 move=rows[2]['result'];require(move['status']=='completed' and move['execution']['program_emissions']==1 and [g['stage'] for g in move['guard_checks']]==['before_admission','before_focus','before_move'],'guarded motion')
 refused=rows[3]['result'];require(rows[3]['status']=='refused' and refused['input_dispatched'] is False and 'execution' not in refused and len(refused['guard_checks'])==1 and refused['guard_checks'][0]['stage']=='before_admission' and refused['guard_checks'][0]['reason']=='region_pixels_missing','old reference refusal')
 require(requests[2]['arguments']['interaction']=='move' and requests[3]['arguments']['alias']==requests[2]['arguments']['alias'],'old-alias control')
 require(requests[4]['arguments']['source_sequence']==rows[3]['source']['sequence'] and requests[5]['arguments']['alias']==rows[4]['alias'] and rows[5]['status']=='completed','fresh grounding')
 for i in [2,5]:
  releases=rows[i]['result']['execution']['releases'];require(releases and all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in releases),'neutral input')
 programs=[read(p) for p in (trial/'session/server').glob('guarded-session-*/program-*.json')];require(len(programs)==2,'two dispatched programs only')
 motion=next(p for p in programs if not any(op['op']=='pointer_button' for op in p['ops']))
 require([op['op'] for op in motion['ops']]==['focus','pointer_move','wait_update','release_all'],'pointer-only program')
 click=next(p for p in programs if any(op['op']=='pointer_button' for op in p['ops']));require(sum(op['op']=='pointer_button' and op['down'] is True for op in click['ops'])==1,'one press')
 require(rows[6]['status']=='closed' and rows[6]['release']['verified'] is True and rows[6]['release']['keys_down']==[] and rows[6]['release']['buttons_down']==[],'neutral close')
 for index in [1,3,4,6]:
  row=rows[index-1];blocks=[c for c in replies[index-1]['result']['content'] if c['type']=='image'];require(len(blocks)==1,'original image')
  data=base64.b64decode(blocks[0]['data'],validate=True);artifact=row['source']['native']['artifact'];relative=artifact['path'].split('/session/',1)[1]
  require(data==(trial/'session'/relative).read_bytes() and sha(data)==artifact['sha256'],'PNG byte identity')
  review=read(host/f'review-{index}.json');require(review['source_sequence']==row['source']['sequence'] and review['reply_sha256']==sha((host/f'reply-{index}.json').read_bytes()) and review['images'][0]['sha256']==sha(data),'review binding')
 events=[json.loads(line) for line in (trial/'session/fixture/events.jsonl').read_text().splitlines()];effect=read(trial/'session/independent-effect.json')
 saves=[e for e in events if e['kind']=='save'];require(effect['events']==events and effect['save_count']==len(saves)==1 and saves[0]['count']==1,'independent save count')
 require(saves[0]['monotonic_ns']>move['execution']['ended_ns'],'no save during move')
 require(read(host/'exit.json')=={'code':0,'signal':None} and all(p['returncode'] is not None for p in read(trial/'session/cleanup.json')),'terminal cleanup')
 terminal=read(trial/'session/primary-terminal.json');require(terminal['public_requests']==plan['calls_expected']==7 and terminal['extra_disk_previews']==1,'complete counted trial')
 spec=importlib.util.spec_from_file_location('retained_timing',root/'runtime/integration_checks/host_timing.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);timing=module.summarize(host)
 require(timing['timeline_status']=='complete' and timing['call_count']==7,'timing boundaries')
 check=root/'results-local/hover-lifetime-main-01';require(read(check/'red.json')['returncode']!=0 and read(check/'green.json')['returncode']==read(check/'native.json')['returncode']==0,'test exits')
 log=(check/'native.stdout').read_text();require('Ran 337 tests' in log and 'Ran 156 tests' in log and log.count('\nOK')>=2,'full native suites')
 return {'source':plan['source'],'scoped_result':'PASS hover / stale refusal / fresh save once','personal_trial':True,'calls':7,'images':4,'extra_disk_previews':1,'saves':1,'protocol_tests':337,'harness_tests':156,'time_partition':timing['time_partition'],'move_send_to_reply_ms':timing['calls'][2]['send_to_reply_ms'],'scope':'Known Tk fixture, not matched speed, first useful feedback, semantic latency, human tempo or provider tokens/cost.'}
if __name__=='__main__':print(json.dumps(audit(Path(sys.argv[1])),indent=2))
