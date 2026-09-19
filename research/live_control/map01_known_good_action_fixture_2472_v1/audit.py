import hashlib, importlib.util, os, pathlib, shutil, subprocess, sys, time

def sha(a): return hashlib.sha256(memoryview(a).tobytes()).hexdigest()
def emit(x, **k): print(x, k)
if importlib.util.find_spec("vizdoom") is None or not shutil.which("Xvfb"):
    emit("HOLD_MISSING_RUNTIME"); raise SystemExit(0)
import vizdoom as vd
pkg=pathlib.Path(vd.__file__).resolve().parent
x=subprocess.Popen(["Xvfb",":99","-screen","0","1024x768x24","-nolisten","tcp"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
g=None
try:
    time.sleep(1); os.environ["DISPLAY"]=":99"
    if x.poll() is not None: emit("STOP_XVFB"); raise SystemExit(0)
    g=vd.DoomGame(); g.set_doom_game_path(str(pkg/"freedoom2.wad")); g.set_doom_map("MAP01")
    g.set_mode(vd.Mode.PLAYER); g.set_window_visible(False); g.set_sound_enabled(False)
    g.set_screen_resolution(vd.ScreenResolution.RES_320X240); g.set_screen_format(vd.ScreenFormat.RGB24)
    g.set_available_buttons([vd.Button.MOVE_FORWARD,vd.Button.USE,vd.Button.TURN_LEFT,vd.Button.TURN_RIGHT])
    g.set_episode_timeout(35*40); g.init(); g.new_episode()
    a=g.get_state(); before=float(g.get_game_variable(vd.GameVariable.ANGLE)) if False else None
    ah=sha(a.screen_buffer)
    # Match the repository's known-good four-element vector convention.
    reward=g.make_action([0,0,1,0],4)
    b=g.get_state(); bh=sha(b.screen_buffer)
    print("vizdoom",vd.__version__); print("wad",str(pkg/"freedoom2.wad")); print("mode PLAYER")
    print("action_vector [0,0,1,0]"); print("action_tics 4"); print("reward",reward)
    print("before_screen_sha256",ah); print("after_screen_sha256",bh)
    g.close(); g=None
    emit("PASS_DIRECT_FIXTURE_OBSERVATION_CHANGE" if ah!=bh else "HOLD_FIXTURE_NO_FRAME_CHANGE")
finally:
    if g is not None:g.close()
    x.terminate();x.wait(timeout=5)
