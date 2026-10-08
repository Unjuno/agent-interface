"""Audit fixed-image A/B prompts, raw model calls and decision classifications."""
import hashlib,json,statistics
from pathlib import Path
from phased_outcome_v2 import feedback
from calc_proposal_schema_v1 import parse
H=Path(__file__).resolve().parent;R=H/'results/outcome-decisions-01'
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
plan=read(R/'plan.json');runs=read(R/'runs.json');result=read(R/'result.json')
assert len(runs)==result['calls']==12
for n,digest in plan['sources'].items():assert sha(H/n)==digest
expected=[(name,i,mode) for name,label,index,order in plan['order'] for i,mode in enumerate(order,1)]
assert [(r['case'],r['index'],r['mode']) for r in runs]==expected
summaries=[]
for name,label,index,order in plan['order']:
 case=R/name;case_plan=read(case/'case.json');source=H/'results'/label;rows=read(source/'turns.json')
 assert case_plan['turns_sha256']==sha(source/'turns.json')
 image=source/'runtime'/Path(rows[index]['source']['image']).name
 assert sha(image)==case_plan['image_sha256']
 assert sha(source/f'prompt-{index+1}.txt')==case_plan['original_prompt_sha256']
 a=read(case/'feedback-A.json');b=read(case/'feedback-B.json')
 assert a==rows[index]['feedback'] and b==feedback(a,rows[index-1]['phases'])
 assert b['resolution']==a['resolution'] and set(b)==set(a)|{'execution_outcome'}
 assert all(b[k]==v for k,v in a.items() if k!='phase_status')
 assert b['execution_outcome']['application_effect'].startswith('unknown')
 prefix='Recorded decision replay: propose the next step for the depicted state as if it were current. No action will execute.\n'+(source/f'prompt-{index+1}.txt').read_text(encoding='utf-8').split('Evidence: ')[0]
 for mode,encoded in [('A',a),('B',b)]:
  assert (case/f'prompt-{mode}.txt').read_text(encoding='utf-8')==prefix+'Evidence: '+json.dumps(encoded)
 args=None
 for row in [r for r in runs if r['case']==name]:
  i,mode=row['index'],row['mode'];d=case/f'model-{i}-{mode}';model_plan=read(d/'plan.json');process=read(d/'process.json')
  assert row['exit_code']==process['exit_code']==0 and 'parse_error' not in row
  assert model_plan['image_sha256']==case_plan['image_sha256']
  assert model_plan['runner_sha256']==sha(H/'model_context_runner_v1.py') and model_plan['instructions_sha256']==sha(H/'screenshot_responder_v1.txt')
  assert model_plan['requested_model']=='gpt-5.6-luna' and model_plan['requested_effort']=='low' and model_plan['instruction_mode']=='responder'
  if args is None:args=model_plan['args']
  else:assert args==model_plan['args']
  assert (d/'prompt.txt').read_text(encoding='utf-8')==(case/f'prompt-{mode}.txt').read_text(encoding='utf-8')
  raw=(d/'events.jsonl').read_bytes().splitlines(keepends=True);arrivals=[json.loads(l) for l in (d/'arrivals.jsonl').read_bytes().splitlines()]
  assert len(raw)==len(arrivals)==4
  for j,(line,arrival) in enumerate(zip(raw,arrivals)):assert arrival['line']==j and arrival['sha256']==hashlib.sha256(line).hexdigest() and arrival['bytes']==len(line)
  records=[json.loads(l) for l in raw]
  assert [e['type'] for e in records]==['thread.started','turn.started','item.completed','turn.completed']
  assert records[2]['item']['type']=='agent_message'
  proposal=parse(records[2]['item']['text']);assert proposal==row['proposal'] and records[3]['usage']==row['usage']
  saves=sum(s=={'op':'chord','modifier':'Control_L','key':'s'} for s in proposal.get('steps',[]));assert saves==row['save_proposals']
  verifies=proposal['kind']=='verify' and [proposal['visible_A1'],proposal['visible_A2'],proposal['confirmation_dialog_visible']]==[480,192,False]
  assert verifies==row['goal_verification_requested']
  assert row['premature_goal_verification']==(verifies and name!='post_confirmation')
  row['runner_s']=(process['exited_ns']-process['started_ns'])/1e9
 for mode in ['A','B']:
  subset=[r for r in runs if r['case']==name and r['mode']==mode];assert len(subset)==2
  summaries.append({'case':name,'mode':mode,'calls':len(subset),
   'kinds':[r['proposal']['kind'] for r in subset],
   'goal_verification_requests':sum(r['goal_verification_requested'] for r in subset),
   'save_proposals':sum(r['save_proposals'] for r in subset),
   'premature_goal_verifications':sum(r['premature_goal_verification'] for r in subset),
   'mean_input_tokens':statistics.mean(r['usage']['input_tokens'] for r in subset),
   'cached_input_tokens':[r['usage']['cached_input_tokens'] for r in subset],
   'output_tokens':[r['usage']['output_tokens'] for r in subset],
   'mean_runner_s':statistics.mean(r['runner_s'] for r in subset)})
report={'scope':'12 fixed-case proposals; no live inputs or task-speed measurement',
        'summaries':summaries,'served_identity_and_cost':'unavailable',
        'source_hashes_verified':True,'same_image_and_prefix_within_case':True,
        'model_received_saved_oracle':False,'raw_records_retained':True}
(R/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
