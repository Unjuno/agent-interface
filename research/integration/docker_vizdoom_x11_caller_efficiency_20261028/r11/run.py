import argparse, hashlib, json, os, threading, time
from pathlib import Path
from Xlib import display, XK
import vizdoom as vd
from runtime.guarded_x11_v1.bridge import NativeHandleBridge
from runtime.guarded_x11_v1 import compiled

HOLD_MS=600
THRESHOLD=0.1
SEEDS={3:2026102913,4:2026102914}

def write_json(p,v): Path(p).write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n')
def coords(g): return {'x':float(g.get_game_variable(vd.GameVariable.POSITION_X)), 'y':float(g.get_game_variable(vd.GameVariable.POSITION_Y))}
def key_down(d,code):
    m=d.query_keymap();return bool(m[code//8] & (1 << (code%8)))
def effect_pass(before,after): return abs(after['x']-before['x'])>=THRESHOLD or abs(after['y']-before['y'])>=THRESHOLD

def graph_spec(bridge):
    return {'format':'compiled-gui-interface-v1','interface_id':'map01-forward-efficiency-r1',
        'session_scope':bridge.scope,'surface':compiled.surface(bridge),
        'predicates':['ready','moved'],
        'symbols':{'game':{'kind':'target_reference','target_reference':'forward_target',
                           'identity_predicate':'ready','dependencies':['ready']}},
        'actions':{'forward':{'target_symbol':'game','operation':'move_forward_600ms',
                              'expected_effect':{'moved':True}}},
        'method':{'name':'one-forward-action','version':'1','initial_state':'waiting',
                  'max_transitions':1,'max_runtime_ms':9000,
                  'states':{
                    'waiting':{'branches':[{'when':{'ready':True,'moved':False},'outcome':'action',
                                             'action':'forward','next_state':'done','reason':None}]},
                    'done':{'branches':[{'when':{'ready':True,'moved':True},'outcome':'complete',
                                         'action':None,'next_state':None,'reason':None}]}}}}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--arm',choices=['direct','compiled'],required=True);ap.add_argument('--pair',type=int,choices=[3,4],required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False);bridge_dir=out/'bridge'
    seed=SEEDS[args.pair];result={'arm':args.arm,'pair':args.pair,'seed':seed,'hold_ms':HOLD_MS,'runtime':'Docker Desktop Linux Engine + Xvfb -cc 4','source_route':args.arm,'no_model_provider_calls':True,'error':None}
    cfg=Path('/tmp')/f'map01-eff-r11-{args.arm}-{args.pair}.ini';cfg.write_text('[Doom.Bindings]\nw=+forward\ne=+use\nleftarrow=+left\nrightarrow=+right\n')
    game=bridge=observer=None;worker=None
    try:
        game=vd.DoomGame();game.set_doom_game_path(str(Path(vd.__file__).resolve().parent/'freedoom2.wad'));game.set_doom_map('MAP01');game.set_doom_config_path(str(cfg));game.set_mode(vd.Mode.ASYNC_SPECTATOR);game.set_ticrate(35);game.set_seed(seed);game.set_doom_skill(1);game.set_episode_timeout(35*30);game.set_window_visible(True);game.set_sound_enabled(False);game.set_console_enabled(False);game.set_screen_resolution(vd.ScreenResolution.RES_640X480);game.set_render_all_frames(True);game.set_render_hud(True);game.set_available_buttons([vd.Button.MOVE_FORWARD,vd.Button.USE,vd.Button.TURN_LEFT,vd.Button.TURN_RIGHT]);game.set_available_game_variables([vd.GameVariable.POSITION_X,vd.GameVariable.POSITION_Y]);game.init();time.sleep(.35);game.advance_action(1, True);time.sleep(.05)
        observer=display.Display(os.environ['DISPLAY']);wins=[]
        for win in observer.screen().root.query_tree().children:
            title=win.get_wm_name()
            if title and 'VIZDOOM' in title.upper() and win.get_attributes().map_state==2:wins.append((win.id,title,win.get_geometry().width,win.get_geometry().height))
        if len(wins)!=1:raise RuntimeError(f'expected one mapped ViZDoom window, got {wins!r}')
        wid,title,width,height=wins[0];result['target']={'window_id':wid,'title':title,'width':width,'height':height,'display':os.environ['DISPLAY']}
        bridge=NativeHandleBridge(os.environ['DISPLAY'],{'doom':wid},'doom',str(bridge_dir));bridge.backend.focus('doom')
        result['window_geometry']=bridge.backend.geometry('doom')
        # Identical out-of-clock setup for both routes: acquire and mint one
        # HUD-region handle, then prove that it resolves against a fresh capture.
        pre=bridge.observe();geo=result['window_geometry'];point=(geo['x']+44,geo['y']+height-22)
        minted=bridge.mint_reference('forward_target',pre['sequence'],point,region_size=(24,38));offset=minted['offset'];result['preflight_source_sequence']=pre['sequence'];result['minted_reference']=minted
        time.sleep(.10);check=bridge.observe();check_image=bridge.history[check['sequence']][1];resolution=bridge.store.resolve_point('forward_target',offset,check,check_image,time.monotonic_ns(),session_scope=bridge.scope);result['alias_preflight']={k:resolution.get(k) for k in ('eligible','status','valid_until_ns')}
        if not resolution.get('eligible'):raise RuntimeError('grounded HUD reference did not survive fresh capture: '+str(resolution))
        baseline=coords(game);result['position_before']=baseline
        code=observer.keysym_to_keycode(XK.string_to_keysym('w'));result['w_keycode']=code
        if not code or key_down(observer,code):raise RuntimeError('W keycode unavailable or already down at preflight')
        tail=[{'op':'key_state','key':'w','down':True},{'op':'wait_update','timeout_ms':HOLD_MS},{'op':'key_state','key':'w','down':False}]
        tick_pending={'value':False}
        def perceive(native,image):
            if tick_pending['value']:
                game.advance_action(1, True)
                tick_pending['value']=False
                result['effect_oracle_sync_tick']='one game.advance_action(1, True) after key release and before post-action position readback'
            c=coords(game);moved=effect_pass(baseline,c)
            return {'ready':bool(image.mode=='RGB' and image.width==observer.screen().width_in_pixels and native.get('native',{}).get('artifact',{}).get('sha256')),'moved':bool(moved)}
        def verify_effect(payload,native,image):
            after=coords(game);ok=effect_pass(baseline,after)
            result['oracle_at_verification']={'position':after,'delta':{'x':after['x']-baseline['x'],'y':after['y']-baseline['y']},'passed':ok,'evidence_ref':payload.get('observation',{}).get('evidence_ref')}
            return {'status':'succeeded' if ok else 'failed','evidence_ref':payload['observation']['evidence_ref']}
        original_keyboard=bridge.keyboard
        def tracked_keyboard(*args,**kwargs):
            raw=original_keyboard(*args,**kwargs)
            if raw.get('status') in ('completed','returned'):
                tick_pending['value']=True
            return raw
        bridge.keyboard=tracked_keyboard
        def input_dependency(stage,native,image):
            predicates=perceive(native,image)
            return predicates.get('ready') is True and predicates.get('moved') is False
        def route():
            t0=time.perf_counter_ns();result['timed_start_ns']=t0
            if args.arm=='direct':
                obs=bridge.observe();im=bridge.history[obs['sequence']][1];initial=perceive(obs,im);result['direct_initial_predicates']=initial
                if initial!= {'ready':True,'moved':False}:raise RuntimeError(f'direct initial gate failed: {initial}')
                with bridge.input_guard('forward_target',offset,tail=tail,verify=input_dependency,interaction='keyboard'):
                    raw=bridge.keyboard('forward_target',offset,tail=tail)
                result['action_result']=raw
                post=bridge.observe();im2=bridge.history[post['sequence']][1];pred=perceive(post,im2);result['direct_post_predicates']=pred
                after=coords(game);ok=effect_pass(baseline,after);result['oracle_at_verification']={'position':after,'delta':{'x':after['x']-baseline['x'],'y':after['y']-baseline['y']},'passed':ok,'evidence_ref':'direct-position-readback'}
                result['route_outcome']='TASK_SUCCEEDED' if ok and raw.get('status') in ('completed','returned') else 'NOT_VERIFIED'
                result['effect_observation_sequence']=post['sequence']
            else:
                interface=graph_spec(bridge);binding={'forward':{'interaction':'keyboard','offset':offset,'tail':tail}}
                result['compiled_receipt']=compiled.run(bridge,interface,binding,perceive=perceive,verify_effect=verify_effect,cancelled=lambda:False)
                result['route_outcome']=result['compiled_receipt'].get('outcome')
            result['timed_end_ns']=time.perf_counter_ns();result['caller_path_elapsed_ns']=result['timed_end_ns']-t0
        holder={}
        def invoke():
            try:route()
            except BaseException as exc:holder['exception']=repr(exc)
        worker=threading.Thread(target=invoke,name='efficiency-arm',daemon=True);worker.start()
        samples=[]
        while worker.is_alive():
            samples.append({'monotonic_ns':time.monotonic_ns(),'w_down':key_down(observer,code)})
            time.sleep(.01)
        worker.join();result['during_call_keymap_samples']=samples
        if 'exception' in holder:raise RuntimeError(holder['exception'])
        result['dispatch_elapsed_ms']=round(result.get('caller_path_elapsed_ns',0)/1_000_000,3)
        result['position_after']=coords(game);result['position_delta']={'x':result['position_after']['x']-baseline['x'],'y':result['position_after']['y']-baseline['y']}
        result['independent_w_down_after']=key_down(observer,code)
        if args.arm=='direct':
            execrow=result.get('action_result',{}).get('execution',{});rels=execrow.get('releases',[]);result['release_receipt']=rels[-1] if rels else result.get('action_result',{}).get('release')
        else:
            execfiles=list(bridge_dir.glob('*-execution.json'));found=[]
            for p in execfiles:
                try:
                    obj=json.loads(p.read_text());raw=obj.get('result',{});rels=raw.get('execution',{}).get('releases',[])
                    if rels:found.append({'file':p.name,'receipt':rels[-1],'status':raw.get('status')})
                except Exception:pass
            result['retained_execution_results']=found;result['release_receipt']=found[-1]['receipt'] if found else None
        release=result.get('release_receipt') or {}
        result['gates']={'route_completed':result.get('route_outcome') in ('TASK_SUCCEEDED','TASK_SUCCEEDED') or (args.arm=='direct' and result.get('route_outcome')=='TASK_SUCCEEDED'),'w_observed_down':any(s['w_down'] for s in samples),'release_verified':release.get('verified') is True and release.get('keys_down')==[] and release.get('buttons_down')==[],'independent_w_neutral':result['independent_w_down_after'] is False,'position_changed':effect_pass(baseline,result['position_after']),'effect_receipt_succeeded':bool(result.get('oracle_at_verification',{}).get('passed'))}
        result['passed']=all(result['gates'].values())
        result['outcome']='PASS_SCOPED_ARM' if result['passed'] else 'FAIL_OR_INCOMPLETE'
    except BaseException as exc:
        result['error']=repr(exc);result['outcome']='FAIL_OR_INCOMPLETE';result['passed']=False
    finally:
        if bridge is not None:
            try:result['bridge_terminal']={'recovery_required':bridge.session.recovery_required,'backend_held_keys':dict(bridge.backend.held_keycodes),'backend_held_buttons':sorted(bridge.backend.held_buttons),'sequence':bridge.sequence};bridge.close()
            except Exception as exc:result['bridge_close_error']=repr(exc)
        if observer is not None:
            try:observer.close()
            except Exception:pass
        if game is not None:
            try:game.close()
            except Exception as exc:result['game_close_error']=repr(exc)
        write_json(out/'result.json',result);print(json.dumps(result,sort_keys=True))
    if not result.get('passed'):raise SystemExit(2)

if __name__=='__main__':main()



