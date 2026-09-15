from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,subprocess,time,traceback
from pathlib import Path
from Xlib import X,XK
from Xlib import display as xdisplay
from Xlib.ext import xtest

SEED=994601
VALID_NS=500_000_000
PLANNED_HOLD_NS=1_500_000_000
LIFECYCLE_NS=400_000_000
EXPECTED_BRIDGE='37e544086fe70087c0a2e6c03ce8c42c1c5dd71989f7fe541eb9055b3551eb52'
EXPECTED_NORMALIZER='dc664652c7c29b002005feb7b69122d29619a449c6ad781a65ac5abfaa186d41'
H=Path(__file__).resolve().parent
ROOT=H.parent
ABI=ROOT/'inkscape_authority_ended_abi_v2'
BRIDGE=ABI/'authority_ended_bridge_v2.py'
NORMALIZER=ABI/'post_authority_normalize_v2.py'

def sha256(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def down_keycodes(d):
    keymap=d.query_keymap();out=[]
    for keycode in range(8,256):
        if keymap[keycode//8] & (1<<(keycode%8)): out.append(keycode)
    return out

def pointer_buttons_down(root):
    mask=root.query_pointer().mask
    masks=[X.Button1Mask,X.Button2Mask,X.Button3Mask,X.Button4Mask,X.Button5Mask]
    return [i+1 for i,m in enumerate(masks) if mask & m]

def active_inkscape(d):
    root=d.screen().root
    prop=root.get_full_property(d.intern_atom('_NET_ACTIVE_WINDOW'),X.AnyPropertyType)
    if prop is None or len(prop.value)!=1 or int(prop.value[0])==0: return None
    w=d.create_resource_object('window',int(prop.value[0]))
    try: cls=w.get_wm_class();name=w.get_wm_name();attrs=w.get_attributes()
    except Exception: return None
    if not cls or 'Inkscape' not in cls or attrs.map_state!=X.IsViewable: return None
    return {'id':int(w.id),'name':name,'wm_class':list(cls),'map_state':int(attrs.map_state)}

def capture_root(root,sequence):
    g=root.get_geometry();width=min(int(g.width),320);height=min(int(g.height),240)
    started=time.monotonic_ns();im=root.get_image(0,0,width,height,X.ZPixmap,0xffffffff);finished=time.monotonic_ns()
    data=im.data.encode('latin1') if isinstance(im.data,str) else im.data
    return {'sequence':sequence,'capture_started_ns':started,'capture_ns':finished,'width':width,'height':height,'raw_bytes':len(data),'raw_sha256':hashlib.sha256(data).hexdigest()}

def terminate(p,timeout=5):
    if p is None or p.poll() is not None:return
    p.terminate()
    try:p.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill();p.wait(timeout=timeout)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--display',default=':103');args=ap.parse_args()
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False)
    result_path=out/'formal-result.json';events=[];xp=op=ip=None;d=None
    def ev(kind,**data): events.append({'event':kind,'monotonic_ns':time.monotonic_ns(),**data})
    result={'schema':'inkscape-abi-v2-source-first-live-v1-formal-result','result_id':'inkscape-abi-v2-source-first-live-v1-20260916-994601','formal_seed':SEED,'formal_retries':0,'pass':False,'decision':'RETAIN_LIVE_FAILURE','gates':{},'events':events}
    try:
        bridge_sha=sha256(BRIDGE);normalizer_sha=sha256(NORMALIZER);runner_sha=sha256(Path(__file__))
        result['source_sha256']={'live_runner.py':runner_sha,'authority_ended_bridge_v2.py':bridge_sha,'post_authority_normalize_v2.py':normalizer_sha}
        source_gate=(bridge_sha==EXPECTED_BRIDGE and normalizer_sha==EXPECTED_NORMALIZER)
        result['gates']['source_identities']=source_gate
        if not source_gate: raise RuntimeError('source identity mismatch')
        bridge=load_module(BRIDGE,'source_first_live_bridge_v2');normalizer=load_module(NORMALIZER,'source_first_live_normalizer_v2')
        display_num=args.display.lstrip(':').split('.')[0]
        lock=Path('/tmp')/f'.X{display_num}-lock';socket=Path('/tmp/.X11-unix')/f'X{display_num}'
        if lock.exists() or socket.exists(): raise RuntimeError('requested X display already exists')
        auth=out/'xauth';auth.touch()
        env=os.environ.copy();env['DISPLAY']=args.display;env['XAUTHORITY']=str(auth);env['NO_AT_BRIDGE']='1'
        os.environ['DISPLAY']=args.display;os.environ['XAUTHORITY']=str(auth)
        xp=subprocess.Popen(['Xvfb',args.display,'-ac','-screen','0','1024x768x24'],stdout=(out/'xvfb.stdout').open('w'),stderr=(out/'xvfb.stderr').open('w'))
        time.sleep(.35)
        op=subprocess.Popen(['openbox'],env=env,stdout=(out/'openbox.stdout').open('w'),stderr=(out/'openbox.stderr').open('w'))
        time.sleep(.4)
        svg=out/'shape.svg';svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200"><rect x="50" y="50" width="40" height="30" fill="blue"/></svg>\n',encoding='utf-8');svg_before=sha256(svg)
        ip=subprocess.Popen(['inkscape',str(svg)],env=env,stdout=(out/'inkscape.stdout').open('w'),stderr=(out/'inkscape.stderr').open('w'))
        d=xdisplay.Display(args.display);active=None
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            active=active_inkscape(d)
            if active and active.get('name') and 'shape.svg' in active['name']: break
            time.sleep(.05)
        active_gate=bool(active and active.get('name') and 'shape.svg' in active['name'])
        result['gates']['active_inkscape_document']=active_gate;result['active_window']=active
        if not active_gate: raise RuntimeError('active Inkscape document not established')
        root=d.screen().root;sequence=1;pre=capture_root(root,sequence);release_sequence=sequence;ev('pre_observation',capture=pre)
        shift=d.keysym_to_keycode(XK.string_to_keysym('Shift_L'))
        if not shift: raise RuntimeError('Shift_L keycode unavailable')
        if down_keycodes(d): raise RuntimeError('unexpected key down before authority admission')
        intent_token=hashlib.sha256(f'live-abi-v2:{SEED}:authority-epoch-1'.encode()).hexdigest()[:32]
        admitted_ns=time.monotonic_ns();valid_until_ns=admitted_ns+VALID_NS;planned_hold_end_ns=admitted_ns+PLANNED_HOLD_NS
        xtest.fake_input(d,X.KeyPress,shift);d.sync();time.sleep(.02)
        press_gate=shift in down_keycodes(d);result['gates']['shift_down_observed']=press_gate;ev('input_admitted',key='Shift_L',intent_token=intent_token,valid_until_ns=valid_until_ns,press_observed=press_gate)
        while time.monotonic_ns()<valid_until_ns+15_000_000: time.sleep(.002)
        expiry_detected_ns=time.monotonic_ns()
        expiry_gate=expiry_detected_ns>=valid_until_ns and expiry_detected_ns<planned_hold_end_ns
        result['gates']['expired_before_planned_hold_end']=expiry_gate
        xtest.fake_input(d,X.KeyRelease,shift);d.sync();time.sleep(.015)
        release_verified_ns=time.monotonic_ns();keys_down=down_keycodes(d);buttons_down=pointer_buttons_down(root);release_verified=(keys_down==[] and buttons_down==[])
        result['gates']['release_verified_empty']=release_verified;ev('release_verified',verified=release_verified,keys_down=keys_down,buttons_down=buttons_down,verified_ns=release_verified_ns)
        post_release_input_admissions=0;tail_sent=False;lifecycle_deadline_ns=release_verified_ns+LIFECYCLE_NS
        sequence+=1;c1=capture_root(root,sequence);time.sleep(.05);sequence+=1;c2=capture_root(root,sequence);snapshot_finished_ns=time.monotonic_ns()
        post_release={'captures':2,'sequences':[c1['sequence'],c2['sequence']],'records':[c1,c2],'error':None}
        post_authority=normalizer.normalize(post_release,release_sequence=release_sequence,lifecycle_deadline_ns=lifecycle_deadline_ns,snapshot_finished_ns=snapshot_finished_ns)
        capture_gate=(post_authority.get('captures')==2 and post_authority.get('sequences')==[2,3] and post_authority.get('sequence')==3 and post_authority.get('selection_rule')=='latest' and post_authority.get('within_lifecycle_deadline') is True and c1['raw_bytes']>0 and c2['raw_bytes']>0)
        result['gates']['two_passive_captures_within_lifecycle']=capture_gate;ev('post_authority_observation',post_authority=post_authority,captures=[c1,c2])
        terminal={'status':'authority_ended','legacy_terminal_status':'expired','steps_completed':0,'release':{'verified':release_verified,'keys_down':keys_down,'buttons_down':buttons_down,'verified_ns':release_verified_ns,'intent_token':intent_token},'interruption':{'intent_token':intent_token,'record':{'reason':'expired','verified':release_verified,'keys_down':keys_down,'buttons_down':buttons_down,'valid_until_ns':valid_until_ns,'detected_ns':expiry_detected_ns}},'post_release_observation':post_release,'post_authority_observation':post_authority,'post_release_input_admissions':post_release_input_admissions}
        no_tail_gate=(post_release_input_admissions==0 and terminal['steps_completed']==0 and post_authority.get('tail_program_steps_resumed')==0 and tail_sent is False)
        result['gates']['zero_post_release_input_and_tail_resume']=no_tail_gate
        receipt={'terminal_status':'authority_ended','release_verified':release_verified,'keys_down':keys_down,'buttons_down':buttons_down,'post_release_input_admissions':post_release_input_admissions,'steps_completed':0,'post_authority':post_authority,'authority_end_id':intent_token}
        decision=bridge.to_caller_execution_decision(receipt)
        bridge_gate=decision=={'status':'safe_yield','reason':'authority_unavailable','completed_actions':0};result['gates']['bridge_safe_yield']=bridge_gate
        svg_after=sha256(svg);svg_gate=(svg_after==svg_before and b'999' not in svg.read_bytes());result['gates']['svg_unchanged_no_tail_text']=svg_gate
        result.update({'intent_token':intent_token,'authority_end_id':intent_token,'timing':{'admitted_ns':admitted_ns,'valid_until_ns':valid_until_ns,'expiry_detected_ns':expiry_detected_ns,'planned_hold_end_ns':planned_hold_end_ns,'release_verified_ns':release_verified_ns,'lifecycle_deadline_ns':lifecycle_deadline_ns,'snapshot_finished_ns':snapshot_finished_ns,'expiry_late_ns':expiry_detected_ns-valid_until_ns,'lifecycle_slack_ns':lifecycle_deadline_ns-snapshot_finished_ns},'terminal':terminal,'receipt':receipt,'decision':decision,'captures':[pre,c1,c2],'svg_sha256_before':svg_before,'svg_sha256_after':svg_after,'inkscape_version':subprocess.check_output(['inkscape','--version'],text=True).strip(),'display':args.display})
        all_gates=(len(result['gates'])==9 and all(result['gates'].values()))
        result['pass']=all_gates;result['decision']='RETAIN_SOURCE_FIRST_LIVE_ABI_V2_SEMANTIC_REPRODUCTION' if all_gates else 'RETAIN_LIVE_FAILURE'
    except Exception as e:
        result['error']={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
    finally:
        if d is not None:
            try:d.close()
            except Exception:pass
        terminate(ip);terminate(op);terminate(xp,3)
        result_path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        (out/'events.json').write_text(json.dumps(events,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        print(json.dumps({'pass':result['pass'],'decision':result['decision'],'gates':result['gates'],'result':str(result_path)},sort_keys=True))
    raise SystemExit(0 if result['pass'] else 2)

if __name__=='__main__': main()
