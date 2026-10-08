import base64,hashlib,json
from pathlib import Path
def require(value,message):
 if not value:raise ValueError(message)
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def audit(root):
 public=root/'results-local/activation-review-main-public-01';freeze=read(public/'FREEZE.json')
 for name,digest in freeze['hashes'].items():require(sha(root/name)==digest,'public frozen '+name)
 case=public/'case';metas={};images=[];exchanges=[]
 expected=['interface_guarded_observe','interface_guarded_mint','interface_guarded_input','interface_clock','interface_guarded_activate_window','interface_guarded_mint','interface_guarded_input','interface_close']
 for i,tool in enumerate(expected,1):
  row=read(case/f'exchange-{i}.json');exchanges.append(row)
  require(row['index']==i and row['tool']==tool and row['ended_ns']>=row['started_ns'],'public exchange')
  meta=json.loads(next(c['text'] for c in row['reply']['content'] if c['type']=='text'));metas[i]=meta
  require(meta.get('task_success') is None,'no inferred task success')
  for block in (c for c in row['reply']['content'] if c['type']=='image'):
   images.append(i);artifact=meta['source']['native']['artifact'];data=base64.b64decode(block['data'],validate=True)
   require(hashlib.sha256(data).hexdigest()==artifact['sha256'],'exact image')
   require((case/'server'/meta['call_id']/'images'/Path(artifact['path']).name).read_bytes()==data,'retained image')
 require(images==[1,3,5,7],'public images')
 require(metas[3]['status']=='execution_failed' and metas[3]['result']['execution']['failed_op']==5 and 'outside guarded target before key press' in metas[3]['result']['execution']['error'],'actual focus stop')
 args=exchanges[4]['arguments'];combined=metas[5]
 require(args['review_after_activation'] is True and args['expires_at_ns']==metas[4]['monotonic_ns']+5_000_000_000 and args['source_sequence']==metas[3]['source']['sequence'],'explicit combined lineage')
 require(args['window_id']==metas[1]['session']['targets']['app'] and args['current_binding_revision']==0,'target/revision')
 require(combined['status']=='reviewed' and combined['result']['status']=='completed' and combined['result']['execution']['program_emissions']==0,'activation no editing')
 require(combined['session']['binding_revision']==1 and combined['session']['review_required'] is False and combined['source']==combined['review']['observation'],'fresh review source')
 require(exchanges[5]['arguments']['source_sequence']==combined['source']['sequence'] and exchanges[5]['arguments']['alias']!=exchanges[1]['arguments']['alias'],'fresh grounding')
 require(metas[7]['status']=='completed' and exchanges[6]['arguments']['alias']==exchanges[5]['arguments']['alias'],'fresh input')
 for i in [3,5,7]:
  releases=metas[i]['result']['execution']['releases'];require(bool(releases) and all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in releases),'neutral release')
 require(metas[8]['status']=='closed' and metas[8]['release']['verified'] is True,'public close')
 events=[json.loads(line) for line in (case/'fixture/events.jsonl').read_text().splitlines()]
 require(sum(e['kind']=='focus_transfer' for e in events)==1,'transfer journal')
 require([(e['role'],e['char']) for e in events if e['kind']=='key']==[('A','z')],'independent effects')
 score=read(case/'independent-effect.json');require(score=={'events':events,'A_text':'z','B_text':''},'score reconstruction')
 require(len(read(case/'cleanup.json'))==3 and all(type(p['returncode']) is int for p in read(case/'cleanup.json')),'public owned cleanup')
 require(read(root/'results-local/activation-review-main-01/red.json')['returncode']!=0,'RED')
 require(read(root/'results-local/activation-review-main-01/native-exit.json')['returncode']==0,'native exit')
 log=(root/'results-local/activation-review-main-01/native.stdout').read_text()
 require('Ran 332 tests' in log and 'Ran 148 tests' in log and log.count('\nOK')>=2,'native suites')
 return {'source':freeze['source'],'base':freeze['base'],'public_contract':'PASS_SCOPED','public_calls':8,'public_images':4,'public_task_effect':'A=z, B empty','model_trial':False,'native_protocol':332,'native_harness':148,'claims_excluded':['matched speed','semantic latency','human tempo','provider tokens/cost','whole candidate adoption']}
if __name__=='__main__':
 import sys
 print(json.dumps(audit(Path(sys.argv[1])),indent=2))
