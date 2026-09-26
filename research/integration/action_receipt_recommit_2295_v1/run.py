from __future__ import annotations
import argparse, hashlib, json, os, select, shutil, subprocess, sys, tempfile, time
from pathlib import Path

POLICIES=['REUSED_ID','FRESH_EPOCH','COMPOUND']
SCENARIOS=['STABLE_CURRENT','RECOMMIT_SAME_CLAIM','DOUBLE_RECOMMIT','TARGET_REPLACED','AUTHORITY_CHANGED','APP_RESTARTED','DUPLICATE_DELIVERY','TRUNCATED_RECEIPT','FRESH_AFTER_RECOMMIT']

def jdump(x): return json.dumps(x,sort_keys=True,separators=(',',':'))
def sha_text(x): return hashlib.sha256(x.encode()).hexdigest()
def evid(s): return hashlib.sha256(jdump({k:s[k] for k in ('session','surface_id','target_id')}).encode()).hexdigest()

def read_line(proc, timeout=3):
    r,_,_=select.select([proc.stdout],[],[],timeout)
    if not r: raise TimeoutError('child line timeout')
    line=proc.stdout.readline()
    if not line: raise RuntimeError('child EOF')
    return json.loads(line)

def send(proc,obj): proc.stdin.write(jdump(obj)+'\n'); proc.stdin.flush(); return read_line(proc)

