from __future__ import annotations
import hashlib, json, os, subprocess, tempfile, time
from pathlib import Path
from Xlib import X, XK, display
from Xlib.ext import xtest

TASK='MULTI-APP-GUARDED-RECOVERY-R3-20260918-003'
CYCLES=3
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
    rootdir=Path(tempfile.mkdtemp(prefix=f'ai1769-{session_id}-'))
    auth=rootdir/'.Xauthority';auth.write_bytes(b'')
    env=os.environ.copy();env['DISPLAY']=disp;env['XAUTHORITY']=str(auth)
    os.environ['DISPLAY']=disp;os.environ['XAUTHORITY']=str(auth)
    f_xv=(rootdir/'xvfb.err').open('w');f_wm=(rootdir/'openbox.err').open('w')
    xv=launch(['Xvfb',disp,'-screen','0','1280x800x24','-ac'],env,f_xv);time.sleep(.25)
    wm=launch(['openbox'],env,f_wm);time.sleep(.4)
    d=display.Display(disp);root=d.screen().root
    atom_clients=d.intern_atom('_NET_CLIENT_LIST');atom_name=d.intern_atom('_NET_WM_NAME');utf8=d.intern_atom('UTF8_STRING')
    ps=[];opened=[];refusals=[];batches=[];effects=[];replacements=[];task_input_batches=0
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
    def refuse(cycle,reason,details):
        before=task_input_batches
        row={'cycle':cycle,'reason':reason,'input_before':before,'input_after':task_input_batches,'at_ns':time.perf_counter_ns()}
        row.update(details);refusals.append(row)
    def task_shortcut(cycle,wid,mods,keyname,expected,phase):
        nonlocal task_input_batches
        active=focus_id();before=task_input_batches
        if active!=wid:raise RuntimeError(f'wrong_active_before_task:{active}!={wid}')
        chord(mods,keyname);task_input_batches+=1
        t=wait_exact_title(wid,expected);after_hash=framebuffer_hash()
        batches.append({'cycle':cycle,'phase':phase,'window':int(wid),'active_before':int(active),'input_before':before,'input_after':task_input_batches,'shortcut':'+'.join(mods+[keyname]),'expected_title':expected})
        effects.append({'cycle':cycle,'phase':phase,'window':int(wid),'title':t,'observed_ns':time.perf_counter_ns(),'framebuffer_sha256':after_hash})
    try:
        pdir=rootdir/'chromium-0';pdir.mkdir();err=(rootdir/'chromium-0.err').open('w');opened.append(err)
        current_proc=launch(['chromium','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--user-data-dir='+str(pdir),'--no-first-run','about:blank'],env,err);ps.append(current_proc)
        current=wait_title('Chromium',20);focus(current)
        binding={'window':int(current),'geometry':geom(current),'focus':focus_id(),'observation_hash':framebuffer_hash()}
        xerr=(rootdir/'xterm.err').open('w');opened.append(xerr)
        peer_proc=launch(['xterm','-T',f'AI1769-PEER-{session_id}'],env,xerr);ps.append(peer_proc)
        peer=wait_title('AI1769-PEER',10)

        for cycle in range(1,CYCLES+1):
            subprocess.run(['wmctrl','-ir',hex(current),'-b','remove,maximized_vert,maximized_horz'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            subprocess.run(['wmctrl','-ir',hex(current),'-e','0,80,60,900,650'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(.4)
            cur_geom=geom(current)
            if cur_geom==binding['geometry']:raise RuntimeError(f'geometry_drift_missing:{cycle}')
            refuse(cycle,'REFUSE_GEOMETRY',{'bound_geometry':binding['geometry'],'current_geometry':cur_geom,'window':int(current)})
            binding['geometry']=cur_geom;focus(current);binding['focus']=focus_id();binding['observation_hash']=framebuffer_hash()
            task_shortcut(cycle,current,['Control_L'],'j',EFFECT_TITLES[0],1)

            focus(peer);cur_focus=focus_id()
            if cur_focus==binding['window']:raise RuntimeError(f'focus_drift_missing:{cycle}')
            refuse(cycle,'REFUSE_FOCUS',{'bound_window':binding['window'],'current_focus':cur_focus})
            focus(current);binding['focus']=focus_id();binding['observation_hash']=framebuffer_hash()
            task_shortcut(cycle,current,['Control_L'],'h',EFFECT_TITLES[1],2)

            ndir=rootdir/f'chromium-{cycle}';ndir.mkdir();nerr=(rootdir/f'chromium-{cycle}.err').open('w');opened.append(nerr)
            next_proc=launch(['chromium','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--user-data-dir='+str(ndir),'--no-first-run','about:blank'],env,nerr);ps.append(next_proc)
            new=wait_title('Chromium',20,exclude={current});focus(new);old=int(current);stop(current_proc)
            end=time.time()+6
            while current in clients() and time.time()<end:time.sleep(.05)
            old_gone=current not in clients()
            if not old_gone or int(new)==binding['window']:raise RuntimeError(f'replacement_missing:{cycle}')
            refuse(cycle,'REFUSE_BINDING',{'bound_window':binding['window'],'replacement_window':int(new),'old_gone':old_gone})
            replacements.append({'cycle':cycle,'old_window':old,'new_window':int(new),'old_gone':old_gone})
            current=int(new);current_proc=next_proc
            binding={'window':current,'geometry':geom(current),'focus':focus_id(),'observation_hash':framebuffer_hash()}
            task_shortcut(cycle,current,['Control_L'],'j',EFFECT_TITLES[2],3)

            binding['observation_hash']=framebuffer_hash();focus(current);chord(['Control_L','Shift_L'],'Delete');time.sleep(.8)
            clear_title=wait_exact_title(current,'chrome://settings/clearBrowserData - Chromium')
            current_hash=framebuffer_hash()
            if current_hash==binding['observation_hash']:raise RuntimeError(f'observation_drift_missing:{cycle}')
            refuse(cycle,'REFUSE_OBSERVATION',{'bound_observation_hash':binding['observation_hash'],'current_observation_hash':current_hash,'perturbation_title':clear_title,'window':current})
            binding['observation_hash']=current_hash;focus(current);binding['focus']=focus_id()
            task_shortcut(cycle,current,['Control_L'],'h',EFFECT_TITLES[3],4)
            time.sleep(.15)

        return {'task':TASK,'session_id':session_id,'cycles_completed':CYCLES,'refusals':refusals,'task_batches':batches,'effects':effects,'replacements':replacements,'task_input_batches':task_input_batches,'terminal_window':current,'terminal_neutral':neutral(),'apps':['Chromium','XTerm'],'display':disp}
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
    expected_reasons=REFUSAL_ORDER*CYCLES
    expected_titles=EFFECT_TITLES*CYCLES
    if row.get('cycles_completed')!=CYCLES:errors.append('cycle_count')
    if [r.get('reason') for r in row.get('refusals',[])]!=expected_reasons:errors.append('refusal_order')
    if [r.get('cycle') for r in row.get('refusals',[])]!=sum(([c]*4 for c in range(1,CYCLES+1)),[]):errors.append('refusal_cycle')
    if any(r.get('input_before')!=r.get('input_after') for r in row.get('refusals',[])):errors.append('stale_task_input')
    batches=row.get('task_batches',[])
    if row.get('task_input_batches')!=4*CYCLES or len(batches)!=4*CYCLES:errors.append('batch_count')
    if any(b.get('active_before')!=b.get('window') for b in batches):errors.append('wrong_target_input')
    eff=row.get('effects',[])
    if [e.get('title') for e in eff]!=expected_titles:errors.append('task_effects')
    if [e.get('cycle') for e in eff]!=sum(([c]*4 for c in range(1,CYCLES+1)),[]):errors.append('effect_cycle')
    reps=row.get('replacements',[])
    if len(reps)!=CYCLES or any(x.get('old_window')==x.get('new_window') or x.get('old_gone') is not True for x in reps):errors.append('replacement')
    if row.get('terminal_neutral') is not True:errors.append('terminal_neutral')
    if sorted(row.get('apps',[]))!=['Chromium','XTerm']:errors.append('apps')
    return errors
