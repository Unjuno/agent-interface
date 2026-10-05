"""One fresh Calc row, driven by bounded primary-review request files."""
import hashlib,json,os,pathlib,signal,subprocess,sys,time,traceback
from Xlib import X,display,protocol
from runtime.guarded_x11_v1.bridge import NativeHandleBridge
from runtime.backends.x11_v1.backend import X11Backend
from runtime.backends.x11_v1.session import X11RuntimeSession
ROOT=pathlib.Path('/src');OUT=pathlib.Path('/out');plan=json.loads((ROOT/'PLAN.json').read_text());spec=plan['rows'][int(sys.argv[1])]
def now():return time.monotonic_ns()
def save(name,value):(OUT/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
raw=dict(schema='calc-heldout-row-v1',spec=spec,events=[],errors=[],started_ns=now(),source_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in plan['source_hashes']},cgroups={p:pathlib.Path('/sys/fs/cgroup/'+p).read_text().strip() if pathlib.Path('/sys/fs/cgroup/'+p).exists() else 'unavailable' for p in ('cpu.max','memory.max','pids.max')})
actors=[];logs=[];d=b=g=None
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
    g=NativeHandleBridge(':151',{'owned':found[0]['id']},'owned',OUT/'guarded')
    b=g.backend
    observation=g.observe();raw['initial_guarded']=observation;save('READY.json',dict(observation=observation))
    path=OUT/'proposal.json';deadline=now()+150_000_000_000
    while not path.exists():
        if now()>deadline:raise RuntimeError('primary proposal unavailable')
        time.sleep(.02)
    proposal=json.loads(path.read_text());raw['proposal']=proposal
    if set(proposal)!=set(('x','y','source_sequence','artifact_sha256')) or any(type(proposal[k]) is not int for k in ('x','y','source_sequence')):raise RuntimeError('invalid proposal')
    if proposal['source_sequence']!=observation['sequence'] or proposal['artifact_sha256']!=observation['native']['artifact']['sha256']:raise RuntimeError('wrong source image/sequence')
    reference=g.mint_reference('a1_primary',observation['sequence'],[proposal['x'],proposal['y']],region_size=(90,14));raw['reference']=reference
    # Explicitly chosen finite keyboard tail from the viewed A1 anchor; no semantic sensor.
    tail=[dict(op='key_chord',keys=['Down']),dict(op='text',text='31',gap_ms=20),dict(op='key_chord',keys=['TAB']),dict(op='text',text='37',gap_ms=20),dict(op='key_chord',keys=['TAB']),dict(op='text',text='=A2*B2',gap_ms=20),dict(op='key_chord',keys=['ENTER']),dict(op='key_chord',keys=['CTRL','s']),dict(op='wait_update',timeout_ms=300)]
    raw['tail']=tail;raw['dispatch_start_ns']=now();raw['before_emissions']=b.emissions
    raw['guarded_result']=g.click('a1_primary',reference['offset'],tail=tail)
    raw['dispatch_end_ns']=now();raw['after_emissions']=b.emissions;raw['after_dispatch_physical']=physical()
    raw['final_guarded']=g.observe();save('FINAL.json',raw['final_guarded'])
    blob=doc.read_bytes();(OUT/'saved.fods').write_bytes(blob);raw['saved_sha256']=hashlib.sha256(blob).hexdigest();raw['guard_checks']=g.checks
    if raw['guarded_result']['status']!='completed':raise RuntimeError('cold shared dispatch not completed')
    old_emissions=b.emissions
    raw['reuse_old_result']=g.click('a1_primary',reference['offset'],tail=tail)
    raw['reuse_old_emission_delta']=b.emissions-old_emissions;raw['reuse_old_physical']=physical();save('raw.json',raw)
    if raw['reuse_old_result']['status']!='refused' or raw['reuse_old_emission_delta']!=0:raise RuntimeError('changed A1 patch did not refuse before input')
    repair_image=g.observe();save('REPAIR_READY.json',dict(observation=repair_image))
    path=OUT/'repair.proposal.json';deadline=now()+150_000_000_000
    while not path.exists():
        if now()>deadline:raise RuntimeError('primary repair proposal unavailable')
        time.sleep(.02)
    repair=json.loads(path.read_text());raw['repair_proposal']=repair
    if repair['source_sequence']!=repair_image['sequence'] or repair['artifact_sha256']!=repair_image['native']['artifact']['sha256']:raise RuntimeError('wrong repair source')
    ref2=g.mint_reference('a1_repaired',repair_image['sequence'],[repair['x'],repair['y']],region_size=(90,14));raw['repair_reference']=ref2
    tail2=[dict(op='key_chord',keys=['Down']),dict(op='text',text='47',gap_ms=20),dict(op='key_chord',keys=['TAB']),dict(op='text',text='53',gap_ms=20),dict(op='key_chord',keys=['TAB']),dict(op='text',text='=A2*B2',gap_ms=20),dict(op='key_chord',keys=['ENTER']),dict(op='key_chord',keys=['CTRL','s']),dict(op='wait_update',timeout_ms=300)]
    raw['repair_result']=g.click('a1_repaired',ref2['offset'],tail=tail2);raw['repair_physical']=physical();raw['repair_image']=g.observe();blob=doc.read_bytes();(OUT/'repair.fods').write_bytes(blob)
    if raw['repair_result']['status']!='completed':raise RuntimeError('fresh repair input incomplete')
    tail3=[dict(op='key_chord',keys=['Down']),dict(op='text',text='59',gap_ms=20),dict(op='key_chord',keys=['TAB']),dict(op='text',text='61',gap_ms=20),dict(op='key_chord',keys=['TAB']),dict(op='text',text='=A2*B2',gap_ms=20),dict(op='key_chord',keys=['ENTER']),dict(op='key_chord',keys=['CTRL','s']),dict(op='wait_update',timeout_ms=300)]
    raw['warm_result']=g.click('a1_repaired',ref2['offset'],tail=tail3);raw['warm_physical']=physical();raw['warm_image']=g.observe();blob=doc.read_bytes();(OUT/'warm.fods').write_bytes(blob)
    raw['all_guard_checks']=g.checks
    if raw['warm_result']['status']!='completed':raise RuntimeError('repaired alias warm input incomplete')
    raw['result']='CURRENT_SHARED_COLD_INVALIDATION_REPAIR_WARM_RETURNED_EFFECT_UNSCORED';save('raw.json',raw)
except Exception:raw['errors'].append(traceback.format_exc())
finally:
    if b:
        try:raw['cleanup_release']=b.release_all();raw['cleanup_physical']=physical();g.close() if g else b.close()
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
print(json.dumps(dict(errors=raw['errors'],extra=raw.get('extra_observations'),task_dispatches=1 if 'guarded_result' in raw else 0)));raise SystemExit(2 if raw['errors'] else 0)
