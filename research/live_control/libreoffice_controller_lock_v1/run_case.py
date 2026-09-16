#!/usr/bin/env /usr/bin/python3
import argparse, hashlib, json, os, socket, subprocess, tempfile, time
from pathlib import Path
import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.awt import Point, Size


def prop(name, value):
    p = PropertyValue(); p.Name = name; p.Value = value; return p

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close(); return port

def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n', encoding='utf-8')

def connect(port, timeout_s=8.0):
    ctx = uno.getComponentContext()
    resolver = ctx.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', ctx)
    deadline = time.monotonic() + timeout_s
    last = None
    while time.monotonic() < deadline:
        try:
            return resolver.resolve(f'uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext')
        except Exception as e:
            last = e; time.sleep(0.05)
    raise RuntimeError(f'UNO connect timeout: {last}')

def x(shape): return int(shape.getPosition().X)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scenario', choices=['locked_stable','locked_intervening_write'], required=True)
    ap.add_argument('--case-id', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--external-writer', required=True)
    args = ap.parse_args()
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=False)
    profile = Path(tempfile.mkdtemp(prefix=f'lo-{args.case_id}-'))
    port = free_port()
    office_cmd = ['soffice','--headless','--nologo','--nodefault','--nofirststartwizard',
                  f'-env:UserInstallation=file://{profile}',
                  f'--accept=socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext']
    proc = subprocess.Popen(office_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    events=[]
    result={'case_id':args.case_id,'scenario':args.scenario,'port':port,'office_cmd':office_cmd}
    doc=None; desktop=None
    try:
        remote=connect(port); smgr=remote.ServiceManager
        desktop=smgr.createInstanceWithContext('com.sun.star.frame.Desktop', remote)
        doc=desktop.loadComponentFromURL('private:factory/sdraw','_blank',0,(prop('Hidden', True),))
        pages=doc.getDrawPages(); page=pages.getByIndex(0)
        A=doc.createInstance('com.sun.star.drawing.RectangleShape'); A.Name='A'; A.setPosition(Point(1000,1000)); A.setSize(Size(1000,1000)); page.add(A)
        B=doc.createInstance('com.sun.star.drawing.RectangleShape'); B.Name='B'; B.setPosition(Point(5000,1000)); B.setSize(Size(1000,1000)); page.add(B)
        events.append({'event':'fixture_ready','t_ns':time.monotonic_ns(),'a_x':x(A),'b_x':x(B)})
        observed=x(A); result['observed_a_x']=observed
        doc.lockControllers()
        t_lock=time.monotonic_ns(); lock_state=bool(doc.hasControllersLocked())
        events.append({'event':'lock_verified','t_ns':t_lock,'locked':lock_state})
        result['lock_verified']=lock_state
        external=None
        if args.scenario=='locked_intervening_write':
            t0=time.monotonic_ns()
            cp=subprocess.run(['/usr/bin/python3', args.external_writer, str(port), '1700'], capture_output=True, text=True, timeout=10)
            t1=time.monotonic_ns()
            external={'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr,'parent_start_ns':t0,'parent_end_ns':t1}
            try: external['json']=json.loads(cp.stdout.strip())
            except Exception as e: external['json_error']=repr(e)
            events.append({'event':'external_write_complete','t_ns':t1,'returncode':cp.returncode,'a_x_now':x(A)})
        result['external']=external
        stale_target=observed+200
        p=A.getPosition(); p.X=stale_target
        t_sw0=time.monotonic_ns(); A.setPosition(p); t_sw1=time.monotonic_ns()
        events.append({'event':'stale_write','t_ns':t_sw1,'requested_x':stale_target,'a_x_now':x(A)})
        result['stale_write_start_ns']=t_sw0; result['stale_write_end_ns']=t_sw1
        result['locked_before_unlock']=bool(doc.hasControllersLocked())
        doc.unlockControllers(); t_unlock=time.monotonic_ns()
        events.append({'event':'unlock','t_ns':t_unlock,'locked_after':bool(doc.hasControllersLocked())})
        result['final_a_x']=x(A); result['final_b_x']=x(B); result['locked_after_unlock']=bool(doc.hasControllersLocked())
        ok = lock_state and result['locked_before_unlock'] and not result['locked_after_unlock'] and result['final_b_x']==5000
        if args.scenario=='locked_stable': ok = ok and result['final_a_x']==1200
        else:
            ej=(external or {}).get('json') or {}
            ok = ok and external['returncode']==0 and ej.get('ok') is True and ej.get('lock_seen_before') is True and ej.get('lock_seen_after') is True and ej.get('before_x')==1000 and ej.get('after_x')==1700 and result['final_a_x']==1200
        result['case_gate_pass']=bool(ok)
        write_json(out/'events.json', events); write_json(out/'result.json', result)
        return 0 if ok else 3
    except Exception as e:
        result['exception']=f'{type(e).__name__}:{e}'
        try: write_json(out/'events.json', events); write_json(out/'result.json', result)
        except Exception: pass
        return 4
    finally:
        try:
            if doc is not None and bool(doc.hasControllersLocked()): doc.unlockControllers()
        except Exception: pass
        try:
            if doc is not None: doc.close(True)
        except Exception:
            try:
                if doc is not None: doc.dispose()
            except Exception: pass
        try:
            if desktop is not None: desktop.terminate()
        except Exception: pass
        try: proc.wait(timeout=3)
        except Exception:
            proc.terminate()
            try: proc.wait(timeout=2)
            except Exception: proc.kill(); proc.wait()
        stdout, stderr = proc.communicate() if proc.stdout else ('','')
        (out/'soffice_stdout.txt').write_text(stdout or '', encoding='utf-8')
        (out/'soffice_stderr.txt').write_text(stderr or '', encoding='utf-8')

if __name__=='__main__': raise SystemExit(main())
