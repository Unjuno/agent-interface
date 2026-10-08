"""One exclusive construction invocation; preserve uncertain terminals, no retry."""
if not __debug__:raise RuntimeError('STOP_OPTIMIZED_RUNNER')
import datetime,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def call(args):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=30)
        return dict(command=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
    except (OSError,subprocess.TimeoutExpired) as e:
        def decode(x):return x.decode(errors='replace') if isinstance(x,bytes) else (x or '')
        return dict(command=args,exit=None,error=repr(e),stdout=decode(getattr(e,'stdout',None)),stderr=decode(getattr(e,'stderr',None)))
def main():
    out=ROOT/'runs';out.mkdir(exist_ok=False)
    files=['policy.py','test_policy.py','probe.py','run_probe.py']
    source={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in files}
    with (ROOT/'CONSTRUCTION_FREEZE.json').open('x') as f:json.dump(source,f,indent=2);f.write('\n')
    engine=['orbctl','run','-m','research-59-hud-ocr-5ce3-20261003','-u','root','docker'];name='native-failure-7163-c01-5ce3'
    args=engine+['create','--name',name,'--pull','never','--entrypoint','python3','--network','none','--read-only','--cpus','1','--memory','512m','--memory-swap','512m','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,nodev,size=64m','--label','research.owner=01a0b98b-5ce3-7f53-82f3-e09294f24d57','--mount',f'type=bind,src={ROOT},dst=/study,readonly','--mount',f'type=bind,src={out},dst=/out','--workdir','/study','sha256:b2ae049f7c500a3f6b6d162b0351297331434cff5a43f66e1bb41aff90478c96','-B','/study/probe.py','/out/preflight']
    receipt=dict(allocation='NATIVE-FAILURE-7163-C01-5CE3-20261004-01',started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_sha256=source,formal_candidate_runs=0,formal_auditor_runs=0,terminal=None)
    try:
        receipt['create']=call(args);assert receipt['create']['exit']==0
        receipt['run']=call(engine+['start','-a',name])
    finally:
        receipt['inspect']=call(engine+['inspect',name])
        if receipt['inspect']['exit']==0:receipt['terminal']=json.loads(receipt['inspect']['stdout'])[0]['State']
        receipt['source_unchanged']=all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h for n,h in source.items())
        receipt['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        with (out/'receipt.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
    assert receipt['run']['exit']==0 and receipt['terminal'] is not None and not receipt['terminal']['Running'] and receipt['terminal']['ExitCode']==0 and not receipt['terminal']['OOMKilled'] and receipt['source_unchanged']
    print(json.dumps({'terminal':receipt['terminal'],'source_unchanged':receipt['source_unchanged']}))
if __name__=='__main__':main()
