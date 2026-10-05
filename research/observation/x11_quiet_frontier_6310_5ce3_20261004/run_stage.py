"""One-shot digest-pinned owned Engine stages with immutable source gate."""
import datetime,hashlib,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def call(args,timeout=60):
    t=time.monotonic_ns();p=subprocess.run(args,capture_output=True,timeout=timeout)
    return {'command':args,'returncode':p.returncode,'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace'),'elapsed_ns':time.monotonic_ns()-t}
def main():
    stage=sys.argv[1];assert stage in ('candidate','auditor')
    freeze=json.loads((ROOT/'FREEZE.json').read_text());plan=json.loads((ROOT/'PLAN.json').read_text())
    for path,digest in freeze['sha256'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,('SOURCE_DRIFT',path)
    engine=['orbctl','run','-m',plan['vm'],'-u','root','docker']
    if stage=='auditor':
        prior=json.loads((ROOT/'runs/candidate/receipt.json').read_text())
        assert prior['run']['returncode']==0 and prior['terminal']['Running']is False and prior['terminal']['ExitCode']==0
    out=ROOT/'runs'/stage;out.mkdir(parents=True,exist_ok=False)
    name='frontier-6310-t1-5ce3-'+stage
    command=engine+['create','--name',name,'--pull','never','--entrypoint','python3','--network','none','--read-only','--cpus','1','--memory','512m','--memory-swap','512m','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,nodev,size=64m','--label','research.owner=01a0b98b-5ce3-7f53-82f3-e09294f24d57','--mount',f'type=bind,src={ROOT},dst=/study,readonly','--mount',f'type=bind,src={out},dst=/out',plan['image'],'-B']
    command+=['/study/candidate.py','/out']if stage=='candidate'else['/study/auditor.py','/study/runs/candidate/raw.jsonl','/out/AUDIT.json']
    receipt={'stage':stage,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'freeze_sha256':hashlib.sha256((ROOT/'FREEZE.json').read_bytes()).hexdigest(),'create':call(command)}
    try:
        assert receipt['create']['returncode']==0,'create failed'
        receipt['before']=call(engine+['inspect',name]);assert receipt['before']['returncode']==0
        receipt['run']=call(engine+['start','-a',name],60)
        receipt['after']=call(engine+['inspect',name]);assert receipt['after']['returncode']==0
        receipt['terminal']=json.loads(receipt['after']['stdout'])[0]['State']
        assert not receipt['terminal']['Running']and receipt['terminal']['ExitCode']==0 and not receipt['terminal']['OOMKilled']and receipt['run']['returncode']==0,'stage failed'
    finally:
        receipt['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        with(out/'receipt.json').open('x')as f:json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps({'stage':stage,'exit':receipt['terminal']['ExitCode']}))
if __name__=='__main__':main()
