"""Audit frozen focus prompt pairs and report wrong answers without reruns."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 r=HERE/'results/focus-model-pair-01';plan=read(r/'plan.json');rows=[];args=None
 for n,h in plan['sources'].items():assert sha(HERE/n)==h
 for spec in plan['schedule']:
  d=r/spec['name'];rp=read(d/'plan.json');assert sha(r/(spec['name']+'.txt'))==spec['prompt_sha256']==rp['stdin_sha256']==sha(d/'prompt.txt')
  assert sha(HERE/spec['source'])==spec['source_sha256']
  assert sha(HERE.parent/'live_control/model_text_runner_v1.py')==rp['runner_sha256']
  if args is None:args=rp['args']
  assert args==rp['args'] and rp['requested_model']=='gpt-5.6-luna' and rp['requested_effort']=='low'
  raw=(d/'events.jsonl').read_bytes().splitlines(keepends=True);events=[json.loads(l) for l in raw];arrivals=[json.loads(l) for l in (d/'arrivals.jsonl').read_text().splitlines()]
  assert len(raw)==len(arrivals)
  for n,(line,a) in enumerate(zip(raw,arrivals)):assert a['line']==n and a['sha256']==hashlib.sha256(line).hexdigest() and a['bytes']==len(line)
  messages=[e['item'] for e in events if e['type']=='item.completed'];assert len(messages)==1 and messages[0]['type']=='agent_message'
  answer=json.loads(messages[0]['text']);usage=next(e['usage'] for e in events if e['type']=='turn.completed');process=read(d/'process.json');assert process['exit_code']==0
  wrong={k:{'expected':v,'actual':answer.get(k)} for k,v in spec['expected'].items() if type(answer.get(k))!=type(v) or answer.get(k)!=v}
  rows.append({'name':spec['name'],'correct':not wrong,'wrong_fields':wrong,'answer':answer,'usage':usage,'local_run_ms':(process['exited_ns']-process['started_ns'])/1e6,'stderr_bytes':(d/'stderr.txt').stat().st_size})
 report={'rows':rows,'all_answers_correct':all(x['correct'] for x in rows),'scope':'static known text-only pairs; full and view differ in explicit authority cue and omitted information; no isolated compression benefit, cost or live recovery proof','audit_sha256':sha(Path(__file__))}
 (r/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
