"""One fresh Calc row, driven by bounded primary-review request files."""
import hashlib,json,os,pathlib,signal,subprocess,sys,time,traceback
from Xlib import X,display,protocol
from geometry_guard import authorize
from runtime.backends.x11_v1.backend import X11Backend
from runtime.backends.x11_v1.session import X11RuntimeSession
ROOT=pathlib.Path('/src');OUT=pathlib.Path('/out');plan=json.loads((ROOT/'PLAN.json').read_text());spec=plan['rows'][int(sys.argv[1])]
def now():return time.monotonic_ns()
def save(name,value):(OUT/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
raw=dict(schema='calc-heldout-row-v1',spec=spec,events=[],errors=[],started_ns=now(),source_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in plan['source_hashes']},cgroups={p:pathlib.Path('/sys/fs/cgroup/'+p).read_text().strip() if pathlib.Path('/sys/fs/cgroup/'+p).exists() else 'unavailable' for p in ('cpu.max','memory.max','pids.max')})
actors=[];logs=[];d=b=None
def spawn(name,args,env):
    h=(OUT/(name+'.log')).open('wb');logs.append(h);p=subprocess.Popen(args,env=env,stdout=h,stderr=subprocess.STDOUT,start_new_session=True);actors.append((name,p));return p
def physical():
    start=now();bits=d.query_keymap();mask=d.screen().root.query_pointer().mask
    return dict(start_ns=start,end_ns=now(),keys=[i for i in range(256) if bits[i//8]&(1<<(i%8))],buttons=int(mask)&(X.Button1Mask|X.Button2Mask|X.Button3Mask))
def control(name):
    deadline=now()+600_000_000_000;path=OUT/(name+'.request.json')
    while not path.exists():
        if now()>deadline:raise RuntimeError('primary review/request timeout')
        time.sleep(.05)
    req=json.loads(path.read_text());raw['events'].append(dict(kind='primary_request',stage=name,read_ns=now(),request=req));return req
def snapshot(label):
    start=now();image=b.observe_read_only('owned','screen_physical_px',[0,0,1280,800]);row=dict(start_ns=start,end_ns=now(),image=image,physical=physical())
    if 'artifact' not in image:raise RuntimeError('exact PNG unavailable')
    save(label+'.json',row);return row
try:
    if raw['source_hashes']!=plan['source_hashes']:raise RuntimeError('source hash mismatch before effect')
    env=dict(os.environ,DISPLAY=':151',HOME='/out/home',SAL_USE_VCLPLUGIN='gen');pathlib.Path(env['HOME']).mkdir(exist_ok=True)
    doc=OUT/'heldout-comparison.fods';doc.write_bytes((ROOT/'blank.fods').read_bytes());raw['initial_document_sha256']=hashlib.sha256(doc.read_bytes()).hexdigest()
    xvfb=spawn('Xvfb',['Xvfb',':151','-screen','0','1280x800x24','-nolisten','tcp','-ac'],env)
    deadline=now()+3_000_000_000
    while d is None:
        try:d=display.Display(':151')
        except Exception:
            if now()>deadline or xvfb.poll() is not None:raise
            time.sleep(.02)
    spawn('openbox',['openbox','--sm-disable'],env);time.sleep(.2)
    lo=spawn('Calc',['libreoffice','-env:UserInstallation=file:///out/profile','--calc','--nologo','--norestore','--nodefault','--nofirststartwizard',str(doc)],env)
    deadline=now()+20_000_000_000;found=[]
    def walk(w,depth=0):
        rows=[]
        if depth>6:return rows
        for c in w.query_tree().children:
            try:
                prop=c.get_full_property(d.intern_atom('_NET_WM_NAME'),X.AnyPropertyType)
                net=bytes(prop.value).decode('utf8','replace') if prop is not None else ''
                title=c.get_wm_name();title=title.decode('utf8','replace') if isinstance(title,bytes) else str(title or '')
                rows.append(dict(id=c.id,title=net or title,map_state=c.get_attributes().map_state));rows.extend(walk(c,depth+1))
            except Exception:pass
        return rows
    while not found:
        rows=walk(d.screen().root);raw['last_window_tree']=rows
        found=[w for w in rows if w['title']=='heldout-comparison.fods — LibreOffice Calc' and w['map_state']==X.IsViewable]
        if len(found)>1:raise RuntimeError('ambiguous document windows')
        if now()>deadline or lo.poll() is not None:raise RuntimeError('document readiness failed')
        if not found:time.sleep(.05)
    time.sleep(1);raw['target']=found[0]
    b=X11Backend(':151',{'owned':found[0]['id']});b.configure_capture_artifacts(OUT/'images')
    raw['initial']=snapshot('initial');save('raw.json',raw)
    window=d.create_resource_object('window',found[0]['id'])
    def geometry():
        g=window.get_geometry(); p=d.screen().root.translate_coords(window,0,0)
        return dict(window_id=window.id,x=p.x,y=p.y,width=g.width,height=g.height,map_state=window.get_attributes().map_state)
    raw['tasks']=[];raw['guard_attempts']=[]
    def execute(label,a_value,b_value,x,y,binding):
        current=geometry();decision=authorize(binding,[current])
        attempt=dict(label=label,cached=binding,current=current,decision=decision,input_dispatches=0,start_ns=now())
        raw['guard_attempts'].append(attempt)
        if decision!='ACCEPT':
            attempt['end_ns']=now();save('raw.json',raw);return decision
        ops=[dict(op='focus',target='owned'),dict(op='pointer_move',frame='screen_physical_px',x=x,y=y),dict(op='pointer_button',button='left',down=True),dict(op='pointer_button',button='left',down=False)]
        for segment in (str(a_value),'TAB',str(b_value),'TAB','=A2*B2','ENTER'):
            if segment in ('TAB','ENTER'):ops.append(dict(op='key_chord',keys=[segment]))
            else:
                for char in segment:ops.extend([dict(op='text',text=char),dict(op='wait_update',timeout_ms=20)])
        ops.extend([dict(op='key_chord',keys=['CTRL','s']),dict(op='wait_update',timeout_ms=300),dict(op='release_all')])
        program=dict(schema='agent-interface/program-v1',program_id=label,source=dict(observation_seq=1,binding_revision=1),authority=dict(lease_id='owned-real-calc-construction',expires_at_ns=now()+10_000_000_000),terminal=dict(release_all_required=True),ops=ops)
        attempt['input_dispatches']=1;start=now();receipt=X11RuntimeSession(b).dispatch(program,current_observation_seq=1,current_binding_revision=1);end=now()
        if receipt['status']!='completed':raise RuntimeError('native dispatch failed '+label)
        image=snapshot(label);saved=doc.read_bytes();(OUT/(label+'.fods')).write_bytes(saved)
        raw['tasks'].append(dict(label=label,a=a_value,b=b_value,program=program,receipt=receipt,start_ns=start,end_ns=end,image=image,saved_sha256=hashlib.sha256(saved).hexdigest(),physical=physical()))
        attempt['end_ns']=now();save('raw.json',raw);return decision
    cached=geometry();raw['cold_geometry']=cached
    execute('cold',13,17,80,168,cached)
    execute('warm',19,23,80,168,cached)
    state=window.get_full_property(d.intern_atom('_NET_WM_STATE'),X.AnyPropertyType)
    raw['wm_state_before']=[d.get_atom_name(int(a)) for a in state.value] if state is not None else []
    event=protocol.event.ClientMessage(window=window.id,client_type=d.intern_atom('_NET_WM_STATE'),data=(32,[0,d.intern_atom('_NET_WM_STATE_MAXIMIZED_VERT'),d.intern_atom('_NET_WM_STATE_MAXIMIZED_HORZ'),1,0]))
    d.screen().root.send_event(event,event_mask=X.SubstructureRedirectMask|X.SubstructureNotifyMask);d.sync();time.sleep(.3)
    window.configure(x=80,y=55,width=900,height=600);d.sync();time.sleep(.3)
    raw['moved_geometry']=geometry();snapshot('moved')
    stale=execute('stale',47,53,80,168,cached)
    if stale!='STALE_GEOMETRY':raise RuntimeError('stale operation was not refused')
    repaired=geometry()
    execute('repair',47,53,160,204,repaired)
    execute('warm-after-repair',59,61,160,204,repaired)
    raw['result']='CONSTRUCTION_NATIVE_CACHE_AND_SAVED_DOCUMENT_ONLY'
except Exception:raw['errors'].append(traceback.format_exc())
finally:
    if b:
        try:raw['cleanup_release']=b.release_all();raw['cleanup_physical']=physical();b.close()
        except Exception:raw['errors'].append(traceback.format_exc())
    if d:d.close()
    for name,p in reversed(actors):
        if p.poll() is None:os.killpg(p.pid,signal.SIGTERM)
        try:code=p.wait(5)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL);code=p.wait(3);raw['errors'].append(name+' required SIGKILL')
        raw.setdefault('terminal',[]).append(dict(name=name,pid=p.pid,exit_code=code,cleanup='group TERM/parent wait; not graceful close/full descendant proof'))
    for h in logs:h.close()
    raw['ended_ns']=now();save('raw.json',raw)
print(json.dumps(dict(errors=raw['errors'],extra=raw.get('extra_observations'),task_dispatches=1 if 'dispatch_start_ns' in raw else 0)));raise SystemExit(2 if raw['errors'] else 0)
