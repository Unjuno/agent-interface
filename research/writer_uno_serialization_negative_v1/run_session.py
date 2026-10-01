#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys,time,uuid
from pathlib import Path
from odf.opendocument import OpenDocumentText
from odf.text import P
HERE=Path(__file__).resolve().parent

def run_sys(args,env=None,timeout=15): return subprocess.run(['/usr/bin/python3',*map(str,args)],env=env,text=True,capture_output=True,timeout=timeout)
def wait_display(env):
    for _ in range(100):
        if subprocess.run(['xdpyinfo'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:return
        time.sleep(.03)
    raise RuntimeError('display unavailable')
def parse_one(s): return json.loads(s.strip().splitlines()[-1])
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--arm',required=True,choices=['compare_set','recheck_set','controllers_lock_set']); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); out=a.out.resolve(); out.mkdir(parents=True,exist_ok=False)
    if os.environ.get('AGENT_INTERFACE_PRIVATE_XVFB')!='1': raise RuntimeError('private Xvfb marker required')
    doc=OpenDocumentText();doc.text.addElement(P(text='book'));odt=out/'task.odt';doc.save(str(odt)); url=odt.as_uri(); pipe='unoneg_'+uuid.uuid4().hex[:12]
    env=os.environ.copy(); profile=(out/'profile').resolve();
    ob=subprocess.Popen(['openbox'],env=env,stdout=(out/'openbox.stdout').open('w'),stderr=(out/'openbox.stderr').open('w'))
    lo=None
    try:
        wait_display(env)
        lo=subprocess.Popen(['libreoffice',f'-env:UserInstallation=file://{profile}','--nologo','--nodefault','--nofirststartwizard','--norestore',f'--accept=pipe,name={pipe};urp;StarOffice.ComponentContext',str(odt)],env=env,stdout=(out/'lo.stdout').open('w'),stderr=(out/'lo.stderr').open('w'))
        # observer is also the readiness gate.
        ready=None
        for _ in range(120):
            r=run_sys([HERE/'observe.py','--pipe',pipe,'--url',url],env=env,timeout=3)
            if r.returncode==0:
                ready=parse_one(r.stdout);break
            time.sleep(.04)
        if ready is None: raise RuntimeError('writer UNO readiness failed')
        barrier=out/'barrier'; cp=subprocess.Popen(['/usr/bin/python3',str(HERE/'candidate.py'),'--pipe',pipe,'--url',url,'--arm',a.arm,'--barrier',str(barrier)],env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        for _ in range(500):
            if (barrier/'guard.json').exists(): break
            if cp.poll() is not None: break
            time.sleep(.004)
        if not (barrier/'guard.json').exists():
            so,se=cp.communicate(timeout=2); raise RuntimeError(f'candidate guard failed rc={cp.returncode} out={so} err={se}')
        guard=json.loads((barrier/'guard.json').read_text())
        m=run_sys([HERE/'mutator.py','--pipe',pipe,'--url',url],env=env); (out/'mutator.stdout').write_text(m.stdout);(out/'mutator.stderr').write_text(m.stderr)
        if m.returncode: raise RuntimeError('mutator failed '+m.stderr)
        mut=parse_one(m.stdout); (barrier/'continue').write_text('1\n')
        so,se=cp.communicate(timeout=10); (out/'candidate.stdout').write_text(so);(out/'candidate.stderr').write_text(se)
        if cp.returncode: raise RuntimeError('candidate failed '+se)
        cand=parse_one(so); o=run_sys([HERE/'observe.py','--pipe',pipe,'--url',url],env=env); final=parse_one(o.stdout)
        passed=(guard['initial']=='book' and mut['before']=='book' and mut['after']=='boox' and cand['prewrite']=='boox' and cand['post']=='bookkeeperoffice' and final['text']=='bookkeeperoffice' and (a.arm!='controllers_lock_set' or mut['controllers_locked'] is True))
        rep={'schema':'agent-interface/writer-uno-serialization-negative-session-v1','arm':a.arm,'guard':guard,'mutator':mut,'candidate':cand,'final':final,'passed_negative':passed,'input_sha256':hashlib.sha256(odt.read_bytes()).hexdigest()}
        (out/'report.json').write_text(json.dumps(rep,indent=2)+'\n'); print(json.dumps(rep)); return 0 if passed else 1
    finally:
        if lo and lo.poll() is None: lo.terminate()
        if lo:
            try:lo.wait(timeout=2)
            except:lo.kill()
        if ob.poll() is None: ob.terminate()
if __name__=='__main__': raise SystemExit(main())
