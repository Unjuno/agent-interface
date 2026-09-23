from __future__ import annotations
import hashlib, json, os, subprocess, tempfile, time
from pathlib import Path
from Xlib import X, XK, display
from Xlib.ext import xtest

TASK='MULTI-APP-GUARDED-RECOVERY-A2-20260918-002'
REFUSAL_ORDER=['REFUSE_GEOMETRY','REFUSE_FOCUS','REFUSE_BINDING','REFUSE_OBSERVATION']
EFFECT_TITLES=['chrome://downloads/ - Chromium','chrome://history/ - Chromium','chrome://downloads/ - Chromium','chrome://history/ - Chromium']

def free_display(start=90,end=130):
    sock=Path('/tmp/.X11-unix')
    for n in range(start,end):
        if not (sock/f'X{n}').exists(): return n
    raise RuntimeError('no_free_display')

def launch(cmd,env,stderr):
    return subprocess.Popen(cmd,env=env,stdout=subprocess.DEVNULL,stderr=stderr)

def stop(p):
    if p and p.poll() is None:
        p.terminate()
        try:p.wait(timeout=3)
        except subprocess.TimeoutExpired:p.kill();p.wait(timeout=3)

def run_session(session_id:int):
    n=free_display(); disp=f':{n}'
    rootdir=Path(tempfile.mkdtemp(prefix=f'ai1728-{session_id}-'))
    auth=rootdir/'.Xauthority';auth.write_bytes(b'')
    env=os.environ.copy();env['DISPLAY']=disp;env['XAUTHORITY']=str(auth)
    os.environ['DISPLAY']=disp;os.environ['XAUTHORITY']=str(auth)
    f_xv=(rootdir/'xvfb.err').open('w');f_wm=(rootdir/'openbox.err').open('w')
    xv=launch(['Xvfb',disp,'-screen','0','1280x800x24','-ac'],env,f_xv);time.sleep(.25)
    wm=launch(['openbox'],env,f_wm);time.sleep(.4)
    d=display.Display(disp);root=d.screen().root
    atom_clients=d.intern_atom('_NET_CLIENT_LIST');atom_name=d.intern_atom('_NET_WM_NAME');utf8=d.intern_atom('UTF8_STRING')
    ps=[]; opened=[]; refusals=[]; batches=[]; effects=[]; task_input_batches=0
    def clients():
        p=root.get_full_property(atom_clients,X.AnyPropertyType);return list(p.value) if p else []
    def title(wid):
        w=d.create_resource_object('window',wid)
        try:
            p=w.get_full_property(atom_name,utf8)
            if p and p.value:return p.value.decode('utf-8','replace') if isinstance(p.value,bytes) else str(p.value)
        except Exception:pass
        try:return w.get_wm_name() or ''
        except Exception:return ''
    def wait_title(substr,timeout=15,exclude=None):
        end=time.time()+timeout
        while time.time()<end:
            for wid in clients():
                if exclude and wid in exclude:continue
                if substr.lower() in title(wid).lower():return wid
            time.sleep(.05)
        raise RuntimeError('window_not_found:'+substr)
    def wait_exact_title(wid,expected,timeout=8):
        end=time.time()+timeout
        while time.time()<end:
            t=title(wid)
            if t==expected:return t
            time.sleep(.03)
        raise RuntimeError(f'effect_title_missing:{expected}:{title(wid)}')
    def geom(wid):
        g=d.create_resource_object('window',wid).get_geometry();return [int(g.x),int(g.y),int(g.width),int(g.height)]
    def focus(wid):
        subprocess.run(['wmctrl','-ia',hex(int(wid))],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        d.create_resource_object('window',wid).set_input_focus(X.RevertToParent,X.CurrentTime);d.sync();time.sleep(.15)
    def focus_id():
        f=d.get_input_focus().focus;return int(f.id) if hasattr(f,'id') else int(f)
    def key(name,down):
        kc=d.keysym_to_keycode(XK.string_to_keysym(name));xtest.fake_input(d,X.KeyPress if down else X.KeyRelease,kc)
    def chord(mods,k):
        for m in mods:key(m,True)
        key(k,True);key(k,False)
        for m in reversed(mods):key(m,False)
        d.sync()
    def framebuffer_hash():
        g=root.get_geometry();im=root.get_image(0,0,g.width,g.height,X.ZPixmap,0xffffffff)
        raw=im.data.encode('latin1') if isinstance(im.data,str) else bytes(im.data)
        return hashlib.sha256(raw).hexdigest()
    def neutral():
        km=d.query_keymap();q=root.query_pointer();return (not any(km)) and int(q.mask)==0
    def refuse(reason,details):
        before=task_input_batches
        row={'reason':reason,'input_before':before,'input_after':task_input_batches,'at_ns':time.perf_counter_ns()}
        row.update(details);refusals.append(row)
    def task_shortcut(wid,mods,key,expected,phase):
        nonlocal task_input_batches
        active=focus_id();before=task_input_batches
        if active!=wid:raise RuntimeError(f'wrong_active_before_task:{active}!={wid}')
        chord(mods,key);task_input_batches+=1
        t=wait_exact_title(wid,expected)
        after_hash=framebuffer_hash()
        batches.append({'phase':phase,'window':int(wid),'active_before':int(active),'input_before':before,'input_after':task_input_batches,'shortcut':'+'.join(mods+[key]),'expected_title':expected})
        effects.append({'phase':phase,'window':int(wid),'title':t,'observed_ns':time.perf_counter_ns(),'framebuffer_sha256':after_hash})
    try:
        c1dir=rootdir/'c1';c1dir.mkdir();e1=(rootdir/'c1.err').open('w');opened.append(e1)
        c1=launch(['chromium','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--user-data-dir='+str(c1dir),'--no-first-run','about:blank'],env,e1);ps.append(c1)
        old=wait_title('Chromium',20);focus(old)
        binding={'window':int(old),'geometry':geom(old),'focus':focus_id(),'observation_hash':framebuffer_hash()}

        subprocess.run(['wmctrl','-ir',hex(old),'-b','remove,maximized_vert,maximized_horz'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        subprocess.run(['wmctrl','-ir',hex(old),'-e','0,80,60,900,650'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.4)
        cur_geom=geom(old)
        if cur_geom==binding['geometry']:raise RuntimeError('geometry_drift_missing')
        refuse('REFUSE_GEOMETRY',{'bound_geometry':binding['geometry'],'current_geometry':cur_geom})
        binding['geometry']=cur_geom;focus(old);binding['focus']=focus_id();binding['observation_hash']=framebuffer_hash()
        task_shortcut(old,['Control_L'],'j',EFFECT_TITLES[0],1)

        ex=(rootdir/'xterm.err').open('w');opened.append(ex);xt=launch(['xterm','-T',f'AI1728-PEER-{session_id}'],env,ex);ps.append(xt)
        peer=wait_title('AI1728-PEER',10);focus(peer);cur_focus=focus_id()
        if cur_focus==binding['window']:raise RuntimeError('focus_drift_missing')
        refuse('REFUSE_FOCUS',{'bound_window':binding['window'],'current_focus':cur_focus})
        focus(old);binding['focus']=focus_id();binding['observation_hash']=framebuffer_hash()
        task_shortcut(old,['Control_L'],'h',EFFECT_TITLES[1],2)

        c2dir=rootdir/'c2';c2dir.mkdir();e2=(rootdir/'c2.err').open('w');opened.append(e2)
        c2=launch(['chromium','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--user-data-dir='+str(c2dir),'--no-first-run','about:blank'],env,e2);ps.append(c2)
        new=wait_title('Chromium',20,exclude={old});focus(new);stop(c1)
        end=time.time()+6
        while old in clients() and time.time()<end:time.sleep(.05)
        if old in clients() or int(new)==binding['window']:raise RuntimeError('replacement_missing')
        refuse('REFUSE_BINDING',{'bound_window':binding['window'],'replacement_window':int(new),'old_gone':old not in clients()})
        binding={'window':int(new),'geometry':geom(new),'focus':focus_id(),'observation_hash':framebuffer_hash()}
        task_shortcut(new,['Control_L'],'j',EFFECT_TITLES[2],3)

        binding['observation_hash']=framebuffer_hash();focus(new);chord(['Control_L','Shift_L'],'Delete');time.sleep(.8)
        clear_title=wait_exact_title(new,'chrome://settings/clearBrowserData - Chromium')
        current_hash=framebuffer_hash()
        if current_hash==binding['observation_hash']:raise RuntimeError('observation_drift_missing')
        refuse('REFUSE_OBSERVATION',{'bound_observation_hash':binding['observation_hash'],'current_observation_hash':current_hash,'perturbation_title':clear_title})
        binding['observation_hash']=current_hash;focus(new);binding['focus']=focus_id()
        task_shortcut(new,['Control_L'],'h',EFFECT_TITLES[3],4)
        time.sleep(.2)
        return {'task':TASK,'session_id':session_id,'refusals':refusals,'task_batches':batches,'effects':effects,'task_input_batches':task_input_batches,'old_window':int(old),'new_window':int(new),'old_gone':old not in clients(),'terminal_neutral':neutral(),'apps':['Chromium','XTerm'],'display':disp}
    finally:
        for p in reversed(ps):stop(p)
        try:d.close()
        except Exception:pass
        stop(wm);stop(xv)
        for f in opened+[f_xv,f_wm]:
            try:f.close()
            except Exception:pass

def evaluate(row):
    errors=[]
    if [r.get('reason') for r in row.get('refusals',[])]!=REFUSAL_ORDER:errors.append('refusal_order')
    if any(r.get('input_before')!=r.get('input_after') for r in row.get('refusals',[])):errors.append('stale_task_input')
    if row.get('task_input_batches')!=4 or len(row.get('task_batches',[]))!=4:errors.append('batch_count')
    if any(b.get('active_before')!=b.get('window') for b in row.get('task_batches',[])):errors.append('wrong_target_input')
    if [e.get('title') for e in row.get('effects',[])]!=EFFECT_TITLES:errors.append('task_effects')
    if row.get('old_window')==row.get('new_window') or row.get('old_gone') is not True:errors.append('replacement')
    if row.get('terminal_neutral') is not True:errors.append('terminal_neutral')
    if sorted(row.get('apps',[]))!=['Chromium','XTerm']:errors.append('apps')
    return errors
