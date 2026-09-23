#!/usr/bin/env python3
import argparse, json, os, pathlib, socket, subprocess, sys, time, hashlib
from Xlib import X, XK, display
from Xlib.ext import xtest

POLICIES=['POP_ONLY','EVIDENCE_BOUND_RESUME']
SCENARIOS=['NORMAL','TARGET_REPLACED','QUEUE_CHANGED','SOURCE_STALE','PENDING_UNKNOWN','TASK_CANCELED']

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def ipc(path,cmd):
    s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM); s.connect(path); s.sendall((json.dumps({'cmd':cmd})+'\n').encode());
    buf=b''
    while b'\n' not in buf: buf+=s.recv(65536)
    s.close(); return json.loads(buf.split(b'\n',1)[0])
def wait_socket(p,timeout=3):
    end=time.time()+timeout
    while time.time()<end:
        if os.path.exists(p): return
        time.sleep(.01)
    raise RuntimeError('socket timeout')
def key_state(d,keycode):
    m=d.query_keymap(); return bool(m[keycode//8] & (1<<(keycode%8)))
def type_char(d,ch):
    kc=d.keysym_to_keycode(XK.string_to_keysym(ch))
    xtest.fake_input(d,X.KeyPress,kc); d.sync(); time.sleep(.02)
    xtest.fake_input(d,X.KeyRelease,kc); d.sync(); time.sleep(.02)
    return kc
def decide(policy,saved,current):
    if not current['task_active']: return 'CANCELED'
    if not current['interrupt_resolved']: return 'WAIT_INTERRUPT'
    if policy=='POP_ONLY': return 'RESUME'
    if current['pending_result']=='UNKNOWN': return 'RECONCILE_RESULT'
    if (not current['source_fresh']) or current['source_epoch']!=saved['source_epoch']: return 'YIELD_STALE'
    if current['queue_version']!=saved['queue_version']: return 'REPLAN_QUEUE'
    if current['target_id']!=saved['target_id']: return 'REVALIDATE_TARGET'
    return 'RESUME'
def wait_value(sock,key,val,timeout=2):
    end=time.time()+timeout
    last=None
    while time.time()<end:
        last=ipc(sock,'snapshot')['snapshot']
        if last[key]==val:return last
        time.sleep(.02)
    raise RuntimeError(f'value timeout {key} {last}')
def start_x(display_num,auth):
    cookie=subprocess.check_output(['mcookie'],text=True).strip()
    pathlib.Path(auth).touch()
    subprocess.run(['xauth','-f',auth,'add',f':{display_num}','.',cookie],check=True,stdout=subprocess.DEVNULL)
    p=subprocess.Popen(['Xvfb',f':{display_num}','-screen','0','640x360x24','-nolisten','tcp','-auth',auth],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    sock=f'/tmp/.X11-unix/X{display_num}'; end=time.time()+3
    while time.time()<end:
        if os.path.exists(sock): return p
        time.sleep(.02)
    raise RuntimeError('xvfb timeout')
def run_case(root,policy,scenario,rep,display_num):
    cid=f'r{rep}-{policy}-{scenario}'; cdir=pathlib.Path(root)/cid; cdir.mkdir(parents=True,exist_ok=False)
    auth=str(cdir/'Xauthority'); xvfb=start_x(display_num,auth); env=os.environ.copy(); env['DISPLAY']=f':{display_num}'; env['XAUTHORITY']=auth
    sock=str(cdir/'app.sock'); app=subprocess.Popen([sys.executable,'-B','app.py',sock],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    ready=json.loads(app.stdout.readline()); wait_socket(sock)
    old_xauth=os.environ.get('XAUTHORITY'); old_disp=os.environ.get('DISPLAY')
    os.environ['XAUTHORITY']=auth; os.environ['DISPLAY']=f':{display_num}'
    try:
        d=display.Display(f':{display_num}')
    finally:
        if old_xauth is None: os.environ.pop('XAUTHORITY',None)
        else: os.environ['XAUTHORITY']=old_xauth
        if old_disp is None: os.environ.pop('DISPLAY',None)
        else: os.environ['DISPLAY']=old_disp
    try:
        kc_a=type_char(d,'a'); pre=wait_value(sock,'a','a')
        shown=ipc(sock,'show_interrupt')['snapshot']; saved=dict(shown)
        if scenario=='TARGET_REPLACED': ipc(sock,'replace_target')
        elif scenario=='QUEUE_CHANGED': ipc(sock,'queue_changed')
        elif scenario=='SOURCE_STALE': ipc(sock,'source_stale')
        elif scenario=='PENDING_UNKNOWN': ipc(sock,'pending_unknown')
        elif scenario=='TASK_CANCELED': ipc(sock,'task_cancel')
        closed=ipc(sock,'close_interrupt')['snapshot']
        current=ipc(sock,'snapshot')['snapshot']
        decision=decide(policy,saved,current); suffix_sent=False; kc_b=None
        if decision=='RESUME':
            suffix_sent=True; kc_b=type_char(d,'b'); time.sleep(.05)
        final=ipc(sock,'snapshot')['snapshot']
        neutral_a=not key_state(d,kc_a); neutral_b=True if kc_b is None else (not key_state(d,kc_b))
        task_success=(final['a']=='ab' and final['b']=='' and final['target_id']==saved['target_id'])
        unsafe_resume=(decision=='RESUME' and scenario not in ('NORMAL',))
        ipc(sock,'close')
        app_out=app.stdout.read(); app_err=app.stderr.read(); app_rc=app.wait(timeout=3)
        d.close(); xvfb.terminate(); xvfb_rc=xvfb.wait(timeout=3); xvfb_err=xvfb.stderr.read()
        row={'case_id':cid,'policy':policy,'scenario':scenario,'rep':rep,'display':display_num,
          'ready':ready['snapshot'],'pre':pre,'saved':saved,'after_close':closed,'current':current,'decision':decision,
          'suffix_sent':suffix_sent,'final':final,'task_success':task_success,'unsafe_resume':unsafe_resume,
          'neutral_a':neutral_a,'neutral_b':neutral_b,'app_exit':app_rc,'xvfb_exit':xvfb_rc,
          'app_stdout_tail':app_out,'app_stderr':app_err,'xvfb_stderr':xvfb_err,
          'source_hashes':{n:sha(n) for n in ['app.py','run.py','audit.py','controls.py']}}
        (cdir/'row.json').write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
        return row
    except Exception:
        try:d.close()
        except:pass
        try:app.kill(); app.wait(timeout=2)
        except:pass
        try:xvfb.terminate(); xvfb.wait(timeout=2)
        except:pass
        raise

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--rep',type=int,required=True); ap.add_argument('--display-base',type=int,required=True); a=ap.parse_args()
    root=pathlib.Path(a.out); root.mkdir(parents=True,exist_ok=False); rows=[]; i=0
    for scenario in SCENARIOS:
      for policy in POLICIES:
        rows.append(run_case(root,policy,scenario,a.rep,a.display_base+i)); i+=1
    (root/'ROWS.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'rows':len(rows),'rep':a.rep,'out':str(root)},sort_keys=True))
if __name__=='__main__': main()
