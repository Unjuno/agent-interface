import hashlib, importlib.util, os, pathlib, shutil, subprocess, sys, time
def sha(a): return hashlib.sha256(memoryview(a).tobytes()).hexdigest()
def emit(x,**k): print(x,k)
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
    buttons=[vd.Button.TURN_LEFT,vd.Button.TURN_RIGHT,vd.Button.MOVE_FORWARD,vd.Button.MOVE_BACKWARD,vd.Button.MOVE_LEFT,vd.Button.MOVE_RIGHT,vd.Button.ATTACK]
    g.set_available_buttons(buttons); g.set_available_game_variables([vd.GameVariable.AMMO1])
    g.set_episode_timeout(35*40); g.init(); g.new_episode()
    a=g.get_state(); before=float(g.get_game_variable(vd.GameVariable.AMMO1)); ah=sha(a.screen_buffer)
    reward=g.make_action([0,0,0,0,0,0,1],1)
    b=g.get_state(); after=float(g.get_game_variable(vd.GameVariable.AMMO1)); bh=sha(b.screen_buffer)
    print("vizdoom",vd.__version__); print("wad",str(pkg/"freedoom2.wad")); print("mode PLAYER")
    print("buttons TURN_LEFT TURN_RIGHT MOVE_FORWARD MOVE_BACKWARD MOVE_LEFT MOVE_RIGHT ATTACK")
    print("action_vector [0,0,0,0,0,0,1]"); print("action_tics 1"); print("before_ammo1",before); print("after_ammo1",after); print("ammo_delta",after-before); print("reward",reward)
    print("before_screen_sha256",ah); print("after_screen_sha256",bh)
    g.close();g=None
    # A frame change is supplementary only; attack calibration requires the
    # action-specific AMMO1 decrease to avoid animation/no-op false positives.
    emit("PASS_DIRECT_ATTACK_AMMO_BOUNDARY" if after < before else "HOLD_NO_ATTACK_EFFECT")
finally:
    if g is not None:g.close()
    x.terminate();x.wait(timeout=5)
