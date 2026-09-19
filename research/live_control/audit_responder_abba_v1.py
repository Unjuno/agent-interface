"""Cross-episode comparison, after per-episode runtime replay audits."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE/'results/responder-abba-01'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(ROOT/'plan.json');runs=read(ROOT/'runs.json')
assert [(r['label'],r['mode']) for r in runs]==[tuple(x) for x in plan['order']]
for name,digest in plan['sources'].items():assert sha(HERE/name)==digest
rows=[];first_prompts=[];common_args=None
for run in runs:
 assert run['exit_code']==0
 root=HERE/'results'/run['label'];audit=read(root/'audit.json')
 assert audit['instruction_mode']==run['mode']
 assert audit['audit_sha256']==sha(HERE/'audit_responder_calc_v1.py')
 first_prompts.append((root/'prompt-1.txt').read_bytes())
 arrivals=[]
 for turn in audit['model_turns']:
  model=root/f"model-{turn['turn']}";p=read(model/'plan.json');args=p['args'];at=args.index('-C')
  flags=['-c','model_instructions_file='+json.dumps((HERE/'screenshot_responder_v1.txt').resolve().as_posix())] if run['mode']=='responder' else []
  if flags:
   assert args[at-len(flags):at]==flags
   assert p['instructions_sha256']==sha(HERE/'screenshot_responder_v1.txt')
  else:assert p['instructions_sha256'] is None
  normalized=args[:at-len(flags)]+args[at:]
  assert normalized[normalized.index('-C')-2:normalized.index('-C')]==['--disable','fast_mode']
  normalized[normalized.index('-i')+1]='<audited current episode image>'
  if common_args is None:common_args=normalized
  assert normalized==common_args
  process=read(model/'process.json')
  events=[json.loads(l) for l in (model/'events.jsonl').read_bytes().splitlines()]
  stamps=[json.loads(l) for l in (model/'arrivals.jsonl').read_bytes().splitlines()]
  assert [e['type'] for e in events]==['thread.started','turn.started','item.completed','turn.completed']
  times=[process['started_ns'],process['stdin_closed_ns']]+[a['received_ns'] for a in stamps]+[process['exited_ns']]
  assert times==sorted(times)
  arrivals.append((stamps[2]['received_ns']-process['started_ns'])/1e9)
 row={'label':run['label'],'instruction_mode':run['mode'],'model_calls':len(audit['model_turns']),
      'saves':audit['save_chords'],'capture_to_evaluation_s':audit['linux_initial_capture_to_evaluation_ms']/1000,
      'supervisor_s':audit['supervisor_start_to_verified_exit_ms']/1000,
      'proposal_arrival_s':arrivals,'runner_total_s':sum(t['runner_wall_ms'] for t in audit['model_turns'])/1000,
      'usage':{k:sum(t['usage'][k] for t in audit['model_turns']) for k in ['input_tokens','cached_input_tokens','output_tokens']},
      'events':audit['events'],'frames':audit['exact_frames'],'append_records':audit['append_records'],'socket_calls':audit['socket_calls']}
 rows.append(row)
assert all(p==first_prompts[0] for p in first_prompts)
report={'scope':'requested modes only; unequal model actions/cache possible; two episodes per mode; descriptive not causal',
        'identical_first_prompts':True,'rows':rows}
(ROOT/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
