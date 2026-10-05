"""One bounded browser invocation; preserve complete server evidence in finally."""
import argparse,datetime,json,os,pathlib,subprocess,sys
from fixture import Trial,make_server
p=argparse.ArgumentParser();p.add_argument('spec',type=pathlib.Path);p.add_argument('output',type=pathlib.Path)
a=p.parse_args();spec=json.loads(a.spec.read_text());a.output.mkdir(exist_ok=False)
schedule=[];trials={}
for i,case in enumerate(spec):
    for policy in (('STAGE','WAIT') if i%2==0 else ('WAIT','STAGE')):
        trial_id=case['case_id']+'_'+policy.lower()
        schedule.append(dict(trial_id=trial_id,case_id=case['case_id'],policy=policy))
        trials[trial_id]=Trial(case)
(a.output/'schedule.json').write_text(json.dumps(schedule,indent=2)+'\n')
server,thread=make_server(trials);origin=f'http://127.0.0.1:{server.server_port}'
argv=[os.environ['NODE_EXE'],str(pathlib.Path(__file__).with_name('controller.cjs')),origin,str(a.output/'schedule.json'),str(a.output/'controller.jsonl')]
receipt=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),argv=['$NODE_EXE','$SOURCE/controller.cjs','$ORIGIN','$OUTPUT/schedule.json','$OUTPUT/controller.jsonl'],pid=os.getpid(),origin=origin,exit_code=None)
try:
    with (a.output/'controller.stdout.txt').open('x') as out,(a.output/'controller.stderr.txt').open('x') as err:
        r=subprocess.run(argv,stdout=out,stderr=err,timeout=180,check=False);receipt['exit_code']=r.returncode
except Exception as e:
    receipt['runner_error']=repr(e);receipt['exit_code']=124
finally:
    server.shutdown();server.server_close();thread.join(timeout=2)
    with (a.output/'server.jsonl').open('x') as f:
        for trial_id,trial in trials.items():
            f.write(json.dumps(dict(trial_id=trial_id,events=trial.events,effects=trial.effects),sort_keys=True)+'\n')
    receipt['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    receipt['server_stopped']=not thread.is_alive()
    receipt['output_bytes']=sum(x.stat().st_size for x in a.output.iterdir() if x.is_file())
    (a.output/'EXECUTION.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
if receipt['output_bytes']>10_000_000:raise SystemExit(2)
raise SystemExit(receipt['exit_code'])
