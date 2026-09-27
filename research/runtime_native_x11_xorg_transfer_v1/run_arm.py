#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, re, signal, subprocess, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def run(cmd, **kw): return subprocess.run(cmd, text=True, **kw)
def wait_display(display, timeout=10):
    end=time.time()+timeout
    while time.time()<end:
        if run(['xdpyinfo','-display',display],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:return True
        time.sleep(.1)
    return False
def find_calc(display, timeout=20):
    env={**os.environ,'DISPLAY':display};end=time.time()+timeout
    while time.time()<end:
        p=run(['wmctrl','-lx'],env=env,capture_output=True)
        for line in p.stdout.splitlines():
            if 'libreoffice.libreoffice-calc' in line.lower() and 'task.xlsx' in line.lower():return line.split()[0]
        time.sleep(.1)
    return None
def stop(p):
    if p is None:return
    try:p.terminate();p.wait(timeout=5)
    except Exception:
        try:p.kill();p.wait(timeout=2)
        except Exception:pass

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--controller',type=Path,required=True);ap.add_argument('--pacing-ms',type=int,choices=[1,12],required=True);ap.add_argument('--display-num',type=int,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False); display=f':{a.display_num}'; env={**os.environ,'DISPLAY':display}
    task=a.out/'task.xlsx'; profile=a.out/'profile';profile.mkdir();
    seed=run([sys.executable,str(HERE/'seed_workbook.py'),'--out',str(task)],capture_output=True);(a.out/'seed.stdout').write_text(seed.stdout);(a.out/'seed.stderr').write_text(seed.stderr)
    if seed.returncode: raise SystemExit('seed failed')
    lock=Path(f'/tmp/.X{a.display_num}-lock'); sock=Path(f'/tmp/.X11-unix/X{a.display_num}'); lock.unlink(missing_ok=True);sock.unlink(missing_ok=True)
    xlog=a.out/'Xorg.log'; xo=(a.out/'xorg.stdout').open('w'); xe=(a.out/'xorg.stderr').open('w')
    xorg=subprocess.Popen(['Xorg',display,'-config',str(HERE/'xorg-dummy.conf'),'-noreset','-nolisten','tcp','-ac','-logfile',str(xlog)],stdout=xo,stderr=xe,text=True)
    ob=None;lo=None
    try:
        if not wait_display(display): raise RuntimeError('Xorg not ready')
        xd=run(['xdpyinfo','-display',display],capture_output=True,check=True).stdout
        server={'display':display,'vendor':re.search(r'vendor string:\s*(.+)',xd).group(1).strip(),'release':int(re.search(r'vendor release number:\s*(\d+)',xd).group(1)),'xorg_version':run(['Xorg','-version'],capture_output=True).stderr.strip() or run(['Xorg','-version'],capture_output=True).stdout.strip(),'xtest':'XTEST' in run(['xdpyinfo','-display',display,'-queryExtensions'],capture_output=True).stdout,'dimensions':re.search(r'dimensions:\s*([^\n]+)',xd).group(1).strip()}
        (a.out/'server.json').write_text(json.dumps(server,indent=2)+'\n')
        if not server['xtest']: raise RuntimeError('XTEST absent')
        ob=subprocess.Popen(['openbox'],env=env,stdout=(a.out/'openbox.stdout').open('w'),stderr=(a.out/'openbox.stderr').open('w'),text=True);time.sleep(.5)
        uri=profile.resolve().as_uri();lo=subprocess.Popen(['libreoffice','--nologo','--nodefault','--nolockcheck','--norestore',f'-env:UserInstallation={uri}','--calc',str(task)],env=env,stdout=(a.out/'lo.stdout').open('w'),stderr=(a.out/'lo.stderr').open('w'),text=True)
        xid=find_calc(display)
        if not xid: raise RuntimeError('Calc window not found')
        (a.out/'window.json').write_text(json.dumps({'xid':xid},indent=2)+'\n');time.sleep(1)
        cp=run([str(a.controller),'--display',display,'--window-id',xid,'--pacing-ms',str(a.pacing_ms),'--out',str(a.out/'execution.json')],capture_output=True)
        (a.out/'controller.stdout').write_text(cp.stdout);(a.out/'controller.stderr').write_text(cp.stderr);(a.out/'controller.exitcode').write_text(str(cp.returncode)+'\n')
        time.sleep(1);stop(lo);lo=None
        sp=run([sys.executable,str(HERE/'score_workbook.py'),'--workbook',str(task),'--out',str(a.out/'score.json')],capture_output=True)
        (a.out/'scorer.stdout').write_text(sp.stdout);(a.out/'scorer.stderr').write_text(sp.stderr);(a.out/'scorer.exitcode').write_text(str(sp.returncode)+'\n')
        execution=json.loads((a.out/'execution.json').read_text()) if (a.out/'execution.json').exists() else None
        score=json.loads((a.out/'score.json').read_text()) if (a.out/'score.json').exists() else None
        controls=bool(execution and execution.get('passed_transport') and execution['stale']['accepted'] is False and execution['stale']['error']=='STALE_OBSERVATION' and execution['stale']['injected_events']==0 and execution['task']['final_release_verified'] and execution['confirm']['final_release_verified'])
        passed=cp.returncode==0 and sp.returncode==0 and controls and score and score['passed']
        report={'schema':'agent-interface/native-x11-xorg-transfer-arm-v1','dependency_source_freeze':'48030f5829690bdd3209d05974e390d88e7742a9','dependency_retained_head':'3f6e46556e44983d39e306a58ca80c688e7b2af5','pacing_ms':a.pacing_ms,'controller_sha256':sha(a.controller),'server':server,'controller_exit':cp.returncode,'scorer_exit':sp.returncode,'controls_passed':controls,'score':score,'execution':execution,'passed':passed}
        (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0 if passed else 1
    finally:
        stop(lo);stop(ob);stop(xorg);xo.close();xe.close()
if __name__=='__main__':raise SystemExit(main())
