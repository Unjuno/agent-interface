"""Audit fixed full/compact prompts, raw model calls and token deltas."""
import hashlib,json,statistics
from pathlib import Path
from calc_proposal_schema_v1 import parse as parse_calc
from form_proposal_schema_v1 import parse as parse_form
from planner_evidence_v1 import present
H=Path(__file__).resolve().parent;R=H/'results/compact-evidence-decisions-01'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def recorded_path(value):
 value=str(value).replace('\\','/')
 return Path('/mnt/'+value[0].lower()+value[2:]) if len(value)>2 and value[1:3]==':/' else Path(value)
plan=read(R/'plan.json');runs=read(R/'runs.json');result=read(R/'result.json')
assert result=={'calls':16,'actions_executed':0,'all_predeclared_calls_retained':True} and len(runs)==16
for name,digest in plan['sources'].items():assert sha(H/name.replace('\\','/'))==digest
controls=read(H/'results/planner-evidence-controls-01/result.json')
for name,digest in controls['sources'].items():assert sha(H/name.replace('\\','/'))==digest
form=H/'results/checkpoint-recovery-form-01';calc=H/'results/checkpoint-decision-calc-01'
ft=read(form/'turns.json')[0];fl=read(form/'losses.json');ct=read(calc/'turns.json')
evidence={
 'form_unknown':(ft['feedback'],present(fl[0]['recovered']['state']['last_resolution'],recovered=True)),
 'form_verified':({'checkpoint_resolution':fl[1]['recovered']['state']['last_resolution'],'query_recovery':'one command-free read; no query resend'},present(fl[1]['recovered']['state']['last_resolution'],recovered=True)),
 'calc_unknown_dialog':(ct[1]['feedback'],present(ct[1]['feedback']['checkpoint_resolution'],phase_report=ct[0]['phases'],prior_steps=ct[0]['proposal']['steps'])),
 'calc_verified':({'checkpoint_resolution':ct[1]['checkpoint']['state']['last_resolution']},present(ct[1]['checkpoint']['state']['last_resolution']))}
