#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,subprocess,time,shutil
from pathlib import Path
from odf.opendocument import OpenDocumentText
from odf.text import P
from logic import gate,classify_candidate
HERE=Path(__file__).resolve().parent
ORDER=['baseline_gap','append_then_replace','replace_then_append','race_simultaneous','race_candidate_delayed','race_append_delayed','stale_uid']
def mk(p):d=OpenDocumentText();d.text.addElement(P(text='book'));d.save(str(p))
def wait_display(env,name):
 for _ in range(150):
  if subprocess.run(['xdpyinfo','-display',name],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:return
  time.sleep(.03)
 raise RuntimeError('display')
def run_worker(pipe,url,cmd,*args,async_=False):
 a=['/usr/bin/python3',str(HERE/'uno_worker.py'),'--pipe',pipe,'--url',url,cmd,*args]
 if async_:return subprocess.Popen(a,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 p=subprocess.run(a,text=True,capture_output=True)
 data=json.loads(p.stdout) if p.stdout.strip() else {'ok':False,'error':p.stderr}
 return p.returncode,data
def collect(p):
 o,e=p.communicate(timeout=10);return p.returncode,json.loads(o) if o.strip() else {'ok':False,'error':e}
def wf(p):
 for _ in range(4000):
  if Path(p).exists():return
  time.sleep(.001)
 raise RuntimeError('ready')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--display',required=True);ap.add_argument('--pipe',required=True);ap.add_argument('--block',type=int,required=True);a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 doc=out/'task.odt';mk(doc);url=doc.resolve().as_uri();auth=out/'Xauthority';auth.write_bytes(b'');env=os.environ.copy();env.update(DISPLAY=a.display,XAUTHORITY=str(auth));xv=subprocess.Popen(['Xvfb',a.display,'-screen','0','1024x768x24','-ac','-nolisten','tcp'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);ob=lo=None;rows=[]
 def get():return run_worker(a.pipe,url,'get')[1]
 def reset():
  code,r=run_worker(a.pipe,url,'set','--text','book');
  if code:raise RuntimeError(r)
 def barriers(tag):
  r1=out/f'{tag}.r1';r2=out/f'{tag}.r2';g=out/f'{tag}.go'
  for p in (r1,r2,g):p.unlink(missing_ok=True)
  return r1,r2,g
 try:
  wait_display(env,a.display);ob=subprocess.Popen(['openbox'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);lo=subprocess.Popen(['libreoffice',f'-env:UserInstallation=file://{out}/profile','--nologo','--nodefault','--nofirststartwizard','--norestore',f'--accept=pipe,name={a.pipe};urp;StarOffice.ServiceManager',str(doc)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  for _ in range(250):
   try:
    initial=get()
    if initial.get('ok'):break
   except:pass
   time.sleep(.03)
  uid=initial['uid']
  for cond in ORDER:
   if cond=='stale_uid':
    reset(); old=get()['uid'];code,reopen=run_worker(a.pipe,url,'close_reopen','--uid',old);time.sleep(.08);code2,cand=run_worker(a.pipe,url,'replace','--uid',old,'--text','bookkeeperoffice');final=get()['text'];row={'condition':cond,'candidate':cand,'old_uid':old,'new_uid':reopen.get('new_uid'),'final':final,'refused':code2!=0,'count':None,'gate_pass':gate(cond,None,final,code2!=0)};rows.append(row);continue
   reset();r1,r2,g=barriers(cond)
   if cond=='baseline_gap':
    b=run_worker(a.pipe,url,'baseline','--uid',uid,'--text','bookkeeperoffice','--ready',str(r1),'--go',str(g),async_=True);wf(r1);_,app=run_worker(a.pipe,url,'append','--uid',uid,'--text','x');g.touch();_,base=collect(b);final=get()['text'];row={'condition':cond,'baseline':base,'append':app,'final':final,'refused':False,'count':None,'gate_pass':gate(cond,None,final)};rows.append(row);continue
   if cond=='append_then_replace':
    c=run_worker(a.pipe,url,'replace','--uid',uid,'--text','bookkeeperoffice','--ready',str(r1),'--go',str(g),async_=True);wf(r1);_,app=run_worker(a.pipe,url,'append','--uid',uid,'--text','x');g.touch();_,cand=collect(c);final=get()['text'];row={'condition':cond,'candidate':cand,'append':app,'final':final,'count':cand.get('count'),'refused':False,'class':classify_candidate(cand.get('count'),final),'gate_pass':gate(cond,cand.get('count'),final)};rows.append(row);continue
   if cond=='replace_then_append':
    _,cand=run_worker(a.pipe,url,'replace','--uid',uid,'--text','bookkeeperoffice');_,app=run_worker(a.pipe,url,'append','--uid',uid,'--text','x');final=get()['text'];row={'condition':cond,'candidate':cand,'append':app,'final':final,'count':cand.get('count'),'refused':False,'class':classify_candidate(cand.get('count'),final),'gate_pass':gate(cond,cand.get('count'),final)};rows.append(row);continue
   cd,ad=(10000,0) if cond=='race_candidate_delayed' else ((0,10000) if cond=='race_append_delayed' else (0,0))
   c=run_worker(a.pipe,url,'replace','--uid',uid,'--text','bookkeeperoffice','--ready',str(r1),'--go',str(g),'--delay-us',str(cd),async_=True);m=run_worker(a.pipe,url,'append','--uid',uid,'--text','x','--ready',str(r2),'--go',str(g),'--delay-us',str(ad),async_=True);wf(r1);wf(r2);g.touch();_,cand=collect(c);_,app=collect(m);final=get()['text'];row={'condition':cond,'candidate':cand,'append':app,'final':final,'count':cand.get('count'),'refused':False,'class':classify_candidate(cand.get('count'),final),'gate_pass':gate(cond,cand.get('count'),final)};rows.append(row)
  rep={'schema':'agent-interface/writer-uno-compare-replace-block-v1','block':a.block,'order':ORDER,'rows':rows,'passed':all(r['gate_pass'] for r in rows)};(out/'report.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep));return 0 if rep['passed'] else 1
 finally:
  for p in (lo,ob,xv):
   if p and p.poll() is None:p.terminate()
  for p in (lo,ob,xv):
   if p:
    try:p.wait(timeout=3)
    except:p.kill()
if __name__=='__main__':raise SystemExit(main())
