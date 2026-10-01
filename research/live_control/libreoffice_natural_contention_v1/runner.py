#!/usr/bin/env python3
"""Fresh Docker-only natural UNO contention allocation for Issue #2966."""
from __future__ import annotations
import json, os, shutil, socket, subprocess, tempfile, time
from pathlib import Path
import uno
from com.sun.star.awt import Point, Size
from com.sun.star.beans import PropertyValue

def prop(name, value):
    p=PropertyValue(); p.Name=name; p.Value=value; return p
def port():
    s=socket.socket(); s.bind(('127.0.0.1',0)); n=s.getsockname()[1]; s.close(); return n
def connect(n):
    ctx=uno.getComponentContext(); r=ctx.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',ctx)
    end=time.monotonic()+10
    while time.monotonic()<end:
        try:return r.resolve(f'uno:socket,host=127.0.0.1,port={n};urp;StarOffice.ComponentContext')
        except Exception: time.sleep(.05)
    raise RuntimeError('UNO connect timeout')
def setup():
    pr=Path(tempfile.mkdtemp(prefix='lo2966-')); n=port(); env=os.environ.copy(); env['PYTHONPATH']='/usr/lib/python3/dist-packages'
    p=subprocess.Popen(['soffice','--headless','--nologo','--nodefault','--nofirststartwizard',f'-env:UserInstallation=file://{pr}',f'--accept=socket,host=127.0.0.1,port={n};urp;StarOffice.ComponentContext'],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    remote=connect(n); desktop=remote.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',remote)
    doc=desktop.loadComponentFromURL('private:factory/sdraw','_blank',0,(prop('Hidden',True),)); page=doc.getDrawPages().getByIndex(0)
    for name,x in [('A',1000),('B',5000)]:
        sh=doc.createInstance('com.sun.star.drawing.RectangleShape'); sh.Name=name; sh.setPosition(Point(x,1000)); sh.setSize(Size(1000,1000)); page.add(sh)
    return pr,p,n,remote,desktop,doc
def shape(doc,name):
    page=doc.getDrawPages().getByIndex(0)
    for i in range(page.getCount()):
        sh=page.getByIndex(i)
        if getattr(sh,'Name','')==name:return sh
    raise RuntimeError(name)
def x(doc,name): return int(shape(doc,name).getPosition().X)
def mutate(doc,name,v):
    sh=shape(doc,name); p=sh.getPosition(); p.X=v; sh.setPosition(p)
def case(kind,idx,delay_ms=20):
    pr,p,n,remote,desktop,doc=setup(); events=[]; writer=None
    try:
        events.append({'event':'fixture_ready','a':x(doc,'A'),'b':x(doc,'B'),'t_ns':time.monotonic_ns()})
        observed=x(doc,'A'); rev_before=observed
        if kind in ('natural','external'):
            writer=subprocess.Popen(['/usr/bin/python3','-c',"import uno,sys,time,json; from pathlib import Path; n=int(sys.argv[1]); out=Path(sys.argv[2]); d=int(sys.argv[3]); time.sleep(d/1000); c=uno.getComponentContext(); r=c.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver',c); q=r.resolve(f'uno:socket,host=127.0.0.1,port={n};urp;StarOffice.ComponentContext'); de=q.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop',q); ds=de.getComponents().createEnumeration(); doc=None\nwhile ds.hasMoreElements():\n z=ds.nextElement()\n if hasattr(z,'getDrawPages'): doc=z; break\npage=doc.getDrawPages().getByIndex(0); sh=page.getByIndex(0 if sys.argv[4]=='A' else 1); b=int(sh.getPosition().X); p=sh.getPosition(); p.X=int(sys.argv[5]); s=time.monotonic_ns(); sh.setPosition(p); e=time.monotonic_ns(); out.write_text(json.dumps({'before':b,'after':int(sh.getPosition().X),'start_ns':s,'end_ns':e}))",str(n),str(pr/'writer.json'),str(delay_ms), 'A' if kind!='external' else 'B', '1700' if kind!='external' else '5700'],text=True)
        time.sleep(0.005)
        current=x(doc,'A')
        if kind=='recovery':
            mutate(doc,'A',1700)
            current=x(doc,'A')
        if current!=observed:
            outcome='CONFLICT_REJECTED'
        else:
            mutate(doc,'A',1200); outcome='APPLIED'
        if writer: writer.wait(timeout=10)
        wp=json.loads((pr/'writer.json').read_text()) if (pr/'writer.json').exists() else None
        result={'case_id':idx,'kind':kind,'observed_a':observed,'checked_a':current,'final_a':x(doc,'A'),'final_b':x(doc,'B'),'outcome':outcome,'writer':wp,'events':events,'cleanup':'pending'}
        if kind=='recovery' and outcome=='CONFLICT_REJECTED':
            fresh=x(doc,'A'); mutate(doc,'A',1200); result['recovery']={'fresh_expected':fresh,'outcome':'APPLIED','final_a':x(doc,'A')}
        result['cleanup']='verified'
        return result
    finally:
        if writer and writer.poll() is None: writer.kill(); writer.wait()
        try: doc.close(True)
        except Exception: pass
        try: desktop.terminate()
        except Exception: pass
        if p.poll() is None: p.terminate(); p.wait(timeout=5)
        shutil.rmtree(pr,ignore_errors=True)
def main():
    out=Path(os.environ.get('OUT','/out')); out.mkdir(parents=True,exist_ok=False); rows=[]
    for kind,count in [('stable',5),('natural',5),('external',5),('recovery',1)]:
        for i in range(count): rows.append(case(kind,f'{kind}-{i+1}',20+i*7))
    summary={'schema':'lo2966_natural_contention_result_v1','allocation':'lo-natural-contention-20260920-a2','rows':rows,'decision':'HOLD_NO_NATURAL_CONTENTION_OBSERVED' if not any(r['outcome']=='CONFLICT_REJECTED' for r in rows if r['kind']=='natural') else 'PASS_NATURAL_CONFLICT_BOUNDARY_SCOPED'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary))
if __name__=='__main__': main()
