import argparse, hashlib, json, os, pathlib, shutil, subprocess, sys, time
from Xlib import display, XK, X
from Xlib.ext import xtest
SCHEDULES=['PRESS_EFFECT','RELEASE_EFFECT','STATE_ONLY','BACKGROUND_EFFECT']

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def key_down(d,kc):
    m=d.query_keymap(); b=bytes(m); return bool(b[kc//8] & (1<<(kc%8)))
def run_case(root,schedule,rep,display_no):
    cid=f'{schedule.lower()}-r{rep}'; cdir=root/cid; cdir.mkdir()
    journal=cdir/'app.jsonl'; manifest=cdir/'session.json'; score=cdir/'score.json'; ctl=cdir/'controller.json'
    plan=f'plan-{cid}'; act=f'act-{cid}'; json.dump({'case_id':cid,'schedule':schedule,'rep':rep,'plan_id':plan,'actuation_id':act},open(manifest,'w'),sort_keys=True,indent=2)
    env=os.environ.copy(); env['DISPLAY']=f':{display_no}'; env['XAUTHORITY']='/dev/null'
    xv=subprocess.Popen(['Xvfb',env['DISPLAY'],'-screen','0','320x200x24','-nolisten','tcp','-ac'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
    sock=pathlib.Path(f'/tmp/.X11-unix/X{display_no}')
    for _ in range(100):
        if sock.exists(): break
        if xv.poll() is not None: raise RuntimeError('xvfb exited')
        time.sleep(.02)
    app=subprocess.Popen([sys.executable,str(pathlib.Path(__file__).with_name('fixture.py')),'--schedule',schedule,'--journal',str(journal),'--plan-id',plan,'--actuation-id',act],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
    ready_line=app.stdout.readline().strip(); ready=json.loads(ready_line)
    old_xauth=os.environ.get('XAUTHORITY'); os.environ['XAUTHORITY']='/dev/null'
    try:
        d=display.Display(env['DISPLAY'])
    finally:
        if old_xauth is None: os.environ.pop('XAUTHORITY',None)
        else: os.environ['XAUTHORITY']=old_xauth
    kc=d.keysym_to_keycode(XK.string_to_keysym('a'))
    time.sleep(.06)
    down_emit=time.monotonic_ns(); xtest.fake_input(d,X.KeyPress,kc); d.sync(); down_ack=time.monotonic_ns(); down_seen=key_down(d,kc)
    time.sleep(.05)
    up_emit=time.monotonic_ns(); xtest.fake_input(d,X.KeyRelease,kc); d.sync(); up_ack=time.monotonic_ns(); up_seen=key_down(d,kc)
    app_rc=app.wait(timeout=3); app_err=app.stderr.read(); time.sleep(.02); final_down=key_down(d,kc); d.close()
    subprocess.run([sys.executable,str(pathlib.Path(__file__).with_name('scorer.py')),'--manifest',str(manifest),'--journal',str(journal),'--out',str(score)],check=True)
    xv.terminate(); xv_out,xv_err=xv.communicate(timeout=3)
    row={'case_id':cid,'schedule':schedule,'rep':rep,'plan_id':plan,'actuation_id':act,'display':display_no,'ready':ready,'down_emit_ns':down_emit,'down_ack_ns':down_ack,'up_emit_ns':up_emit,'up_ack_ns':up_ack,'down_seen':down_seen,'up_seen_after_release':up_seen,'final_down':final_down,'app_exit':app_rc,'app_stderr':app_err,'xvfb_exit':xv.returncode,'xvfb_stderr':xv_err,'score':json.load(open(score))}
    json.dump(row,open(ctl,'w'),sort_keys=True,indent=2)
    return row

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--reps',type=int,default=3); ap.add_argument('--display-base',type=int,default=310); a=ap.parse_args(); out=pathlib.Path(a.out)
    if out.exists(): raise SystemExit('output exists')
    out.mkdir(parents=True); rows=[]
    for rep in range(a.reps):
      for i,s in enumerate(SCHEDULES): rows.append(run_case(out,s,rep,a.display_base+rep*10+i))
    json.dump(rows,open(out/'RAW.json','w'),sort_keys=True,indent=2)
    files={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='MANIFEST.json'}
    json.dump({'files':files,'count':len(files)},open(out/'MANIFEST.json','w'),sort_keys=True,indent=2)
    print(json.dumps({'cases':len(rows),'out':str(out)}))
if __name__=='__main__': main()