def start_xvfb(display_num, root):
    auth=root/'Xauthority'; cookie=subprocess.check_output(['mcookie'],text=True).strip()
    subprocess.run(['xauth','-f',str(auth),'add',f':{display_num}','.',cookie],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    p=subprocess.Popen(['Xvfb',f':{display_num}','-screen','0','800x600x24','-nolisten','tcp','-auth',str(auth)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    sock=Path(f'/tmp/.X11-unix/X{display_num}')
    for _ in range(200):
        if sock.exists() and p.poll() is None: break
        time.sleep(.01)
    else: raise RuntimeError('Xvfb not ready')
    env=os.environ.copy(); env['DISPLAY']=f':{display_num}'; env['XAUTHORITY']=str(auth)
    return p,env

def start_app(src, env, journal, session):
    p=subprocess.Popen([sys.executable,'-S','-B',str(src/'app.py'),'--journal',str(journal),'--session',session],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
    ready=read_line(p,4)
    if ready.get('event')!='ready': raise RuntimeError('bad app ready')
    return p,ready

def stop_app(p):
    exitcode=None; err=''
    if p and p.poll() is None:
        try: send(p,{'op':'close'})
        except Exception: pass
        try: exitcode=p.wait(timeout=3)
        except subprocess.TimeoutExpired: p.kill(); exitcode=p.wait(timeout=2)
    elif p: exitcode=p.returncode
    if p:
        try: err=p.stderr.read()
        except Exception: pass
    return exitcode,err

def call_receipt(src, mode, policy, payload, dedup=None):
    cmd=[sys.executable,'-S','-B',str(src/'receipt.py'),mode,'--policy',policy]
    if dedup: cmd += ['--dedup',str(dedup)]
    cp=subprocess.run(cmd,input=jdump(payload) if not isinstance(payload,str) else payload,text=True,capture_output=True,timeout=3)
    if cp.returncode!=0: raise RuntimeError(f'receipt child fail {cp.returncode}: {cp.stderr}')
    return cp,json.loads(cp.stdout)

def do_click(src,env,x,y):
    cp=subprocess.run([sys.executable,'-B',str(src/'click.py'),str(x),str(y)],text=True,capture_output=True,env=env,timeout=3)
    if cp.returncode!=0: raise RuntimeError('click fail '+cp.stderr)
    return cp,json.loads(cp.stdout)

def case(src,out,policy,scenario,rep,idx):
    cdir=out/f'case-{idx:03d}-{policy}-{scenario}-r{rep}'; cdir.mkdir(parents=True)
    xvfb=None; app=None; app_initial_exit=None; app_initial_stderr=''; current_app_exit=None; current_app_stderr=''
    display_num=180+(idx%60)
    journal=cdir/'effects.jsonl'; dedup=cdir/'dedup.sqlite'
    row={'case_id':cdir.name,'policy':policy,'scenario':scenario,'rep':rep,'display':display_num,'decisions':[]}
    try:
        xvfb,env=start_xvfb(display_num,cdir)
        session=f'session-{idx}-a'
        app,ready=start_app(src,env,journal,session)
        initial=ready.copy()
        state={'session':ready['session'],'surface_id':ready['surface_id'],'target_id':ready['target_id'],'x':ready['x'],'y':ready['y'],
               'claim':'READY','commit_id':'commit-stable','commit_epoch':1,'authority_generation':1,'operation_id':f'op-{idx}'}
        state['evidence_digest']=evid(state)
        cp_p,receipt=call_receipt(src,'prepare',policy,state)
        receipt_raw=jdump(receipt)
        prepared_state=state.copy()
        old_app=app
        if scenario=='RECOMMIT_SAME_CLAIM': state['commit_epoch']=2
        elif scenario=='DOUBLE_RECOMMIT': state['commit_epoch']=3
        elif scenario=='TARGET_REPLACED':
            repl=send(app,{'op':'replace_target'}); state.update(target_id=repl['target_id'],x=repl['x'],y=repl['y']); state['evidence_digest']=evid(state); row['replacement']=repl
        elif scenario=='AUTHORITY_CHANGED': state['authority_generation']=2
        elif scenario=='APP_RESTARTED':
            app_initial_exit,app_initial_stderr=stop_app(app); app=None
            app,ready2=start_app(src,env,journal,f'session-{idx}-b')
            state.update(session=ready2['session'],surface_id=ready2['surface_id'],target_id=ready2['target_id'],x=ready2['x'],y=ready2['y']); state['evidence_digest']=evid(state); row['restart_ready']=ready2
        elif scenario=='FRESH_AFTER_RECOMMIT':
            state['commit_epoch']=2
            cp_p2,receipt=call_receipt(src,'prepare',policy,state); receipt_raw=jdump(receipt); row['fresh_reprepare']=True
        if scenario=='TRUNCATED_RECEIPT': receipt_raw=receipt_raw[:-7]
        attempts=2 if scenario=='DUPLICATE_DELIVERY' else 1
        for attempt in range(attempts):
            envp={'receipt_raw':receipt_raw,'current_state':state}
            cp_v,decision=call_receipt(src,'validate',policy,envp,dedup)
            entry={'attempt':attempt+1,'validator':decision,'validator_exit':cp_v.returncode,'validator_stderr':cp_v.stderr}
            if decision.get('admitted'):
                cp_c,click=do_click(src,env,decision['x'],decision['y']); entry['click']=click; entry['click_exit']=cp_c.returncode; entry['click_stderr']=cp_c.stderr
                time.sleep(.04); entry['post_click_state']=send(app,{'op':'state'})
            row['decisions'].append(entry)
        final_state=send(app,{'op':'state'})
        row.update(initial_app=initial,prepared_state=prepared_state,current_state=state,receipt_raw=receipt_raw,receipt_sha256=sha_text(receipt_raw),final_app=final_state)
        row['effects_raw']=journal.read_text() if journal.exists() else ''
        row['effect_rows']=[json.loads(x) for x in row['effects_raw'].splitlines() if x.strip()]
        row['app_initial_exit']=app_initial_exit; row['app_initial_stderr']=app_initial_stderr
        current_app_exit,current_app_stderr=stop_app(app); app=None
        row['app_exit']=current_app_exit; row['app_stderr']=current_app_stderr
    finally:
        if app is not None:
            current_app_exit,current_app_stderr=stop_app(app)
            row.setdefault('app_exit',current_app_exit); row.setdefault('app_stderr',current_app_stderr)
        if xvfb is not None:
            xvfb.terminate()
            try: xexit=xvfb.wait(timeout=2)
            except subprocess.TimeoutExpired: xvfb.kill(); xexit=xvfb.wait(timeout=2)
            row['xvfb_exit']=xexit; row['xvfb_stderr']=xvfb.stderr.read()
    return row

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--reps',type=int,default=2); ap.add_argument('--construction',action='store_true'); a=ap.parse_args()
    src=Path(__file__).resolve().parent; a.out.mkdir(parents=True,exist_ok=False)
    if a.construction:
        schedule=[('REUSED_ID','RECOMMIT_SAME_CLAIM',0),('FRESH_EPOCH','RECOMMIT_SAME_CLAIM',0),('COMPOUND','RECOMMIT_SAME_CLAIM',0),('FRESH_EPOCH','TARGET_REPLACED',0),('FRESH_EPOCH','AUTHORITY_CHANGED',0),('FRESH_EPOCH','APP_RESTARTED',0),('COMPOUND','DUPLICATE_DELIVERY',0),('COMPOUND','TARGET_REPLACED',0),('COMPOUND','APP_RESTARTED',0),('COMPOUND','STABLE_CURRENT',0),('COMPOUND','TRUNCATED_RECEIPT',0),('COMPOUND','FRESH_AFTER_RECOMMIT',0)]
    else:
        schedule=[(p,s,r) for r in range(a.reps) for s in SCENARIOS for p in POLICIES]
    rows=[]
    for idx,(p,s,r) in enumerate(schedule):
        rows.append(case(src,a.out,p,s,r,idx))
        (a.out/'RAW.partial.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    (a.out/'RAW.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    (a.out/'END.json').write_text(json.dumps({'cases':len(rows),'formal':not a.construction,'runner_exit':0},sort_keys=True)+'\n')
    print(json.dumps({'cases':len(rows),'status':'COMPLETE','formal':not a.construction},sort_keys=True))
if __name__=='__main__': main()
