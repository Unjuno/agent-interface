#!/usr/bin/env /usr/bin/python3
import argparse, json, os, shutil, socket, subprocess, tempfile, time
from pathlib import Path
import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.awt import Point, Size

def prop(name,value): p=PropertyValue();p.Name=name;p.Value=value;return p
def free_port(): s=socket.socket();s.bind(('127.0.0.1',0));p=s.getsockname()[1];s.close();return p
def write_json(path,obj): Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def connect(port,timeout=8):
    ctx=uno.getComponentContext(); r=ctx.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',ctx); end=time.monotonic()+timeout; last=None
    while time.monotonic()<end:
        try:return r.resolve(f'uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext')
        except Exception as e:last=e;time.sleep(.05)
    raise RuntimeError(f'connect timeout:{last}')
def x(s): return int(s.getPosition().X)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--scenario',choices=['macro_stable','macro_stale_before_call'],required=True);ap.add_argument('--case-id',required=True);ap.add_argument('--out-dir',required=True);ap.add_argument('--macro-source',required=True);ap.add_argument('--external-writer',required=True);args=ap.parse_args()
    out=Path(args.out_dir);out.mkdir(parents=True,exist_ok=False);profile=Path(tempfile.mkdtemp(prefix=f'lomac-{args.case_id}-'));mDir=profile/'user'/'Scripts'/'python';mDir.mkdir(parents=True);shutil.copyfile(args.macro_source,mDir/'conditional_macro.py')
    port=free_port();cmd=['soffice','--headless','--nologo','--nodefault','--nofirststartwizard',f'-env:UserInstallation=file://{profile}',f'--accept=socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext'];env=os.environ.copy();env['PYTHONPATH']='/usr/lib/python3/dist-packages'
    proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env);events=[];result={'case_id':args.case_id,'scenario':args.scenario,'port':port};doc=desk=None
    try:
        remote=connect(port);smgr=remote.ServiceManager;desk=smgr.createInstanceWithContext('com.sun.star.frame.Desktop',remote);doc=desk.loadComponentFromURL('private:factory/sdraw','_blank',0,(prop('Hidden',True),));page=doc.getDrawPages().getByIndex(0)
        A=doc.createInstance('com.sun.star.drawing.RectangleShape');A.Name='A';A.setPosition(Point(1000,1000));A.setSize(Size(1000,1000));page.add(A);B=doc.createInstance('com.sun.star.drawing.RectangleShape');B.Name='B';B.setPosition(Point(5000,1000));B.setSize(Size(1000,1000));page.add(B)
        events.append({'event':'fixture_ready','t_ns':time.monotonic_ns(),'a_x':x(A),'b_x':x(B)})
        external=None
        if args.scenario=='macro_stale_before_call':
            t0=time.monotonic_ns();cp=subprocess.run(['/usr/bin/python3',args.external_writer,str(port),'1700'],capture_output=True,text=True,timeout=10);t1=time.monotonic_ns();external={'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr,'parent_start_ns':t0,'parent_end_ns':t1};
            try:external['json']=json.loads(cp.stdout.strip())
            except Exception as e:external['json_error']=repr(e)
            events.append({'event':'external_write_complete','t_ns':t1,'a_x_now':x(A),'returncode':cp.returncode})
        result['external']=external
        factory=smgr.createInstanceWithContext('com.sun.star.script.provider.MasterScriptProviderFactory',remote);provider=factory.createScriptProvider('');script=provider.getScript('vnd.sun.star.script:conditional_macro.py$apply_if_expected?language=Python&location=user')
        t0=time.monotonic_ns();inv=script.invoke((doc,'A',1000,1200),(),());t1=time.monotonic_ns();macro_ret=json.loads(inv[0]);events.append({'event':'macro_complete','t_ns':t1,'macro_return':macro_ret,'a_x_now':x(A)})
        result['macro_start_ns']=t0;result['macro_end_ns']=t1;result['macro_return']=macro_ret;result['final_a_x']=x(A);result['final_b_x']=x(B)
        if args.scenario=='macro_stable': ok=macro_ret.get('status')=='APPLIED' and macro_ret.get('before_x')==1000 and macro_ret.get('after_x')==1200 and x(A)==1200 and x(B)==5000
        else:
            ej=(external or {}).get('json') or {};ok=external['returncode']==0 and ej.get('after_x')==1700 and macro_ret.get('status')=='REFUSED' and macro_ret.get('before_x')==1700 and x(A)==1700 and x(B)==5000 and external['parent_end_ns'] < t0
        result['case_gate_pass']=bool(ok);write_json(out/'events.json',events);write_json(out/'result.json',result);return 0 if ok else 3
    except Exception as e:
        result['exception']=f'{type(e).__name__}:{e}';write_json(out/'events.json',events);write_json(out/'result.json',result);return 4
    finally:
        try:
            if doc is not None: doc.close(True)
        except Exception:
            try: doc.dispose()
            except Exception: pass
        try:
            if desk is not None: desk.terminate()
        except Exception: pass
        try: proc.wait(timeout=3)
        except Exception: proc.terminate();proc.wait(timeout=2)
        stdout,stderr=proc.communicate() if proc.stdout else ('','');(out/'soffice_stdout.txt').write_text(stdout or '');(out/'soffice_stderr.txt').write_text(stderr or '')
if __name__=='__main__':raise SystemExit(main())
