import hashlib, importlib.util, os, shutil, subprocess, sys, time

def h(b): return hashlib.sha256(memoryview(b).tobytes()).hexdigest()
def emit(x, **kw): print(x, kw)
if importlib.util.find_spec("vizdoom") is None or not shutil.which("Xvfb"):
    emit("HOLD_MISSING_RUNTIME"); raise SystemExit(0)
import vizdoom
x=subprocess.Popen(["Xvfb",":99","-screen","0","1024x768x24","-nolisten","tcp"],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
g=None
try:
    time.sleep(1); os.environ["DISPLAY"]=":99"
    if x.poll() is not None: emit("STOP_XVFB"); raise SystemExit(0)
    g=vizdoom.DoomGame(); g.set_window_visible(False); g.set_mode(vizdoom.Mode.PLAYER)
    g.set_screen_resolution(vizdoom.ScreenResolution.RES_320X240)
    g.set_doom_scenario_path(vizdoom.scenarios_path+"/basic.wad"); g.set_doom_map("map01")
    g.set_available_buttons([vizdoom.Button.TURN_LEFT])
    g.set_available_game_variables([vizdoom.GameVariable.ANGLE])
    g.set_episode_timeout(100); g.init(); g.new_episode()
    a=g.get_state(); before=float(g.get_game_variable(vizdoom.GameVariable.ANGLE))
    ah=h(a.screen_buffer); reward=g.make_action([1],4)
    b=g.get_state(); after=float(g.get_game_variable(vizdoom.GameVariable.ANGLE)); bh=h(b.screen_buffer)
    print("vizdoom",getattr(vizdoom,"__version__","unknown")); print("button TURN_LEFT")
    print("before_angle",before); print("after_angle",after); print("delta",after-before)
    print("reward",reward); print("before_screen_sha256",ah); print("after_screen_sha256",bh)
    g.close(); g=None
    emit("PASS_DIRECT_TURN_EFFECT_BOUNDARY" if after!=before or ah!=bh else "HOLD_NO_MEASURABLE_TURN")
finally:
    if g is not None: g.close()
    x.terminate(); x.wait(timeout=5)
