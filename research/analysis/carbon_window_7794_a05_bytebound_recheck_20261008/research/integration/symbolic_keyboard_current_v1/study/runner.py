import argparse,hashlib,json,os,secrets,signal,subprocess,sys,tempfile,time
from pathlib import Path
from Xlib import X,XK,display
from Xlib.ext import xtest
POLICIES=['RAW_KEYSYM','SNAPSHOT_SYMBOLIC','CURRENT_SYMBOLIC']
CONDS=['US_UNDO','DE_UNDO','MODAL_CONFIRM','NO_MODAL_CONFIRM','STALE_CONTEXT_MODAL_TO_EDITOR','LAYOUT_CHANGED_US_TO_DE_UNDO']
def sh(cmd,env=None,timeout=5):
    p=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=timeout)
    if p.returncode: raise RuntimeError({'cmd':cmd,'rc':p.returncode,'out':p.stdout,'err':p.stderr})
    return p.stdout
def xkb_hash(env):
    data=subprocess.run(['xkbcomp','-xkb',env['DISPLAY'],'-'],env=env,capture_output=True,timeout=5,check=True).stdout
    return hashlib.sha256(data).hexdigest()
def read_state(path,expect_mode=None,timeout=3):
    end=time.time()+timeout
    while time.time()<end:
        try:
            s=json.loads(path.read_text())
            if s.get('ready') and (expect_mode is None or s.get('mode')==expect_mode): return s
        except Exception: pass
        time.sleep(.01)
    raise TimeoutError('state not ready')
def neutral(d):
    km=list(d.query_keymap());ptr=d.screen().root.query_pointer().mask
    return {'keymap':km,'pointer_mask':int(ptr),'neutral':not any(km) and not (ptr & 0x1f00),'ns':time.monotonic_ns()}
def emit(d,keys):
    aliases={'CTRL':'Control_L','Return':'Return'};events=[]
    resolved=[]
    for k in keys:
        sym=XK.string_to_keysym(aliases.get(k,k));code=d.keysym_to_keycode(sym)
        if not code: raise RuntimeError('unmapped '+k)
        resolved.append((k,code))
    for k,code in resolved:
        xtest.fake_input(d,X.KeyPress,code);events.append({'key':k,'keycode':int(code),'down':True})
    for k,code in reversed(resolved):
        xtest.fake_input(d,X.KeyRelease,code);events.append({'key':k,'keycode':int(code),'down':False})
    d.sync();return events
