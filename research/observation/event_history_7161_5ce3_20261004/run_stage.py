if not __debug__: raise RuntimeError('STOP_OPTIMIZED_RUNNER_UNSUPPORTED')
import datetime,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def call(args,timeout=60):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
        return dict(command=args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr)
    except (subprocess.TimeoutExpired,OSError) as e:
        def decode(x): return x.decode(errors='replace') if isinstance(x,bytes) else (x or '')
        return dict(command=args,exit=None,error=type(e).__name__,detail=str(e),stdout=decode(getattr(e,'stdout',None)),stderr=decode(getattr(e,'stderr',None)))
def main():
    stage=sys.argv[1];assert stage in ('tests','tests_final','candidate','auditor');is_test=stage.startswith('tests')
    plan=json.loads((ROOT/'PLAN.json').read_text())
    freeze=ROOT/'FREEZE.json'
    if not is_test:
        for name,digest in json.loads(freeze.read_text()).items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,('SOURCE_DRIFT',name)
    if stage=='auditor':
        prior=json.loads((ROOT/'runs/candidate/receipt.json').read_text());assert prior['run']['exit']==0 and prior['terminal']['ExitCode']==0 and not prior['terminal']['Running']
    out=ROOT/'runs'/stage;out.mkdir(parents=True,exist_ok=False)
    engine=['orbctl','run','-m',plan['vm'],'-u','root','docker'];name='event-history-7161-t0-5ce3-'+stage
    args=engine+['create','--name',name,'--pull','never','--entrypoint','python3','--network','none','--read-only','--cpus','1','--memory','512m','--memory-swap','512m','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,nodev,size=64m','--label','research.owner='+plan['owner'],'--mount',f'type=bind,src={ROOT},dst=/study,readonly','--mount',f'type=bind,src={out},dst=/out','--workdir','/study',plan['image'],'-B']
    args+=['-m','unittest','test_policy','test_runner'] if is_test else (['/study/candidate.py','/out'] if stage=='candidate' else ['/study/auditor.py','/study/runs/candidate/raw.jsonl','/out/AUDIT.json'])
    receipt=dict(stage=stage,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),freeze_sha256=hashlib.sha256(freeze.read_bytes()).hexdigest() if not is_test else None,terminal=None)
    try:
        receipt['create']=call(args)
        assert receipt['create']['exit']==0
        receipt['run']=call(engine+['start','-a',name])
    finally:
        receipt['inspect']=call(engine+['inspect',name])
        if receipt['inspect']['exit']==0:
            try:receipt['terminal']=json.loads(receipt['inspect']['stdout'])[0]['State']
            except (ValueError,KeyError,IndexError,TypeError) as e:receipt['inspection_error']=type(e).__name__
        receipt['terminal_status']='OBSERVED' if receipt['terminal'] is not None else 'UNKNOWN_NO_RETRY'
        receipt['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        with (out/'receipt.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
    assert receipt['run']['exit']==0 and receipt['terminal'] is not None and receipt['terminal']['ExitCode']==0 and not receipt['terminal']['Running'] and not receipt['terminal']['OOMKilled']
    print(json.dumps(dict(stage=stage,state=receipt['terminal'])))
if __name__=='__main__':main()
