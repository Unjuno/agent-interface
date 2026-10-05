"""Predeclared fixed-case A/B decision replay; never executes model actions."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
from phased_outcome_v2 import feedback
from calc_proposal_schema_v1 import parse
H=Path(__file__).resolve().parent;R=H/'results/outcome-decisions-01';R.mkdir(exist_ok=False)
def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
specs=[('post_confirmation','sampled-effect-calc-02',2,['A','B','B','A']),
       ('visible_confirmation','sampled-effect-calc-02',1,['B','A','A','B']),
       ('preinput_refusal','shared-phased-calc-01',2,['A','B','B','A'])]
sources=[Path(__file__),H/'phased_outcome_v2.py',H/'calc_proposal_schema_v1.py',H/'model_context_runner_v1.py',H/'screenshot_responder_v1.txt']
plan={'scope':'archived decision replay, no runtime or input; A original feedback, B typed program outcome; no saved-file oracle supplied',
      'order':specs,'sources':{str(p.relative_to(H)):sha(p) for p in sources},
      'model':'gpt-5.6-luna','effort':'low','instruction_mode':'responder',
      'primary':'next-decision kind and additional Save proposals; dialog/incorrect-value verification controls',
      'limits':'two calls per condition per case, cache/served identity unverified, no live speed or reliability claim'}
dump(R/'plan.json',plan);runs=[]
for name,label,index,order in specs:
 source=H/'results'/label;rows=json.loads((source/'turns.json').read_text(encoding='utf-8'))
 current=rows[index];previous=rows[index-1];case=R/name;case.mkdir()
 original=current['feedback'];typed=feedback(original,previous['phases'])
 raw_prompt=(source/f'prompt-{index+1}.txt').read_text(encoding='utf-8');prefix=raw_prompt.split('Evidence: ')[0]
 prefix='Recorded decision replay: propose the next step for the depicted state as if it were current. No action will execute.\n'+prefix
 image=source/'runtime'/Path(current['source']['image']).name
 dump(case/'case.json',{'source_episode':label,'row_index':index,'turns_sha256':sha(source/'turns.json'),
                       'image':str(image),'image_sha256':sha(image),
                       'original_prompt_sha256':sha(source/f'prompt-{index+1}.txt'),
                       'scope':'only feedback representation differs within this case'})
 for mode,evidence in [('A',original),('B',typed)]:
  dump(case/f'feedback-{mode}.json',evidence)
  (case/f'prompt-{mode}.txt').write_text(prefix+'Evidence: '+json.dumps(evidence),encoding='utf-8')
 for i,mode in enumerate(order,1):
  model_dir=case/f'model-{i}-{mode}';begin=time.perf_counter_ns()
  print(json.dumps({'started':name,'index':i,'mode':mode}),flush=True)
  proc=subprocess.run([sys.executable,str(H/'model_context_runner_v1.py'),r'C:\Program Files\nodejs\node.exe',
      str(Path.home()/'AppData/Roaming/npm/node_modules/@openai/codex/bin/codex.js'),str(image),str(case/f'prompt-{mode}.txt'),str(H.parent.parent),str(model_dir),'responder'],capture_output=True,timeout=90)
  (case/f'runner-{i}-stdout.txt').write_bytes(proc.stdout);(case/f'runner-{i}-stderr.txt').write_bytes(proc.stderr)
  record={'case':name,'index':i,'mode':mode,'begin_ns':begin,'end_ns':time.perf_counter_ns(),'exit_code':proc.returncode}
  if proc.returncode==0:
   try:
    events=[json.loads(l) for l in (model_dir/'events.jsonl').read_text(encoding='utf-8').splitlines()]
    items=[e['item'] for e in events if e['type']=='item.completed']
    assert len(items)==1 and items[0]['type']=='agent_message'
    proposal=parse(items[0]['text']);record['proposal']=proposal;record['usage']=events[-1]['usage']
    saves=sum(s=={'op':'chord','modifier':'Control_L','key':'s'} for s in proposal.get('steps',[]))
    record['save_proposals']=saves
    record['goal_verification_requested']=proposal['kind']=='verify' and [proposal['visible_A1'],proposal['visible_A2'],proposal['confirmation_dialog_visible']]==[480,192,False]
    record['premature_goal_verification']=record['goal_verification_requested'] and name!='post_confirmation'
   except Exception as error:record['parse_error']={'type':type(error).__name__,'detail':str(error)}
  runs.append(record);dump(R/'runs.json',runs)
  print(json.dumps({'finished':name,'index':i,'mode':mode,'kind':record.get('proposal',{}).get('kind'),'save_proposals':record.get('save_proposals'),'error':record.get('parse_error')}),flush=True)
dump(R/'result.json',{'calls':len(runs),'scope':'all predeclared calls retained, no action executed, no per-condition retry'})
