import importlib.util, os, shutil, subprocess, sys, time

def out(status, **fields):
    print(status, fields)

print("python", sys.version.split()[0])
print("display", os.environ.get("DISPLAY", ""))
print("xvfb", shutil.which("Xvfb") or "MISSING")
if importlib.util.find_spec("vizdoom") is None:
    out("HOLD_MISSING_VIZDOOM")
    raise SystemExit(0)
import vizdoom
print("vizdoom", getattr(vizdoom, "__version__", "unknown"))
if not shutil.which("Xvfb"):
    out("HOLD_MISSING_XVFB")
    raise SystemExit(0)
proc = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1024x768x24", "-nolisten", "tcp"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
try:
    time.sleep(1)
    if proc.poll() is not None:
        out("HOLD_XVFB_DID_NOT_START", returncode=proc.returncode)
        raise SystemExit(0)
    os.environ["DISPLAY"] = ":99"
    game = vizdoom.DoomGame()
    game.set_window_visible(False)
    game.set_mode(vizdoom.Mode.PLAYER)
    game.set_screen_resolution(vizdoom.ScreenResolution.RES_320X240)
    game.set_doom_scenario_path(vizdoom.scenarios_path + "/basic.wad")
    game.set_doom_map("map01")
    game.init()
    game.new_episode()
    state = game.get_state()
    if state is None or state.screen_buffer is None:
        out("HOLD_NO_REAL_OBSERVATION")
        game.close()
        raise SystemExit(0)
    print("observation_shape", tuple(state.screen_buffer.shape))
    game.close()
    out("PASS_REAL_OBSERVATION_BOUNDARY")
finally:
    proc.terminate()
    proc.wait(timeout=5)
