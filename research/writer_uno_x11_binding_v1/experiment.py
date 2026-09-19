from __future__ import annotations
import argparse,json,os,subprocess,time,shutil
from pathlib import Path
from odf.opendocument import OpenDocumentText
from odf.text import P
from Xlib import X,XK,display
from Xlib.ext import xtest
from binding import uno,writer_windows,bind_document
HERE=Path(__file__).resolve().parent
DESIRED='bookkeeperoffice'; PREFIX='book'; OTHER='sidecar'; SUFFIX=DESIRED[len(PREFIX):]

def wait_display(env,name):
    for _ in range(100):
        if subprocess.run(['xdpyinfo','-display',name],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:return
        time.sleep(.03)
    raise RuntimeError('display unavailable')
def wait_windows(name,n=2):
    d=display.Display(name);deadline=time.monotonic()+6
    while time.monotonic()<deadline:
        rows=writer_windows(d)
        if len(rows)>=n:d.close();return rows
        time.sleep(.05)
    d.close();raise RuntimeError('writer windows missing')
def keycode(d,name):
    sym=XK.string_to_keysym(name);code=d.keysym_to_keycode(sym)
    if not code:raise RuntimeError(name)
    return code
def send_key(d,code,down):xtest.fake_input(d,X.KeyPress if down else X.KeyRelease,code);d.sync()
def chord(d,names):
    codes=[keycode(d,n) for n in names]
    for c in codes:send_key(d,c,True)
    for c in reversed(codes):send_key(d,c,False)
def type_text(d,text):
    for ch in text:
        c=keycode(d,ch);send_key(d,c,True);send_key(d,c,False);time.sleep(.012)
def physical_empty(d):
    bits=d.query_keymap();keys=[k for k in range(8,256) if bits[k//8]&(1<<(k%8))];mask=int(d.screen().root.query_pointer().mask)
    return keys==[] and mask==0,keys,mask
def focus_xid(d,wid):
    w=d.create_resource_object('window',wid);w.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();time.sleep(.04)

def make_doc(path,text):
    doc=OpenDocumentText();doc.text.addElement(P(text=text));doc.save(str(path))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--display',required=True);ap.add_argument('--policy',choices=['positional','activated'],required=True);ap.add_argument('--pipe',required=True);a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    A=out/'a-target.odt';B=out/'b-sidecar.odt';make_doc(A,PREFIX);make_doc(B,OTHER);auth=out/'Xauthority';auth.write_bytes(b'');env=os.environ.copy();env.update(DISPLAY=a.display,XAUTHORITY=str(auth));os.environ.update(DISPLAY=a.display,XAUTHORITY=str(auth))
    xv=subprocess.Popen(['Xvfb',a.display,'-screen','0','1024x768x24','-nolisten','tcp','-ac'],env=env,stdout=(out/'xvfb.out').open('w'),stderr=(out/'xvfb.err').open('w'));ob=lo=None
    try:
        wait_display(env,a.display);ob=subprocess.Popen(['openbox'],env=env,stdout=(out/'openbox.out').open('w'),stderr=(out/'openbox.err').open('w'))
        profile=(out/'profile').resolve().as_uri();lo=subprocess.Popen(['libreoffice',f'-env:UserInstallation={profile}','--nologo','--nodefault','--nofirststartwizard','--norestore',f'--accept=pipe,name={a.pipe};urp;StarOffice.ComponentContext',str(A),str(B)],env=env,stdout=(out/'lo.out').open('w'),stderr=(out/'lo.err').open('w'))
        wins=wait_windows(a.display,2);rows=uno(env,HERE/'uno_helper.py',a.pipe,'list');deadline=time.monotonic()+4
        while len(rows)<2 and time.monotonic()<deadline:time.sleep(.05);rows=uno(env,HERE/'uno_helper.py',a.pipe,'list')
        target_url=A.resolve().as_uri();target=[r for r in rows if r['url']==target_url]
        if len(target)!=1:raise RuntimeError(f'target UNO missing {rows}')
        target=target[0];binding=None
        if a.policy=='positional':
            idx=next(i for i,r in enumerate(rows) if r['url']==target_url)
            if idx>=len(wins):raise RuntimeError('positional no corresponding x11 window')
            xid=wins[idx]['xid'];binding={'policy':'positional','xid':xid,'uno_index':idx,'x11_index':idx,'uno_order':[Path(r['url']).name for r in rows],'x11_order':[w['title'] for w in wins]}
        else:
            b1=bind_document(env,HERE/'uno_helper.py',a.pipe,target_url,target['uid'],a.display)
            other=[r for r in rows if r['url']!=target_url][0];bo=bind_document(env,HERE/'uno_helper.py',a.pipe,other['url'],other['uid'],a.display)
            b2=bind_document(env,HERE/'uno_helper.py',a.pipe,target_url,target['uid'],a.display)
            if b1['xid']!=b2['xid'] or b1['xid']==bo['xid']:raise RuntimeError('non-bijective binding')
            xid=b2['xid'];binding={'policy':'activated','target_first':b1,'other':bo,'target_second':b2,'uno_order':[Path(r['url']).name for r in rows],'x11_order':[w['title'] for w in wins]}
        d=display.Display(a.display);focus_xid(d,xid);chord(d,['Control_L','End']);type_text(d,SUFFIX);time.sleep(.25);empty,keys,mask=physical_empty(d);d.close()
        after=uno(env,HERE/'uno_helper.py',a.pipe,'list');Arow=[r for r in after if r['url']==target_url][0];Brow=[r for r in after if r['url']==B.resolve().as_uri()][0]
        result={'policy':a.policy,'target':target,'binding':binding,'before_uno':rows,'before_x11':wins,'after':{'a':Arow,'b':Brow},'release':{'empty':empty,'keys':keys,'mask':mask}}
        result['exact_target']=Arow['text']==DESIRED and Brow['text']==OTHER
        result['wrong_target_effect']=Arow['text']!=DESIRED and Brow['text']!=OTHER
        result['gate_pass']=empty and (result['exact_target'] if a.policy=='activated' else result['wrong_target_effect'])
        (out/'report.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps(result,ensure_ascii=False));return 0 if result['gate_pass'] else 1
    finally:
        for p in (lo,ob,xv):
            if p and p.poll() is None:p.terminate()
        for p in (lo,ob,xv):
            if p:
                try:p.wait(timeout=2)
                except: p.kill()
if __name__=='__main__':raise SystemExit(main())