def main():
    p=argparse.ArgumentParser();p.add_argument('--index',type=int,required=True);p.add_argument('--out',required=True);p.add_argument('--construction',action='store_true');a=p.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    if a.construction:
        cs=[('CURRENT_SYMBOLIC','DE_UNDO',0),('CURRENT_SYMBOLIC','NO_MODAL_CONFIRM',0),('SNAPSHOT_SYMBOLIC','LAYOUT_CHANGED_US_TO_DE_UNDO',0)]
        policy,cond,rep=cs[a.index]
    else:
        schedule=[(p,c,r) for r in range(2) for c in CONDS for p in POLICIES];policy,cond,rep=schedule[a.index]
    spec={'index':a.index,'policy':policy,'condition':cond,'rep':rep}
    (out/'SPEC.json').write_text(json.dumps(spec,indent=2,sort_keys=True))
    dispnum=240+(os.getpid()%300);display_name=f':{dispnum}';sock=Path(f'/tmp/.X11-unix/X{dispnum}')
    if sock.exists(): raise RuntimeError('display collision')
    auth=out/'Xauthority';cookie=secrets.token_hex(16);sh(['xauth','-f',str(auth),'add',display_name,'.',cookie])
    xv=open(out/'xvfb.log','wb');xp=subprocess.Popen(['Xvfb',display_name,'-screen','0','640x360x24','-nolisten','tcp','-auth',str(auth),'-noreset'],stdout=xv,stderr=subprocess.STDOUT,start_new_session=True)
    env=dict(os.environ,DISPLAY=display_name,XAUTHORITY=str(auth))
    app=None;d=None;row={'spec':spec,'error':None}
    try:
        end=time.time()+3
        while time.time()<end and not sock.exists():
            if xp.poll() is not None: raise RuntimeError('xvfb early exit')
            time.sleep(.01)
        initial_layout='de' if cond=='DE_UNDO' else 'us';sh(['setxkbmap','-layout',initial_layout],env)
        initial_mode='MODAL' if cond in ('MODAL_CONFIRM','STALE_CONTEXT_MODAL_TO_EDITOR') else 'EDITOR'
        state_path=out/'app_state.json';app_out=open(out/'app.stdout','w');app_err=open(out/'app.stderr','w')
        app=subprocess.Popen([sys.executable,str(Path(__file__).with_name('app.py')),'--state',str(state_path),'--mode',initial_mode],env=env,stdout=app_out,stderr=app_err,text=True,start_new_session=True)
        st=read_state(state_path,initial_mode);window_id=st['window_id']
        os.environ['DISPLAY']=display_name;os.environ['XAUTHORITY']=str(auth)
        d=display.Display(display_name);win=d.create_resource_object('window',window_id);win.set_input_focus(X.RevertToParent,X.CurrentTime);d.sync()
        intent='CONFIRM' if 'CONFIRM' in cond or 'CONTEXT' in cond else 'UNDO'
        plan={'layout_hash':xkb_hash(env),'mode':initial_mode,'layout':initial_layout,'ns':time.monotonic_ns()}
        row['plan']=plan;row['initial_state']=st;row['initial_native']=neutral(d)
        if cond=='STALE_CONTEXT_MODAL_TO_EDITOR':
            os.kill(app.pid,signal.SIGUSR1);read_state(state_path,'EDITOR')
        if cond=='LAYOUT_CHANGED_US_TO_DE_UNDO': sh(['setxkbmap','-layout','de'],env)
        current_state=read_state(state_path)
        current={'layout_hash':xkb_hash(env),'mode':current_state['mode'],'layout':'de' if cond in ('DE_UNDO','LAYOUT_CHANGED_US_TO_DE_UNDO') else initial_layout,'ns':time.monotonic_ns()}
        row['current']=current
        pin={'policy':policy,'intent':intent,'plan':plan,'current':current}
        pp=subprocess.run([sys.executable,str(Path(__file__).with_name('policy.py'))],input=json.dumps(pin),text=True,capture_output=True,timeout=3)
        decision=json.loads(pp.stdout);row['policy_input']=pin;row['policy_output']=decision;row['policy_exit']=pp.returncode;row['policy_stderr']=pp.stderr
        events=[]
        emit_d=d
        if decision['decision']=='EMIT' and policy=='CURRENT_SYMBOLIC':
            emit_d=display.Display(display_name)
        if decision['decision']=='EMIT': events=emit(emit_d,decision['keys'])
        if emit_d is not d:
            emit_d.close()
        time.sleep(.04);final=read_state(state_path)
        row['native_events']=events;row['final_state']=final;row['terminal_native']=neutral(d)
        expected_effect='UNDO' if intent=='UNDO' else 'CONFIRM'
        row['semantic_effect']={'expected':expected_effect,'undo_delta':final['undo']-st['undo'],'redo_delta':final['redo']-st['redo'],'confirm_delta':final['confirm']-st['confirm'],'stray_delta':final['stray_return']-st['stray_return']}
    except Exception as e:
        row['error']=repr(e)
    finally:
        if d:
            try:d.close()
            except Exception:pass
        if app and app.poll() is None:
            os.killpg(app.pid,signal.SIGTERM)
            try:app.wait(timeout=3)
            except subprocess.TimeoutExpired: os.killpg(app.pid,signal.SIGKILL);app.wait()
        row['app_exit']=None if app is None else app.returncode
        if xp.poll() is None:
            os.killpg(xp.pid,signal.SIGTERM)
            try:xp.wait(timeout=3)
            except subprocess.TimeoutExpired: os.killpg(xp.pid,signal.SIGKILL);xp.wait()
        row['xvfb_exit']=xp.returncode;xv.close();row['socket_absent']=not sock.exists();row['auth_sha256']=hashlib.sha256(auth.read_bytes()).hexdigest() if auth.exists() else None
    (out/'ROW.json').write_text(json.dumps(row,indent=2,sort_keys=True))
    print(json.dumps({'index':a.index,'error':row['error'],'policy':policy,'condition':cond,'decision':row.get('policy_output',{}).get('decision'),'effect':row.get('semantic_effect')}))
    if row['error'] is not None: raise SystemExit(1)
if __name__=='__main__':main()
