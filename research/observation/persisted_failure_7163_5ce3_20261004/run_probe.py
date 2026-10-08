"""One source-frozen construction invocation. Never retries an uncertain process."""
if not __debug__:raise RuntimeError('STOP_OPTIMIZED_RUNNER')
import datetime,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
IMAGE='sha256:b2ae049f7c500a3f6b6d162b0351297331434cff5a43f66e1bb41aff90478c96'
ENGINE=['orbctl','run','-m','research-59-hud-ocr-5ce3-20261003','-u','root','docker']
NAME='persisted-failure-7163-c02-5ce3'
def call(args,timeout=20):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
        return dict(command=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
    except (OSError,subprocess.TimeoutExpired) as exc:
        def decode(x):return x.decode(errors='replace') if isinstance(x,bytes) else x or ''
        return dict(command=args,exit=None,error=repr(exc),stdout=decode(getattr(exc,'stdout',None)),stderr=decode(getattr(exc,'stderr',None)))
def main():
    out=ROOT/'runs';out.mkdir(exist_ok=False)
    source={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('policy.py','test_policy.py','probe.py','audit.py','test_audit.py','run_probe.py','README.md')}
    with (ROOT/'CONSTRUCTION_FREEZE.json').open('x') as f:json.dump(source,f,indent=2);f.write('\n')
    receipt=dict(allocation='PERSISTED-FAILURE-7163-C02-5CE3-20261004-01',started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=source,formal_candidate_runs=0,formal_auditor_runs=0,terminal=None)
    args=ENGINE+['create','--name',NAME,'--pull','never','--entrypoint','python3','--network','none','--read-only','--cpus','1','--memory','512m','--memory-swap','512m','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,nodev,size=64m','--label','research.owner=01a0b98b-5ce3-7f53-82f3-e09294f24d57','--mount',f'type=bind,src={ROOT},dst=/study,readonly','--mount',f'type=bind,src={out},dst=/out','--workdir','/study',IMAGE,'-B','/study/probe.py','/out/native']
    try:
        receipt['create']=call(args)
        if receipt['create']['exit']!=0:raise RuntimeError('create failed')
        receipt['run']=call(ENGINE+['start','-a',NAME],60)
    finally:
        receipt['inspect']=call(ENGINE+['inspect',NAME])
        if receipt['inspect']['exit']==0:
            try:receipt['terminal']=json.loads(receipt['inspect']['stdout'])[0]['State']
            except (ValueError,KeyError,IndexError) as exc:receipt['inspect_parse_error']=repr(exc)
        receipt['source_unchanged']=all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in source.items())
        receipt['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        with (out/'receipt.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
    state=receipt['terminal']
    if receipt.get('run',{}).get('exit')!=0 or state is None or state['Running'] or state['ExitCode']!=0 or state['OOMKilled'] or not receipt['source_unchanged']:raise RuntimeError('first STOP retained; do not retry')
    print(json.dumps({'allocation':receipt['allocation'],'terminal':state,'source_unchanged':receipt['source_unchanged']}))
if __name__=='__main__':main()
