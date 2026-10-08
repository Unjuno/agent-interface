from __future__ import annotations
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
OLLAMA_IMAGE='sha256:8262851b2846b87c649eddf3e76beb270c52f4d1bc94559f47efde16b0841551'
HELPER_IMAGE='sha256:570ad778e44baf0bd094241515ed6cbbc7ce154321a7d76f295c42f2d5799261'
MODEL_DIGEST='fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1'
CONTAINER='agent-interface-570-r7-temporal-ollama'; NETWORK='agent-interface-570-r7-temporal-internal'
def run(cmd,check=True,capture=False,timeout=600):
    cp=subprocess.run(cmd,text=True,capture_output=capture,timeout=timeout,encoding='utf-8',errors='replace')
    if check and cp.returncode: raise RuntimeError(f'command exit {cp.returncode}: {cmd[:6]} stderr={cp.stderr if capture else ""}')
    return cp
def require_missing(kind,name):
    cp=run(['docker',kind,'inspect',name],False,True)
    if cp.returncode==0: raise SystemExit('STOP unique Docker name already exists: '+kind+' '+name)
    if 'No such' not in cp.stderr and 'not found' not in cp.stderr.lower(): raise SystemExit('STOP cannot verify unique Docker name '+name)
def helper(root,evidence,network,script,args=(),network_none=False,timeout=600):
    return run(['docker','run','--rm','--platform','linux/amd64','--network','none' if network_none else network,'--cpus','2','--memory','4g','--pids-limit','64',
        '--mount',f'type=bind,source={root},target=/study,readonly','--mount',f'type=bind,source={evidence},target=/study/evidence',
        '--entrypoint','python',HELPER_IMAGE,'/study/'+script,*args],False,True,timeout=timeout)
