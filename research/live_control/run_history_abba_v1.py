"""Predeclared fresh-session ABBA, no per-condition retry or selected rerun."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
root=HERE/'results/history-abba-01';root.mkdir(exist_ok=False)
order=[('history-abba-1-last','last'),('history-abba-2-all','all'),('history-abba-3-all','all'),('history-abba-4-last','last')]
plan={'order':order,'seed':238,'model':'gpt-5.6-luna','effort':'low','max_turns':5,
      'scope':'same supervisor/runtime/prompt except last one versus all prior factual proposal/outcome records; all bounded to five turns',
      'metrics':['independent saved task success','model turns','save chords','input/cached/output tokens','initial capture to evaluation','supervisor wall'],
      'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['run_history_abba_v1.py','history_calc_supervisor_v1.py','history_calc_driver_v1.py','calc_proposal_schema_v1.py','model_pair_runner_v1.py']}}
(root/'plan.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8');runs=[]
for label,mode in order:
    begin=time.perf_counter_ns()
    p=subprocess.Popen([sys.executable,str(HERE/'history_calc_supervisor_v1.py'),label,mode],
                       stdout=(root/(label+'-stdout.txt')).open('wb'),stderr=(root/(label+'-stderr.txt')).open('wb'))
    print(json.dumps({'started':label,'pid':p.pid}),flush=True)
    code=p.wait()
    runs.append({'label':label,'mode':mode,'pid':p.pid,'exit_code':code,'started_ns':begin,'finished_ns':time.perf_counter_ns()})
    (root/'runs.json').write_text(json.dumps(runs,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'finished':label,'exit_code':code}),flush=True)
