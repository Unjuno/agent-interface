from __future__ import annotations
import argparse, hashlib, json, os, sys, time, traceback
from pathlib import Path
from PIL import ImageGrab
RUNTIME=Path('/mnt/data/map510_runtime/src'); DOOM=RUNTIME/'research/doom'; LIVE=RUNTIME/'research/live_control'; OBS=RUNTIME/'research/observation_gating'
sys.path[:0]=[str(LIVE),str(OBS),str(DOOM),str(Path(__file__).parent)]
import vizdoom as vd
from doom_typed_release_backend_v1 import suite
from input_owner_v10 import InputOwner
from lease_release_v1 import Lease
from metric import decide

TASK='MAP01-PIXEL-SHIFT-MULTISTART-20260917-004'
EXPECTED_METRIC_SHA='04f8ea8c42f950b5e8df9e45cf5a19cc7cc0ab38558b3f7568aabdcb298f93c9'
EXPECTED_IWAD_SHA='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
EXPECTED_RUNTIME_DEPS={
 'research/doom/doom_typed_coast_backend_v1.py':'fda541e12414d6c77b41787eaf208e8dae6b462846ad401d4c7b235b8ae2b079',
 'research/doom/doom_typed_release_backend_v1.py':'ceef50881dc0619ffee5b7ef551ce0851f2650c7371fc37775a80755f077d12f',
 'research/live_control/input_owner_v10.py':'ceae7d9983cd0ba13a35e01ce2ce7dbbf03a0397b23ddc123b0110b4d4de670b',
 'research/live_control/lease.py':'e71f9850d3999a31fcb86c00f9ef7a8ba19bae8d3a8bdc11bf7bd620817a535f',
 'research/live_control/lease_release_v1.py':'b4b1521b5207ea14654463f769b05337685750e9040bed36a8acf006aa1d34ff',
 'research/observation_gating/gui_suite.py':'953a078a06d55b9278bd7b31e176404912340a4f13407e1db343b7776645e97f',
}

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def wrap(x): return ((x+180)%360)-180