def gpu_sample():
    r=run(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],True,True,timeout=8)
    return [int(x.strip()) for x in r.stdout.strip().splitlines()[0].split(',')]
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--model-store',type=Path,required=True);a=p.parse_args()
    root=a.root.resolve(); ev=root/'evidence';store=a.model_store.resolve();freeze=json.loads((root/'FREEZE.json').read_text(encoding='utf-8'))
    for name,digest in freeze['source_sha256'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest: raise SystemExit('STOP frozen source changed: '+name)
    pre=json.loads((root/'data/PREFORMAL.json').read_text(encoding='utf-8'))
    input_audit=json.loads((ev/'INPUT_AUDIT.json').read_text(encoding='utf-8'))
    if input_audit.get('decision')!='INPUT_AUDIT_PASS' or len(pre['formal_cases'])!=36: raise SystemExit('STOP input audit/denominator failure')
    for name in ('formal','baseline.json','RUN_STATUS.json','sampler.jsonl','STOP_SAMPLER','audit'):
        if (ev/name).exists(): raise SystemExit('STOP prior formal output exists: '+name)
    ev.mkdir(parents=True,exist_ok=True); require_missing('network',NETWORK); require_missing('container',CONTAINER)
    run(['docker','network','create','--internal',NETWORK])
    sampler=None; started=False
    try:
        tests=run(['docker','run','--rm','--platform','linux/amd64','--network','none','--cpus','2','--memory','4g','--pids-limit','64',
            '--mount',f'type=bind,source={root},target=/study,readonly','--entrypoint','python',HELPER_IMAGE,'-m','unittest','discover','-s','/study','-p','test_study.py','-v'],False,True,timeout=180)
        (ev/'construction-tests.stdout.txt').write_text(tests.stdout,encoding='utf-8');(ev/'construction-tests.stderr.txt').write_text(tests.stderr,encoding='utf-8')
        if tests.returncode: raise SystemExit('STOP_HELPER_TEST_FAILURE; formal_calls=0')
        inp=helper(root,ev,'none','audit.py',['--root','/study','--out','/study/evidence/INPUT_AUDIT.json','--inputs-only'])
        (ev/'input-audit.stdout.txt').write_text(inp.stdout,encoding='utf-8');(ev/'input-audit.stderr.txt').write_text(inp.stderr,encoding='utf-8')
        if inp.returncode or json.loads((ev/'INPUT_AUDIT.json').read_text(encoding='utf-8')).get('decision')!='INPUT_AUDIT_PASS': raise SystemExit('STOP_CONTAINER_INPUT_AUDIT; formal_calls=0')
        run(['docker','run','-d','--name',CONTAINER,'--platform','linux/amd64','--network',NETWORK,'--network-alias','ollama','--gpus','all',
             '--mount',f'type=bind,source={store},target=/models,readonly','--env','OLLAMA_MODELS=/models','--env','OLLAMA_NO_CLOUD=true','--env','OLLAMA_NUM_PARALLEL=1',OLLAMA_IMAGE,'serve'])
        deadline=time.monotonic()+90
        while time.monotonic()<deadline:
            if run(['docker','exec',CONTAINER,'ollama','list'],False,True,timeout=8).returncode==0: break
            time.sleep(1)
        else: raise SystemExit('STOP_LOCAL_OLLAMA_READINESS; formal_calls=0')
        ident=helper(root,ev,NETWORK,'model_runner.py',['--mode','identity','--root','/study','--out','/study/evidence'])
        (ev/'identity.stdout.txt').write_text(ident.stdout,encoding='utf-8');(ev/'identity.stderr.txt').write_text(ident.stderr,encoding='utf-8')
        if ident.returncode: raise SystemExit('STOP_MODEL_IDENTITY_OR_EMPTY_SERVER; formal_calls=0')
        used,util=gpu_sample(); ps=run(['docker','exec',CONTAINER,'ollama','ps'],True,True,timeout=8)
        if len(ps.stdout.strip().splitlines())>1: raise SystemExit('STOP_SERVER_NOT_EMPTY_AT_BASELINE; formal_calls=0')
        (ev/'baseline.json').write_text(json.dumps({'memory_used_mib':used,'gpu_utilization_percent':util,'nvidia_smi':'nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits','ollama_ps':ps.stdout,'empty_model_server':True},indent=2)+'\n',encoding='utf-8')
        (ev/'commands.json').write_text(json.dumps({'allocation':pre['allocation'],'container':CONTAINER,'network':NETWORK,'network_internal':True,'published_ports':False,'model_image':OLLAMA_IMAGE,'helper_image':HELPER_IMAGE,'gpu_flag':'--gpus all','source_and_inputs':'read-only bind mount','formal_schedule':'36 sequential calls; counterbalanced order; zero retry','audit':'separate helper, network none, GPU-less'},indent=2)+'\n',encoding='utf-8')
        (ev/'ollama-start.log').write_text(run(['docker','logs',CONTAINER],False,True).stdout,encoding='utf-8')
        (ev/'STOP_SAMPLER').unlink(missing_ok=True)
        sampler=subprocess.Popen([sys.executable,str(root/'sampler.py'),'--container',CONTAINER,'--out',str(ev/'sampler.jsonl'),'--stop-file',str(ev/'STOP_SAMPLER')])
        time.sleep(1)
        started=True
        formal=helper(root,ev,NETWORK,'model_runner.py',['--mode','formal','--root','/study','--out','/study/evidence'],timeout=900)
        (ev/'formal.stdout.txt').write_text(formal.stdout,encoding='utf-8');(ev/'formal.stderr.txt').write_text(formal.stderr,encoding='utf-8')
        (ev/'STOP_SAMPLER').write_text('formal block ended\n',encoding='utf-8');sampler.wait(timeout=20);sampler=None
        (ev/'ollama-final.log').write_text(run(['docker','logs',CONTAINER],False,True).stdout,encoding='utf-8')
        out=ev/'audit';out.mkdir(exist_ok=False)
        aud=helper(root,ev,'none','audit.py',['--root','/study','--out','/study/evidence/audit/AUDIT.json'])
        (out/'stdout.txt').write_text(aud.stdout,encoding='utf-8');(out/'stderr.txt').write_text(aud.stderr,encoding='utf-8')
        if formal.returncode: raise SystemExit('HOLD_FORMAL_FAILURE_RETAINED_NO_RETRY')
        if aud.returncode: raise SystemExit('HOLD_INDEPENDENT_AUDIT_FAILURE')
        print((out/'AUDIT.json').read_text(encoding='utf-8'))
    finally:
        if sampler is not None:
            (ev/'STOP_SAMPLER').write_text('launcher exit\n',encoding='utf-8')
            try: sampler.wait(timeout=10)
            except subprocess.TimeoutExpired: sampler.kill()
        if started and not (ev/'RUN_STATUS.json').exists():
            (ev/'RUN_STATUS.json').write_text(json.dumps({'schema':'visual-temporal-570-r7-run-status-v1','failure':'launcher terminated during formal block','retries':0},indent=2)+'\n',encoding='utf-8')
        if started and not (ev/'ollama-final.log').exists(): (ev/'ollama-final.log').write_text(run(['docker','logs',CONTAINER],False,True).stdout,encoding='utf-8')
        run(['docker','stop',CONTAINER],False,True,timeout=40);run(['docker','rm',CONTAINER],False,True,timeout=40);run(['docker','network','rm',NETWORK],False,True,timeout=40)
if __name__=='__main__':main()