form_prefix=(form/'prompt-1.txt').read_text(encoding='utf-8').split('Evidence: ')[0]
calc_prefix=(calc/'prompt-2.txt').read_text(encoding='utf-8').split('Evidence: ')[0]
prefix={n:(form_prefix if n.startswith('form_') else calc_prefix) for n in evidence}
replay=('Recorded fixed-image decision replay. No proposed action will execute. Treat the depicted state and supplied evidence as current. A VERIFIED saved checkpoint may request the schema\'s verify result; UNKNOWN cannot.\n')
summaries=[]
for cp in plan['cases']:
 name=cp['name'];directory=R/name;case=read(directory/'case.json');image=recorded_path(cp['image'])
 assert sha(image)==case['image_sha256']==cp['image_sha256']
 assert hashlib.sha256(prefix[name].encode()).hexdigest()==case['prefix_sha256']
 assert case['order']==cp['order'] and case['expected']==cp['expected']
 for mode,value in zip(('A','B'),evidence[name]):
  assert read(directory/f'evidence-{mode}.json')==value
  assert (directory/f'prompt-{mode}.txt').read_text(encoding='utf-8')==replay+prefix[name]+'Evidence: '+json.dumps(value)
  assert len(json.dumps(value,separators=(',',':')).encode())==cp['full_bytes' if mode=='A' else 'compact_bytes']
 subset=[row for row in runs if row['case']==name]
 assert [(row['index'],row['mode']) for row in subset]==list(enumerate(cp['order'],1))
 for row in subset:
  i,mode=row['index'],row['mode'];d=directory/f'model-{i}-{mode}';mp=read(d/'plan.json');process=read(d/'process.json')
  assert row['exit_code']==process['exit_code']==0 and 'parse_error' not in row
  assert mp['image_sha256']==case['image_sha256'] and mp['runner_sha256']==sha(H/'model_context_runner_v1.py')
  assert mp['instructions_sha256']==sha(H/'screenshot_responder_v1.txt')
  assert mp['requested_model']==plan['model'] and mp['requested_effort']==plan['effort'] and mp['instruction_mode']==plan['instruction_mode']
  assert (d/'prompt.txt').read_text(encoding='utf-8')==(directory/f'prompt-{mode}.txt').read_text(encoding='utf-8')
  raw=(d/'events.jsonl').read_bytes().splitlines(keepends=True);arr=[json.loads(line) for line in (d/'arrivals.jsonl').read_bytes().splitlines()]
  assert len(raw)==len(arr)==4
  for j,(line,a) in enumerate(zip(raw,arr)):assert a['line']==j and a['bytes']==len(line) and a['sha256']==hashlib.sha256(line).hexdigest()
  records=[json.loads(line) for line in raw]
  assert [event['type'] for event in records]==['thread.started','turn.started','item.completed','turn.completed'] and records[2]['item']['type']=='agent_message'
  proposal=parse_form(records[2]['item']['text'],'t000240') if row['domain']=='form' else parse_calc(records[2]['item']['text'])
  assert proposal==row['proposal'] and records[3]['usage']==row['usage']
  steps=proposal.get('steps',[]);saves=sum(step=={'op':'chord','modifier':'Control_L','key':'s'} for step in steps);returns=sum(step=={'op':'key','key':'Return'} for step in steps)
  assert saves==row['save_proposals'] and returns==row['return_proposals']
  if case['expected']=='act_exact_value_once':expected=proposal['kind']=='act' and sum(step=={'op':'text','text':'t000240'} for step in steps)==1 and returns==1
  elif case['expected']=='click_dialog_without_save':expected=proposal['kind']=='act' and len(steps)==1 and steps[0]['op']=='pointer_click' and saves==0
  elif row['domain']=='form':expected=proposal['kind']=='verify' and proposal['submission_received_visible'] is True
  else:expected=proposal['kind']=='verify' and [proposal['visible_A1'],proposal['visible_A2'],proposal['confirmation_dialog_visible']]==[480,192,False]
  assert expected==row['expected_decision'] is True
  row['runner_s']=(process['exited_ns']-process['started_ns'])/1e9
 modes={}
 for mode in ('A','B'):
  rows=[row for row in subset if row['mode']==mode];assert len(rows)==2
  inputs=[row['usage']['input_tokens'] for row in rows];assert len(set(inputs))==1
  modes[mode]={'calls':2,'expected_decisions':sum(row['expected_decision'] for row in rows),'kinds':[row['proposal']['kind'] for row in rows],'input_tokens':inputs,'cached_input_tokens':[row['usage']['cached_input_tokens'] for row in rows],'output_tokens':[row['usage']['output_tokens'] for row in rows],'runner_s':[row['runner_s'] for row in rows],'save_proposals':sum(row['save_proposals'] for row in rows)}
 full=statistics.mean(modes['A']['input_tokens']);compact=statistics.mean(modes['B']['input_tokens'])
 summaries.append({'case':name,'full_evidence_bytes':cp['full_bytes'],'compact_evidence_bytes':cp['compact_bytes'],'evidence_byte_reduction':cp['full_bytes']-cp['compact_bytes'],'full':modes['A'],'compact':modes['B'],'input_tokens_saved_per_call':full-compact,'input_token_reduction_percent':(full-compact)*100/full})
full_total=sum(sum(row['usage']['input_tokens'] for row in runs if row['case']==s['case'] and row['mode']=='A') for s in summaries)
compact_total=sum(sum(row['usage']['input_tokens'] for row in runs if row['case']==s['case'] and row['mode']=='B') for s in summaries)
assert all(s['full']['expected_decisions']==s['compact']['expected_decisions']==2 for s in summaries)
report={'scope':'16 fixed-image calls; two calls per evidence mode/case; no actions or live speed comparison','summaries':summaries,'full_input_tokens':full_total,'compact_input_tokens':compact_total,'input_tokens_saved':full_total-compact_total,'input_token_reduction_percent':(full_total-compact_total)*100/full_total,'mean_tokens_saved_per_call':(full_total-compact_total)/8,'all_expected_decisions':True,'raw_records_retained':True,'same_image_and_task_prompt_within_case':True,'served_identity_and_cost':'unavailable','cached_tokens_and_runner_duration':'reported but not causal metrics'}
(R/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
