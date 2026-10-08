#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path
from openpyxl import Workbook
from Xlib import display
HERE=Path(__file__).resolve().parent

def wait_display(env,name):
    for _ in range(100):
        if subprocess.run(['xdpyinfo','-display',name],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:return
        time.sleep(.04)
    raise RuntimeError('Xvfb not ready')
def find_calc(name,timeout=10):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        d=display.Display(name)
        def walk(w):
            try: kids=w.query_tree().children
            except Exception:return None
            for c in kids:
                try: cls=c.get_wm_class()
                except Exception: cls=None
                if cls and any('libreoffice-calc' in str(x).lower() for x in cls): return c.id
                z=walk(c)
                if z is not None:return z
            return None
        f=walk(d.screen().root); d.close()
        if f is not None:return f
        time.sleep(.05)
    raise RuntimeError('Calc window not found')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--display',required=True); ap.add_argument('--pacing-ms',type=float,required=True); a=ap.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
    xlsx=a.out/'task.xlsx'; wb=Workbook(); ws=wb.active
    for i in range(1,17): ws.cell(i,1).value=f'old-{i}'
    wb.save(xlsx); input_sha=hashlib.sha256(xlsx.read_bytes()).hexdigest()
    auth=a.out/'Xauthority'; auth.write_bytes(b''); env=os.environ.copy(); env.update({'DISPLAY':a.display,'XAUTHORITY':str(auth)}); os.environ.update({'DISPLAY':a.display,'XAUTHORITY':str(auth)})
    xvfb=subprocess.Popen(['Xvfb',a.display,'-screen','0','1024x768x24','-nolisten','tcp','-ac'],env=env,stdout=(a.out/'xvfb.stdout').open('w'),stderr=(a.out/'xvfb.stderr').open('w')); ob=lo=None
    try:
        wait_display(env,a.display); ob=subprocess.Popen(['openbox'],env=env,stdout=(a.out/'openbox.stdout').open('w'),stderr=(a.out/'openbox.stderr').open('w'))
        profile=f'file://{a.out}/profile'; lo=subprocess.Popen(['libreoffice',f'-env:UserInstallation={profile}','--nologo','--nodefault','--nofirststartwizard','--norestore',str(xlsx)],env=env,stdout=(a.out/'libreoffice.stdout').open('w'),stderr=(a.out/'libreoffice.stderr').open('w'))
        wid=find_calc(a.display); time.sleep(.4)
        child=env.copy(); child['AGENT_INTERFACE_PORTABLE_ORACLE']=os.environ['AGENT_INTERFACE_PORTABLE_ORACLE']; child['AGENT_INTERFACE_X11_BACKEND']=os.environ['AGENT_INTERFACE_X11_BACKEND']; child['AGENT_INTERFACE_OFFICE_V0']=os.environ['AGENT_INTERFACE_OFFICE_V0']
        exdir=a.out/'execution'; r=subprocess.run([sys.executable,str(HERE/'experiment.py'),'--display',a.display,'--window-id',str(wid),'--pacing-ms',str(a.pacing_ms),'--out',str(exdir)],env=child,text=True,capture_output=True)
        (a.out/'executor.stdout').write_text(r.stdout); (a.out/'executor.stderr').write_text(r.stderr); (a.out/'executor.exitcode').write_text(str(r.returncode)+'\n')
        time.sleep(.8)
        s=subprocess.run([sys.executable,str(HERE/'score_workbook.py'),'--xlsx',str(xlsx),'--out',str(a.out/'score.json')],text=True,capture_output=True)
        (a.out/'scorer.stdout').write_text(s.stdout); (a.out/'scorer.stderr').write_text(s.stderr); (a.out/'scorer.exitcode').write_text(str(s.returncode)+'\n')
        rep={'schema':'agent-interface/office-x11-text-pacing-arm-v1','pacing_ms':a.pacing_ms,'window_id':wid,'input_sha256':input_sha,'output_sha256':hashlib.sha256(xlsx.read_bytes()).hexdigest(),'executor_exitcode':r.returncode,'scorer_exitcode':s.returncode,'passed':r.returncode==0 and s.returncode==0}
        (a.out/'report.json').write_text(json.dumps(rep,indent=2)+'\n'); print(json.dumps(rep,indent=2)); return 0 if rep['passed'] else 1
    finally:
        if lo and lo.poll() is None: lo.terminate()
        if lo:
            try: lo.wait(timeout=2)
            except subprocess.TimeoutExpired: lo.kill()
        if ob and ob.poll() is None: ob.terminate()
        xvfb.terminate()
if __name__=='__main__': raise SystemExit(main())
