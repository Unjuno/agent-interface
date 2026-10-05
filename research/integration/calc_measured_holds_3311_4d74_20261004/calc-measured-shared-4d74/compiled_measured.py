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
    tail=[dict(op='key_chord',keys=['Down']),dict(op='text',text='17',gap_ms=20),dict(op='key_chord',keys=['TAB']),dict(op='text',text='23',gap_ms=20),dict(op='key_chord',keys=['TAB']),dict(op='text',text='=A2*B2',gap_ms=20),dict(op='key_chord',keys=['ENTER']),dict(op='key_chord',keys=['CTRL','s']),dict(op='wait_update',timeout_ms=300)]
    from runtime.core_v1.compiled_gui import run
    from PIL import Image
    roi=(36,161,305,175)
    from ocr_reader import read_values
    from effect_predicate import visible_row_predicate
    templates={'first':['17','23','391'],'second':['37','43','1591']}
    raw['native_attempts']=[];raw['graph_events']=[];raw['images']=[];raw['pixel_checks']=[];raw['physical_checks']=[]
    current={'alias':'a1_primary','reference':reference}
    def observe_graph(request):
        image=g.observe();raw['images'].append(image)
        blob=Image.open(image['native']['artifact']['path']).convert('RGB').crop(roi).tobytes()
        expected='first' if request['state']=='second' else 'second'
        decoded=read_values(image['native']['artifact']['path']);match=visible_row_predicate(decoded,templates[expected])
        raw['pixel_checks'].append(dict(state=request['state'],template=expected,region=list(roi),decoded_values=decoded,expected_values=templates[expected],rgb_sha256=hashlib.sha256(blob).hexdigest(),matches=match))
        return dict(sequence=image['sequence'],captured_ns=image['native']['capture_started_ns'],surface='owned',predicates={'ready':True,'row_visible':match},evidence_ref='frame_'+str(image['sequence']),evidence_digest=image['native']['artifact']['sha256'])
    def admit_graph(request):
        sequence=request['observation']['sequence'];image=g.history[sequence]
        if request['action']=='second':
            current['alias']='a1_second';current['reference']=g.mint_reference(current['alias'],sequence,[proposal['x'],proposal['y']],region_size=(90,14));raw['second_reference']=current['reference']
        resolved=g.store.resolve_point(current['alias'],current['reference']['offset'],image[0],image[1],time.monotonic_ns(),session_scope=g.scope)
        raw.setdefault('graph_admissions',[]).append(resolved)
        return dict(eligible=resolved['eligible'],status='revalidated' if resolved['eligible'] else 'missing',authorization='one_scoped_candidate',expected_sequence=sequence,valid_until_ns=time.perf_counter_ns()+1_000_000_000)
    def execute_graph(request):
        selected=tail if request['action']=='first' else [dict(op='key_chord',keys=['Down']),dict(op='text',text='37',gap_ms=20),dict(op='key_chord',keys=['TAB']),dict(op='text',text='43',gap_ms=20),dict(op='key_chord',keys=['TAB']),dict(op='text',text='=A2*B2',gap_ms=20),dict(op='key_chord',keys=['ENTER']),dict(op='key_chord',keys=['CTRL','s']),dict(op='wait_update',timeout_ms=300)]
        receipt=g.click(current['alias'],current['reference']['offset'],tail=selected,expires_at_ns=request['valid_until_ns']);raw['native_attempts'].append(receipt)
        physical_state=physical();raw['physical_checks'].append(physical_state)
        (OUT/(request['action']+'.fods')).write_bytes(doc.read_bytes())
        releases=receipt.get('execution',{}).get('releases',[])
        verified=bool(releases) and all(r.get('verified') is True and r.get('keys_down')==[] and r.get('buttons_down')==[] for r in releases)
        return dict(status=receipt['status'],action_id='native_'+request['action'],effect_ref='pixel_effect_'+request['action'],release=dict(verified=verified,keys_down=physical_state['keys'],buttons_down=[] if physical_state['buttons']==0 else ['held']))
    def verify_effect(request):
        raw.setdefault('verifier_calls',[]).append(request)
        return {'status':'succeeded' if request['observation']['predicates']['row_visible'] else 'failed','evidence_ref':request['observation']['evidence_ref']}
    def branch(action,next_state):return dict(when={'ready':True},outcome='action',action=action,next_state=next_state,reason=None)
    interface=dict(format='compiled-gui-interface-v1',interface_id='calc_digitunavailable_g09',session_scope='owned_g09',surface='owned',predicates=['ready','row_visible'],symbols={'anchor':dict(kind='target_reference',target_reference='a1_primary',identity_predicate='ready',dependencies=['ready'])},actions={name:dict(target_symbol='anchor',operation='enter_product',expected_effect={'row_visible':True}) for name in ('first','second')},method=dict(name='pixel_verified_two_saves',version='1',initial_state='first',max_transitions=2,max_runtime_ms=10000,states={'first':{'branches':[branch('first','second')]},'second':{'branches':[branch('second','done')]},'done':{'branches':[dict(when={'ready':True},outcome='complete',action=None,next_state=None,reason=None)]}}))
    raw['interface']=interface;raw['graph_started_ns']=now()
    raw['compiled_result']=run(interface,dict(observe=observe_graph,admit=admit_graph,execute=execute_graph,verify_effect=verify_effect,cancelled=lambda:False,journal=lambda event:raw['graph_events'].append(event)))
    raw['graph_ended_ns']=now();raw['final_guarded']=g.observe()
    save('batch.DONE.json',dict(image=dict(image=raw['final_guarded']['native'])))
    blob=doc.read_bytes();(OUT/'saved.fods').write_bytes(blob);raw['saved_sha256']=hashlib.sha256(blob).hexdigest()
    raw['result']='COMPILED_UNKNOWN_EFFECT_CONSTRUCTION_RETURNED_UNSCORED';save('raw.json',raw)
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
print(json.dumps(dict(errors=raw['errors'],native_attempts=len(raw.get('native_attempts',[])),compiled=raw.get('compiled_result',{}).get('reason'))));raise SystemExit(2 if raw['errors'] else 0)
