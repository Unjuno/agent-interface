"""Run predecessor A, request SIGTERM, then retry B either immediately or only after A reap."""
from __future__ import annotations
import json, os, signal, subprocess, sys, time
from pathlib import Path
from contract import image_receipt

def put(path,data):
    with Path(path).open('x',encoding='utf-8') as f: json.dump(data,f,indent=2,sort_keys=True);f.write('\n')

def cmd_a(source,out):
    return ['/usr/bin/ffmpeg','-nostdin','-hide_banner','-loglevel','error','-n','-threads','1','-readrate','1','-i',str(source),'-vf',"select='gte(n,15)'",'-fps_mode','vfr','-map','0:v:0','-frames:v','1','-c:v','png','-threads','1','-pix_fmt','rgb24','-update','1',str(out)]
def cmd_b(source,out):
    return ['/usr/bin/ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-threads','1','-i',str(source),'-map','0:v:0','-frames:v','1','-c:v','png','-threads','1','-pix_fmt','rgb24','-update','1',str(out)]

def main():
    case_path=Path(sys.argv[1]).resolve(); case=json.loads(case_path.read_text()); d=case_path.parent
    out=d/'output.png'; expected=json.loads(Path(case['expected']).read_text())
    if out.exists(): raise RuntimeError('preexisting output')
    put(d/'ready.json',{'id':case['id'],'ns':time.perf_counter_ns(),'pid':os.getpid()})
    print('Retry quiescence '+case['id']+'\nPress Enter once.',flush=True)
    if sys.stdin.readline()!='\n': raise RuntimeError('one Enter required')
    aerr=(d/'a.stderr').open('xb'); berr=(d/'b.stderr').open('xb')
    ap=bp=None
    try:
        ap=subprocess.Popen(cmd_a(Path(case['source_a']),out),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=aerr,start_new_session=True)
        aspawn=time.perf_counter_ns(); put(d/'a-start.json',{'pid':ap.pid,'spawned_ns':aspawn})
        deadline=aspawn+case['signal_after_ms']*1_000_000
        while time.perf_counter_ns()<deadline: time.sleep(.002)
        ss=time.perf_counter_ns(); os.killpg(ap.pid,signal.SIGTERM); sf=time.perf_counter_ns(); put(d/'stop.json',{'signal':int(signal.SIGTERM),'started_ns':ss,'finished_ns':sf})
        if case['strategy']=='wait_reap':
            ap.wait(timeout=3); areap=time.perf_counter_ns()
        else: areap=None
        bspawn0=time.perf_counter_ns();bp=subprocess.Popen(cmd_b(Path(case['source_b']),out),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=berr,start_new_session=True);bspawn=time.perf_counter_ns()
        bp.wait(timeout=3);breap=time.perf_counter_ns()
        after=image_receipt(out,expected)
        if out.exists():(d/'after_b.png').write_bytes(out.read_bytes())
        put(d/'after-b.json',after)
        if case['strategy']=='immediate':
            ap.wait(timeout=3);areap=time.perf_counter_ns()
        time.sleep(.10)
        final=image_receipt(out,expected)
        if out.exists():(d/'final.png').write_bytes(out.read_bytes())
        put(d/'final.json',final)
        proc={'id':case['id'],'strategy':case['strategy'],'a_returncode':ap.returncode,'b_returncode':bp.returncode,'a_spawned_ns':aspawn,'stop_finished_ns':sf,'b_spawn_started_ns':bspawn0,'b_spawned_ns':bspawn,'b_reaped_ns':breap,'a_reaped_ns':areap,'b_started_before_a_reap':bspawn < areap}
        put(d/'process.json',proc)
        put(d/'done.json',{'id':case['id'],'done_ns':time.perf_counter_ns()})
        print(json.dumps({'id':case['id'],'strategy':case['strategy'],'after_b':after['state'],'final':final['state']}),flush=True)
        for _ in range(1000):
            if (d/'close-worker').exists():return
            time.sleep(.01)
    finally:
        for p in (bp,ap):
            if p is not None and p.poll() is None:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                p.wait(timeout=2)
        aerr.close();berr.close()
if __name__=='__main__':
    try:main()
    except Exception as e:
        d=Path(sys.argv[1]).resolve().parent; (d/'worker-failure.json').write_text(json.dumps({'type':type(e).__name__,'error':str(e)},indent=2)); raise