def keymap_neutral(display_name,names=('Left','Right')):
    from Xlib import XK,display
    d=display.Display(display_name); bits=d.query_keymap(); out={}
    for n in names:
        c=d.keysym_to_keycode(XK.string_to_keysym(n)); out[n]=bool(bits[c//8] & (1<<(c%8)))
    d.close(); return out

def pulse(owner,key,ms):
    st=owner.call('input_state'); lease=Lease(time.perf_counter_ns()+2_000_000_000); lease.expected_focus=st['focus']
    down=owner.call('down',lease,key); time.sleep(ms/1000); owner.call('up',lease,key); rel=owner.call('release',lease)
    if rel.get('verified') is not True: raise RuntimeError('release unverified')
    return {'key':key,'duration_ms':ms,'down':down,'release':rel}

def capture(session,bbox,path):
    im=ImageGrab.grab(bbox=bbox,xdisplay=session.name).convert('RGB'); im.save(path)
    if im.size!=(640,480): raise RuntimeError(('capture size',im.size))

def run(case,out):
    if sha(Path(__file__).parent/'metric.py')!=EXPECTED_METRIC_SHA: raise RuntimeError('metric source identity changed')
    runtime_hashes={rel:sha(RUNTIME/rel) for rel in EXPECTED_RUNTIME_DEPS}
    if runtime_hashes!=EXPECTED_RUNTIME_DEPS: raise RuntimeError(('runtime dependency identity changed',runtime_hashes))
    out.mkdir(parents=True,exist_ok=False); session=game=owner=None; setup_inputs=[]; scored_inputs=[]; decisions=[]
    try:
        session=suite.Session(); atom=session.d.intern_atom('_NET_SUPPORTING_WM_CHECK'); session._wait(lambda:session.d.screen().root.get_full_property(atom,0) is not None,4,'WM readiness')
        for k in ('DISPLAY','XAUTHORITY','HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_RUNTIME_DIR'): os.environ[k]=session.env[k]
        os.environ['SDL_VIDEODRIVER']='x11'; os.environ.pop('WAYLAND_DISPLAY',None)
        iwad=Path(vd.__file__).parent/'freedoom2.wad'
        if sha(iwad)!=EXPECTED_IWAD_SHA: raise RuntimeError('IWAD identity mismatch')
        config=session.tmp/'doom.ini'; config.write_text('[Doom.Bindings]\nleftarrow=+left\nrightarrow=+right\n',encoding='utf-8')
        game=vd.DoomGame(); game.set_doom_game_path(str(iwad)); game.set_doom_scenario_path(''); game.set_doom_map('MAP01'); game.set_doom_config_path(str(config)); game.set_mode(vd.Mode.ASYNC_SPECTATOR); game.set_ticrate(35); game.set_seed(case['seed']); game.set_doom_skill(1); game.set_episode_timeout(35*60); game.set_window_visible(True); game.set_console_enabled(False); game.set_sound_enabled(False); game.set_screen_resolution(vd.ScreenResolution.RES_640X480); game.set_render_hud(True); game.set_render_crosshair(True); game.set_render_all_frames(True); game.set_available_buttons([vd.Button.TURN_LEFT,vd.Button.TURN_RIGHT]); game.set_available_game_variables([vd.GameVariable.ANGLE,vd.GameVariable.DEATHCOUNT]); game.init()
        time.sleep(.3); windows=session.windows(); (out/'windows.txt').write_text(windows); cand=[l for l in windows.splitlines() if 'doom' in l.lower()]
        if len(cand)!=1: raise RuntimeError(('doom window',cand))
        session.focus(' '.join(cand[0].split()[3:])); time.sleep(.2)
        wid=int(cand[0].split()[0],16); w=session.d.create_resource_object('window',wid); g=w.get_geometry(); pos=session.d.screen().root.translate_coords(w,0,0); bbox=(int(pos.x),int(pos.y),int(pos.x+g.width),int(pos.y+g.height))
        if (g.width,g.height)!=(640,480): raise RuntimeError(('geometry',g.width,g.height))
        owner=InputOwner(session.name); game.advance_action(1,True); time.sleep(.15); game.advance_action(1,True)
        initial_yaw=float(game.get_game_variable(vd.GameVariable.ANGLE))
        for _ in range(int(case['setup_right_pulses'])):
            setup_inputs.append(pulse(owner,'Right',90)); time.sleep(.1)
        game.advance_action(1,True)
        ref=out/'reference.png'; capture(session,bbox,ref); ref_yaw=float(game.get_game_variable(vd.GameVariable.ANGLE)); ref_sha=sha(ref)
        controller_ref=None if case['kind']=='missing_reference' else ref
        for _ in range(case['displacement']): scored_inputs.append(pulse(owner,'Right',90)); time.sleep(.1)
        game.advance_action(1,True); cur=out/'current_00.png'; capture(session,bbox,cur); cur_yaw=float(game.get_game_variable(vd.GameVariable.ANGLE))
        d=decide('HORIZONTAL_SHIFT_STOP',controller_ref,cur); decisions.append({'correction':0,'decision':d,'image':cur.name,'image_sha256':sha(cur),'evaluator_yaw':cur_yaw,'yaw_error':wrap(cur_yaw-ref_yaw)})
        status=d['status']; corrections=0
        while status=='CONTINUE' and corrections<6:
            corrections+=1; scored_inputs.append(pulse(owner,'Left',90)); time.sleep(.1); game.advance_action(1,True)
            cur=out/f'current_{corrections:02d}.png'; capture(session,bbox,cur); cur_yaw=float(game.get_game_variable(vd.GameVariable.ANGLE)); d=decide('HORIZONTAL_SHIFT_STOP',controller_ref,cur); status=d['status']
            decisions.append({'correction':corrections,'decision':d,'image':cur.name,'image_sha256':sha(cur),'evaluator_yaw':cur_yaw,'yaw_error':wrap(cur_yaw-ref_yaw)})
        if status=='CONTINUE': status='BUDGET_EXHAUSTED'
        final=decisions[-1]; final_state=owner.call('input_state'); neutral=keymap_neutral(session.name); deaths=int(game.get_game_variable(vd.GameVariable.DEATHCOUNT))
        result={**case,'task':TASK,'arm':'HORIZONTAL_SHIFT_STOP','schema':'map01-pixel-shift-multistart-case-v1','initial_yaw':initial_yaw,'reference_yaw':ref_yaw,'reference_yaw_delta_from_initial':wrap(ref_yaw-initial_yaw),'reference_sha256':ref_sha,'client_bbox':bbox,'decisions':decisions,'terminal_status':status,'correction_pulses':corrections,'terminal_yaw_error':final['yaw_error'],'within_6deg':abs(final['yaw_error'])<=6.0,'false_matched':status=='MATCHED' and abs(final['yaw_error'])>6.0,'neutral_keymap':neutral,'owner_records':owner.records,'owned_keys_final':final_state['owned_keycodes'],'death_count':deaths,'setup_input_program_count':len(setup_inputs),'scored_input_program_count':len(scored_inputs),'source':{'metric_py':sha(Path(__file__).parent/'metric.py'),'run_case_py':sha(__file__)},'runtime':{'iwad_sha256':sha(iwad),'dependency_sha256':runtime_hashes}}
        (out/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps({'id':case['id'],'status':status,'setup':case['setup_right_pulses'],'pulses':corrections,'err':final['yaw_error'],'ref_delta':result['reference_yaw_delta_from_initial'],'within':result['within_6deg']}),flush=True)
        return result
    finally:
        if owner:
            try: owner.close()
            except Exception: traceback.print_exc()
        if game:
            try: game.close()
            except Exception: traceback.print_exc()
        if session:
            try: session.close()
            except Exception: traceback.print_exc()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--case',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); run(json.loads(a.case.read_text()),a.out)
if __name__=='__main__': main()
