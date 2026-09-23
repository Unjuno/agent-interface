"""ViZDoom ASYNC_SPECTATOR: X11 screenshots and OS keys, no API actions."""
import argparse,contextlib,hashlib,json,os,shutil,sys,threading,time
from pathlib import Path
import vizdoom as vd

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'live_control'))
from session_v2 import Backend,suite
from executor_v2 import Executor


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--seed',type=int,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False);lock=threading.RLock();latest=None;seen=set();s=None;g=None;e=None
    def emit(row):
        nonlocal latest
        with lock:
            row['emit_ns']=time.perf_counter_ns()
            with (a.out/'events.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
            if row['event']=='observation':
                latest=row.copy();key=(row['id'],row['step'])
                if key in seen:return
                seen.add(key)
            elif row['event']=='command':return
            if row['event']=='terminal' and latest is not None:
                row={**row,'latest_sequence':latest['sequence'],'latest_image':latest['image']}
            print(json.dumps(row),flush=True)
    paths=[HERE/'session_v4.py']+[HERE.parent/p for p in ('live_control/session_v2.py','live_control/executor_v2.py',
        'observation_gating/gui_suite.py','observation_gating/exact_gate.py','real_apps_v1/real_app_suite_v1.py',
        'observation_tiles/tile_transport.py','observation_tiles/image_artifact.py')]
    (a.out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2))
    try:
        with (a.out/'setup.txt').open('w') as diagnostics,contextlib.redirect_stdout(diagnostics):
            s=suite.Session()
            atom=s.d.intern_atom('_NET_SUPPORTING_WM_CHECK')
            s._wait(lambda:s.d.screen().root.get_full_property(atom,0) is not None,4,'WM readiness')
            for key in ('DISPLAY','XAUTHORITY','HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_RUNTIME_DIR'):
                os.environ[key]=s.env[key]
            os.environ['SDL_VIDEODRIVER']='x11';os.environ.pop('WAYLAND_DISPLAY',None)
            g=vd.DoomGame();g.load_config(str(Path(vd.scenarios_path)/'basic.cfg'))
            (s.tmp/'doom.ini').write_text('[Doom.Bindings]\nleft=+left\nright=+right\nup=+forward\ndown=+back\nspace=+attack\nctrl=+attack\n')
            g.set_doom_config_path(str(s.tmp/'doom.ini'))
            g.set_mode(vd.Mode.ASYNC_SPECTATOR);g.set_ticrate(35);g.set_seed(a.seed)
            g.set_episode_timeout(35*180);g.set_window_visible(True);g.set_console_enabled(False)
            g.set_sound_enabled(False);g.set_screen_resolution(vd.ScreenResolution.RES_640X480)
            g.set_render_hud(True);g.set_render_crosshair(True);g.set_render_all_frames(True)
            g.set_available_buttons([vd.Button.TURN_LEFT,vd.Button.TURN_RIGHT,vd.Button.MOVE_FORWARD,
                vd.Button.MOVE_BACKWARD,vd.Button.MOVE_LEFT,vd.Button.MOVE_RIGHT,vd.Button.ATTACK])
            g.init()
        from PIL import ImageGrab
        time.sleep(.3)
        windows=s.windows();(a.out/'windows.txt').write_text(windows)
        ImageGrab.grab(xdisplay=s.name).save(a.out/'setup-screen.png')
        candidates=[line for line in windows.splitlines() if 'doom' in line.lower()]
        if len(candidates)!=1:raise RuntimeError('Expected one Doom window: '+repr(windows))
        s.focus(' '.join(candidates[0].split()[3:]))
        # Environment validation only. No engine advance/action calls during wait.
        g.advance_action(1,True)  # refresh spectator-side cached telemetry
        before=g.get_episode_time();wall=time.perf_counter();time.sleep(2)
        g.advance_action(1,True)
        after=g.get_episode_time();elapsed=time.perf_counter()-wall
        assets={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(vd.scenarios_path)/'basic.cfg',Path(vd.scenarios_path)/'basic.wad',Path(vd.__file__).parent/'freedoom2.wad') if p.exists()}
        (a.out/'environment.json').write_text(json.dumps(dict(vizdoom=vd.__version__,mode=str(g.get_mode()),ticrate=g.get_ticrate(),assets=assets,seed=a.seed),indent=2))
        emit(dict(event='clock_probe',before_tic=before,after_tic=after,wall_seconds=elapsed,
                  no_advance_calls_during_wait=True,refresh_calls_outside_wait=2))
        backend=Backend(s,a.out,emit);e=Executor(backend,emit)
        emit(dict(event='ready',task='Basic ViZDoom scenario using Freedoom assets',bindings={'Left':'turn left','Right':'turn right','Up':'forward','Down':'back','space':'attack'}))
        backend.snapshot('initial',0)
        for line in sys.stdin:
            try:
                c=json.loads(line);emit(dict(event='command',command=c,received_ns=time.perf_counter_ns()))
                if c['op']=='submit':e.submit(c['id'],c['steps'],c['expected_sequence'])
                elif c['op']=='cancel':e.cancel(c['id'])
                elif c['op']=='poll':
                    with lock:emit(dict(event='latest_observation',**{k:latest[k] for k in ('sequence','image','capture_ns')},age_ms=(time.perf_counter_ns()-latest['capture_ns'])/1e6))
                elif c['op']=='finish':
                    e.close()
                    if not g.is_episode_finished():g.advance_action(1,True)
                    emit(dict(event='post_control_score',episode_finished=g.is_episode_finished(),
                              player_dead=g.is_player_dead(),episode_tic=g.get_episode_time(),reward=g.get_total_reward()))
                    break
                else:raise ValueError('unsupported command')
            except (ValueError,TypeError,KeyError) as exc:emit(dict(event='rejected',reason=str(exc)))
    finally:
        if e is not None:e.close()
        if g is not None:g.close()
        if s is not None:
            if (s.tmp/'doom.ini').exists():shutil.copy2(s.tmp/'doom.ini',a.out/'doom.ini')
            s.close();shutil.rmtree(s.tmp)


if __name__=='__main__':main()
