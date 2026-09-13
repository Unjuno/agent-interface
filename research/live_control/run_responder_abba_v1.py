"""Predeclared fresh-session ABBA, no per-condition retry or selected rerun."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
root=HERE/'results/responder-abba-01';root.mkdir(exist_ok=False)
order=[('responder-abba-1-builtin','builtin'),('responder-abba-2-responder','responder'),('responder-abba-3-responder','responder'),('responder-abba-4-builtin','builtin')]
plan={'order':order,'seed':238,'model':'gpt-5.6-luna','effort':'low','max_turns':5,
      'scope':'same supervisor/runtime/prompt/full last outcome; builtin versus constrained responder instructions; Fast disabled both; bounded to five turns',
      'metrics':['independent saved task success','model turns','save chords','input/cached/output tokens','initial capture to evaluation','supervisor wall'],
      'sources':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['run_responder_abba_v1.py','responder_calc_supervisor_v1.py','responder_calc_driver_v1.py','calc_proposal_schema_v1.py','model_context_runner_v1.py','screenshot_responder_v1.txt']}}
(root/'plan.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8');runs=[]
for label,mode in order:
    begin=time.perf_counter_ns()
    p=subprocess.Popen([sys.executable,str(HERE/'responder_calc_supervisor_v1.py'),label,mode],
                       stdout=(root/(label+'-stdout.txt')).open('wb'),stderr=(root/(label+'-stderr.txt')).open('wb'))
    print(json.dumps({'started':label,'pid':p.pid}),flush=True)
    code=p.wait()
    runs.append({'label':label,'mode':mode,'pid':p.pid,'exit_code':code,'started_ns':begin,'finished_ns':time.perf_counter_ns()})
    (root/'runs.json').write_text(json.dumps(runs,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'finished':label,'exit_code':code}),flush=True)
