#!/usr/bin/env python3
import argparse, hashlib, json, os, select, shutil, signal, socket, subprocess, sys, time
from pathlib import Path

EXPECTED_ARTIFACT_SHA256 = '522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b'
EXPECTED_BLOBS = {
    'interactive_v27.py':'9a012c825bcdc995a87185d423ecc496dc399094',
    'event_socket_v11.py':'fe71be94c9284af0ae7c0b4db0b47dd8b1a86522',
    'session_v16.py':'c188b3653ef4bec9b1a846296b003b0415f3f173',
}

def git_blob_sha(path):
    data=Path(path).read_bytes();return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()

def request(path,payload,timeout=20):
    started=time.perf_counter_ns()
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
        s.settimeout(timeout);s.connect(path);s.sendall((json.dumps(payload,separators=(',',':'))+'\n').encode())
        data=b''
        while not data.endswith(b'\n'):
            chunk=s.recv(65536)
            if not chunk:break
            data+=chunk
    returned=time.perf_counter_ns()
    if not data.endswith(b'\n'):raise RuntimeError('bounded response line missing')
    return json.loads(data),started,returned

def read_endpoint(proc,timeout=10):
    ready,_,_=select.select([proc.stdout],[],[],timeout)
    if not ready:raise TimeoutError('endpoint announcement timeout')
    line=proc.stdout.readline()
    if not line:raise RuntimeError('wrapper exited before endpoint: '+proc.stderr.read())
    return json.loads(line),time.perf_counter_ns()

def load_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--case-id',required=True);ap.add_argument('--policy',choices=['endpoint_only','existing_ready_gate'],required=True)
    ap.add_argument('--seed',type=int,required=True);ap.add_argument('--artifact-root',type=Path,required=True);ap.add_argument('--artifact-zip',type=Path,required=True)
    ap.add_argument('--experiment-dir',type=Path,required=True);ap.add_argument('--out-root',type=Path,required=True)
    a=ap.parse_args();case_dir=a.out_root/a.case_id
    case_dir.mkdir(parents=True,exist_ok=False)
    source=a.artifact_root/'source';live=source/'research/live_control'
    if sha256(a.artifact_zip)!=EXPECTED_ARTIFACT_SHA256:raise RuntimeError('artifact sha mismatch')
    blobs={name:git_blob_sha(live/name) for name in EXPECTED_BLOBS}
    if blobs!=EXPECTED_BLOBS:raise RuntimeError(f'core blob mismatch {blobs}')
    candidate_src=a.experiment_dir/'event_socket_existing_ready_gate_v1.py';candidate_exec=live/'event_socket_existing_ready_gate_v1.py'
    if a.policy=='existing_ready_gate':
        if candidate_exec.exists():candidate_exec.unlink()
        shutil.copy2(candidate_src,candidate_exec)
        wrapper=candidate_exec
    else:wrapper=live/'event_socket_v11.py'
    runtime_out=case_dir/'runtime';trace=case_dir/'ready-trace.json'
    env=os.environ.copy();xauth=case_dir/'global-Xauthority';xauth.touch();env['XAUTHORITY']=str(xauth)
    if a.policy=='existing_ready_gate':env['AI_EXISTING_READY_TRACE']=str(trace)
    cmd=[sys.executable,'-u',str(wrapper),'serve','--','--app','xterm','--seed',str(a.seed),'--out',str(runtime_out)]
    launched=time.perf_counter_ns();proc=subprocess.Popen(cmd,cwd=live,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
    endpoint=None;clock=None;finish=None
    try:
        endpoint,endpoint_receipt_ns=read_endpoint(proc)
        clock_payload={'after':0,'events':['clock'],'timeout':0.3,'command':{'op':'clock'},'request_id':f'{a.case_id}-clock'}
        clock,clock_started_ns,clock_returned_ns=request(endpoint['socket'],clock_payload,timeout=5)
        finish_payload={'after':clock.get('cursor',0),'events':['independent_evaluation'],'timeout':8.0,'command':{'op':'finish'},'request_id':f'{a.case_id}-finish'}
        finish,finish_started_ns,finish_returned_ns=request(endpoint['socket'],finish_payload,timeout=12)
        try:code=proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL);code=proc.wait(timeout=3)
        stderr=proc.stderr.read();stdout_tail=proc.stdout.read()
    finally:
        if proc.poll() is None:
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            proc.wait(timeout=3)
        if candidate_exec.exists() and a.policy=='existing_ready_gate':candidate_exec.unlink()
    events=load_jsonl(runtime_out/'events.jsonl');owners=json.loads((runtime_out/'owner-events.json').read_text())
    def first_event(name,**match):
        for r in events:
            if r.get('event')==name and all(r.get(k)==v for k,v in match.items()):return r
        return None
    ready=first_event('ready');initial=first_event('observation',id='initial');clock_event=first_event('clock')
    result={
        'case_id':a.case_id,'policy':a.policy,'seed':a.seed,'launched_ns':launched,
        'endpoint_receipt_ns':endpoint_receipt_ns,'endpoint':endpoint,'clock':clock,'clock_started_ns':clock_started_ns,'clock_returned_ns':clock_returned_ns,
        'finish':finish,'finish_started_ns':finish_started_ns,'finish_returned_ns':finish_returned_ns,'wrapper_exit':code,
        'ready_event':ready,'initial_observation':initial,'clock_event':clock_event,'owner_events':owners,
        'ready_trace':json.loads(trace.read_text()) if trace.exists() else None,'stderr':stderr,'stdout_tail':stdout_tail,
        'source_blobs':blobs,'artifact_sha256':EXPECTED_ARTIFACT_SHA256,
        'runtime_event_count':len(events),
    }
    (case_dir/'case.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'case_id':a.case_id,'policy':a.policy,'clock_status':clock.get('status'),'exit':code},sort_keys=True))

if __name__=='__main__':main()
