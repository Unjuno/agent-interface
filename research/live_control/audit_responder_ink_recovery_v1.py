"""Audit archived recovery choices without model or GUI calls."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;R=H/'results/responder-ink-recovery-01';S=H/'results/inkscape-lost-reply-01'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=read(R/'plan.json');runs=read(R/'runs.json')
assert [(r['case'],r['mode']) for r in runs]==[tuple(v) for v in p['order']]
for n,d in p['sources'].items():assert sha(H/n)==d
for n,d in p['evidence_sources'].items():assert sha(S/n)==d
rows=[]
for r in runs:
 d=R/f"{r['index']}-{r['case']}-{r['mode']}";plan=read(d/'plan.json');process=read(d/'process.json')
 assert process['exit_code']==r['exit_code']==0
 assert plan['instruction_mode']==r['mode'] and plan['runner_sha256']==sha(H/'model_context_runner_v1.py')
 assert plan['image_sha256']==sha(S/'runtime'/p['contexts'][r['case']]['image'])
 assert (d/'prompt.txt').read_text(encoding='utf-8')==(R/(r['case']+'.txt')).read_text(encoding='utf-8')
 assert plan['instructions_sha256']==(sha(H/'screenshot_responder_v1.txt') if r['mode']=='responder' else None)
 raw=(d/'events.jsonl').read_bytes().splitlines(keepends=True);arr=[json.loads(l) for l in (d/'arrivals.jsonl').read_bytes().splitlines()]
 assert len(raw)==len(arr)==4
 for n,(line,a) in enumerate(zip(raw,arr)):assert a['line']==n and a['sha256']==hashlib.sha256(line).hexdigest() and a['bytes']==len(line)
 e=[json.loads(l) for l in raw];assert [x['type'] for x in e]==['thread.started','turn.started','item.completed','turn.completed']
 assert e[2]['item']['type']=='agent_message';proposal=json.loads(e[2]['item']['text'])
 if r['case']=='uncertain':assert set(proposal)=={'kind','action_id','rationale'} and proposal['kind']=='read' and proposal['action_id']=='move-save'
 else:
  assert set(proposal)=={'kind','visible_x','visible_y','visible_width','visible_height','rationale'} and proposal['kind']=='verify'
  assert [proposal[k] for k in ['visible_x','visible_y','visible_width','visible_height']]==[88,50,40,30]
 assert isinstance(proposal['rationale'],str) and proposal['rationale']
 rows.append(dict(**r,proposal=proposal,usage=e[3]['usage'],runner_s=(process['exited_ns']-process['started_ns'])/1e9))
report={'scope':p['scope'],'rows':rows}
(R/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
