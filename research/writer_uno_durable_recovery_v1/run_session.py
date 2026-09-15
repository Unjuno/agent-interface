#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,subprocess,sys,time
from pathlib import Path
from Xlib import display
from candidate import Observation,precheck_bound,final_focus_guard
from x11_writer import *
HERE=Path(__file__).resolve().parent;DESIRED='bookkeeperoffice';A0='book';B0='bookk';MAX_AGE_NS=500_000_000

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--display',required=True);ap.add_argument('--pipe',required=True);ap.add_argument('--condition',choices=['fresh','stale_uid','wrong_doc','focus_drift','stale_age','text_changed'],required=True);a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 A=out/'a-target.odt';B=out/'b-sidecar.odt';mk(A,A0);mk(B,B0);auth=out/'Xauthority';auth.write_bytes(b'');env=os.environ.copy();env.update(DISPLAY=a.display,XAUTHORITY=str(auth));os.environ.update(DISPLAY=a.display,XAUTHORITY=str(auth))
 xv=subprocess.Popen(['Xvfb',a.display,'-screen','0','1024x768x24','-nolisten','tcp','-ac'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);ob=lo=None;rep={}
 try:
  wait_display(env,a.display);ob=subprocess.Popen(['openbox'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.1)
  lo=subprocess.Popen(['libreoffice',f'-env:UserInstallation={(out/"profile").resolve().as_uri()}','--nologo','--nodefault','--nofirststartwizard','--norestore',f'--accept=pipe,name={a.pipe};urp;StarOffice.ServiceManager',str(A),str(B)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  ta=A.resolve().as_uri();tb=B.resolve().as_uri();rows=wait_docs(env,HERE/'uno_helper.py',a.pipe);ar=row(rows,ta);br=row(rows,tb);orow=br if a.condition=='wrong_doc' else ar;obs=Observation(orow['url'],orow['uid'],orow['text'],time.monotonic_ns())
  if a.condition=='stale_uid':uno(env,HERE/'uno_helper.py',a.pipe,'close_reopen',url=ta,uid=ar['uid']);time.sleep(.08)
  if a.condition=='text_changed':uno(env,HERE/'uno_helper.py',a.pipe,'set_text',url=ta,text='boox')
  if a.condition=='stale_age':time.sleep(.65)
  cur=row(wait_docs(env,HERE/'uno_helper.py',a.pipe),ta);dec=precheck_bound(obs,desired=DESIRED,target_url=ta,current_row=cur,now_ns=time.monotonic_ns(),max_age_ns=MAX_AGE_NS);accepted,error,suffix=dec.accepted,dec.error,dec.suffix;emissions=0;bound_xid=0;d=display.Display(a.display)
  if accepted:bound_xid=bind(env,HERE/'uno_helper.py',a.pipe,ta,obs.uid,a.display)
  if accepted and a.condition=='focus_drift':uno(env,HERE/'uno_helper.py',a.pipe,'activate',url=tb,uid=br['uid']);time.sleep(.05)
  if accepted:
   aa,ff=active_focus(d);e=final_focus_guard(bound_xid,aa,ff);rr=row(uno(env,HERE/'uno_helper.py',a.pipe,'list'),ta)
   if e is None and (rr['uid']!=obs.uid or rr['text']!=obs.text):e='FINAL_DOCUMENT_CHANGED'
   if e is None and time.monotonic_ns()-obs.observed_ns>MAX_AGE_NS:e='STALE_OBSERVATION_FINAL'
   if e:accepted=False;error=e
  if accepted:chord(d,['Control_L','End']);emissions+=4;type_text(d,suffix);emissions+=2*len(suffix);time.sleep(.15)
  inmem=uno(env,HERE/'uno_helper.py',a.pipe,'list');fa=row(inmem,ta);fb=row(inmem,tb);uno(env,HERE/'uno_helper.py',a.pipe,'store',url=ta,uid=fa['uid']);uno(env,HERE/'uno_helper.py',a.pipe,'store',url=tb,uid=fb['uid']);time.sleep(.15);keys,mask=phys(d);d.close()
  rep={'condition':a.condition,'accepted':accepted,'error':error,'suffix':suffix,'emissions':emissions,'in_memory_a':fa,'in_memory_b':fb,'release':{'keys':keys,'mask':mask,'empty':not keys and mask==0},'store_fixture':True}
 finally:
  for p in (lo,ob,xv):
   if p and p.poll() is None:p.terminate()
  for p in (lo,ob,xv):
   if p:
    try:p.wait(timeout=3)
    except Exception:p.kill()
 expect_a=DESIRED if a.condition=='fresh' else ('boox' if a.condition=='text_changed' else A0);score=out/'score.json';subprocess.run([sys.executable,str(HERE/'score_odt.py'),'--a',str(A),'--b',str(B),'--expect-a',expect_a,'--expect-b',B0,'--out',str(score)],check=False,text=True,capture_output=True);s=json.loads(score.read_text()) if score.exists() else {'passed':False}
 refusal_ok=(a.condition=='fresh' and accepted and emissions>0) or (a.condition!='fresh' and not accepted and emissions==0);rep.update(expected_a=expect_a,expected_b=B0,durable_score=s,gate_pass=bool(refusal_ok and rep.get('release',{}).get('empty') and s.get('passed')));(out/'report.json').write_text(json.dumps(rep,indent=2,ensure_ascii=False)+'\n');print(json.dumps(rep,ensure_ascii=False));return 0 if rep['gate_pass'] else 1
if __name__=='__main__':raise SystemExit(main())
