"""Predeclared fresh-session ABBA, no per-condition retry or selected rerun."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
root=HERE/'results/context-abba-01';root.mkdir(exist_ok=False)
order=[('context-abba-1-full','full'),('context-abba-2-view','view'),('context-abba-3-view','view'),('context-abba-4-full','full')]
plan={'order':order,'seed':238,'model':'gpt-5.6-luna','effort':'low','max_turns':5,
      'scope':'same supervisor/runtime/prompt and last outcome; full versus known-terminal presentation omitting historical timing/opaque IDs; unknown schema falls back full',
      'metrics':['independent saved task success','model turns','save chords','input/cached/output tokens','initial capture to evaluation','supervisor wall'],
      'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['run_context_abba_v1.py','context_calc_supervisor_v1.py','context_calc_driver_v1.py','calc_proposal_schema_v1.py','model_pair_runner_v1.py','terminal_context_v1.py']}}
(root/'plan.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8');runs=[]
for label,mode in order:
    begin=time.perf_counter_ns()
    p=subprocess.Popen([sys.executable,str(HERE/'context_calc_supervisor_v1.py'),label,mode],
                       stdout=(root/(label+'-stdout.txt')).open('wb'),stderr=(root/(label+'-stderr.txt')).open('wb'))
    print(json.dumps({'started':label,'pid':p.pid}),flush=True)
    code=p.wait()
    runs.append({'label':label,'mode':mode,'pid':p.pid,'exit_code':code,'started_ns':begin,'finished_ns':time.perf_counter_ns()})
    (root/'runs.json').write_text(json.dumps(runs,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'finished':label,'exit_code':code}),flush=True)
