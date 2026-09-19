"""v2: absent predecessor stage is NO_EFFECT, never a harness failure or publish."""
from __future__ import annotations
import json,os,signal,subprocess,sys,time,shutil,threading
from pathlib import Path
from contract import Publisher,image_receipt

def put(path,obj):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,sort_keys=True);f.write('\n')
def cmd_a(src,out):
    return ['/usr/bin/ffmpeg','-nostdin','-hide_banner','-loglevel','error','-n','-threads','1','-readrate','1','-i',str(src),'-vf',"select='gte(n,15)'",'-fps_mode','vfr','-map','0:v:0','-frames:v','1','-c:v','png','-threads','1','-pix_fmt','rgb24','-update','1',str(out)]
def cmd_b(src,out):
    return ['/usr/bin/ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-threads','1','-i',str(src),'-map','0:v:0','-frames:v','1','-c:v','png','-threads','1','-pix_fmt','rgb24','-update','1',str(out)]
def main():
    casep=Path(sys.argv[1]).resolve();case=json.loads(casep.read_text());d=casep.parent;exp=json.loads(Path(case['expected']).read_text())
    canonical=d/'output.png';sa=d/'stage-a.png';sb=d/'stage-b.png'
    if any(p.exists() for p in (canonical,sa,sb)):raise RuntimeError('preexisting output/stage')
    put(d/'ready.json',{'id':case['id'],'pid':os.getpid(),'ns':time.perf_counter_ns()});print('Staged promotion '+case['id']+'\nPress Enter once.',flush=True)
    if sys.stdin.readline()!='\n':raise RuntimeError('one Enter required')
    ae=(d/'a.stderr').open('xb');be=(d/'b.stderr').open('xb');ap=bp=None
    try:
        ap=subprocess.Popen(cmd_a(Path(case['source_a']),sa),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=ae,start_new_session=True);aspawn=time.perf_counter_ns();put(d/'a-start.json',{'pid':ap.pid,'spawned_ns':aspawn})
        areap_box={}; areap_event=threading.Event()
        def reap_a():
            ap.wait(); areap_box['ns']=time.perf_counter_ns(); areap_event.set()
        threading.Thread(target=reap_a,daemon=True).start()
        deadline=aspawn+case['signal_after_ms']*1_000_000
        while time.perf_counter_ns()<deadline:time.sleep(.002)
        ss=time.perf_counter_ns();os.killpg(ap.pid,signal.SIGTERM);sf=time.perf_counter_ns();put(d/'stop.json',{'started_ns':ss,'finished_ns':sf,'signal':int(signal.SIGTERM)})
        # Current intent becomes B immediately. Do not wait for A.
        bp=subprocess.Popen(cmd_b(Path(case['source_b']),sb),stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=be,start_new_session=True);bspawn=time.perf_counter_ns();bp.wait(timeout=3);breap=time.perf_counter_ns()
        br=image_receipt(sb,exp);put(d/'b-stage.json',br)
        if br['state']!='B':raise RuntimeError('B stage not exact B')
        shutil.copy2(sb,d/'b-stage-retained.png')
        pub=Publisher(canonical,case['mode'],2);bpub=pub.publish(sb,generation=2,attempt_id='B');bcan=image_receipt(canonical,exp);put(d/'after-b-publish.json',bcan)
        # Old A may complete later. Only after its real reap do we evaluate its completion callback.
        if not areap_event.wait(timeout=3):raise TimeoutError('A reap')
        areap=areap_box['ns'];ar=image_receipt(sa,exp);put(d/'a-stage.json',ar)
        if ar['state']=='A':
            shutil.copy2(sa,d/'a-stage-retained.png')
            apub=pub.publish(sa,generation=1,attempt_id='A')
        elif ar['state']=='ABSENT':
            now=time.perf_counter_ns(); apub={'attempt_id':'A','generation':1,'current_generation':2,'mode':case['mode'],'eligible':False,'outcome':'NO_EFFECT','started_ns':now,'finished_ns':now}; pub.events.append(apub)
        else:
            raise RuntimeError('A stage invalid '+ar['state'])
        after_a=image_receipt(canonical,exp);put(d/'after-a-callback.json',after_a)
        time.sleep(.08);final=image_receipt(canonical,exp);shutil.copy2(canonical,d/'final.png');put(d/'final.json',final);put(d/'publish-events.json',pub.events)
        put(d/'process.json',{'id':case['id'],'mode':case['mode'],'a_returncode':ap.returncode,'b_returncode':bp.returncode,'a_spawned_ns':aspawn,'stop_finished_ns':sf,'b_spawned_ns':bspawn,'b_reaped_ns':breap,'a_reaped_ns':areap,'b_started_before_a_reap':bspawn<areap,'b_publish_finished_ns':bpub['finished_ns'],'a_callback_finished_ns':apub['finished_ns']})
        put(d/'done.json',{'id':case['id'],'done_ns':time.perf_counter_ns()});print(json.dumps({'id':case['id'],'mode':case['mode'],'after_b':bcan['state'],'after_a':after_a['state'],'final':final['state'],'a_publish':apub['outcome']}),flush=True)
        for _ in range(1000):
            if (d/'close-worker').exists():return
            time.sleep(.01)
    finally:
        for p in (bp,ap):
            if p is not None and p.poll() is None:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                p.wait(timeout=2)
        ae.close();be.close()
if __name__=='__main__':
    try:main()
    except Exception as e:
        d=Path(sys.argv[1]).resolve().parent;(d/'worker-failure.json').write_text(json.dumps({'type':type(e).__name__,'error':str(e)},indent=2));raise
