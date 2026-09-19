import hashlib, importlib.util, os, shutil, subprocess, sys, time

def emit(status, **fields):
    print(status, fields)

def digest(buf):
    return hashlib.sha256(memoryview(buf).tobytes()).hexdigest()

print("python", sys.version.split()[0])
if importlib.util.find_spec("vizdoom") is None:
    emit("HOLD_MISSING_VIZDOOM")
    raise SystemExit(0)
import vizdoom
print("vizdoom", getattr(vizdoom, "__version__", "unknown"))
if not shutil.which("Xvfb"):
    emit("HOLD_MISSING_XVFB")
    raise SystemExit(0)

xvfb = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1024x768x24", "-nolisten", "tcp"],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
game = None
try:
    time.sleep(1)
    if xvfb.poll() is not None:
        emit("HOLD_XVFB_DID_NOT_START", returncode=xvfb.returncode)
        raise SystemExit(0)
    os.environ["DISPLAY"] = ":99"
    game = vizdoom.DoomGame()
    game.set_window_visible(False)
    game.set_mode(vizdoom.Mode.PLAYER)
    game.set_screen_resolution(vizdoom.ScreenResolution.RES_320X240)
    game.set_doom_scenario_path(vizdoom.scenarios_path + "/basic.wad")
    game.set_doom_map("map01")
    game.set_available_buttons([vizdoom.Button.MOVE_FORWARD])
    game.set_available_game_variables([
        vizdoom.GameVariable.POSITION_X,
        vizdoom.GameVariable.POSITION_Y,
        vizdoom.GameVariable.ANGLE,
    ])
    game.set_episode_timeout(100)
    game.init()
    game.new_episode()
    before = game.get_state()
    if before is None or before.screen_buffer is None:
        emit("HOLD_NO_PRE_ACTION_OBSERVATION")
        raise SystemExit(0)
    before_vars = tuple(float(game.get_game_variable(v)) for v in [
        vizdoom.GameVariable.POSITION_X,
        vizdoom.GameVariable.POSITION_Y,
        vizdoom.GameVariable.ANGLE,
    ])
    before_hash = digest(before.screen_buffer)
    reward = game.make_action([1], 4)
    after = game.get_state()
    if after is None or after.screen_buffer is None:
        emit("HOLD_NO_POST_ACTION_OBSERVATION", reward=reward)
        raise SystemExit(0)
    after_vars = tuple(float(game.get_game_variable(v)) for v in [
        vizdoom.GameVariable.POSITION_X,
        vizdoom.GameVariable.POSITION_Y,
        vizdoom.GameVariable.ANGLE,
    ])
    after_hash = digest(after.screen_buffer)
    delta = tuple(a-b for a,b in zip(after_vars, before_vars))
    print("button MOVE_FORWARD")
    print("action_tics 4")
    print("reward", reward)
    print("before_vars", before_vars)
    print("after_vars", after_vars)
    print("delta", delta)
    print("before_screen_sha256", before_hash)
    print("after_screen_sha256", after_hash)
    game.close()
    game = None
    if any(abs(v) > 1e-9 for v in delta) or before_hash != after_hash:
        emit("PASS_DIRECT_ACTION_EFFECT_BOUNDARY")
    else:
        emit("HOLD_NO_MEASURABLE_STATE_CHANGE")
finally:
    if game is not None:
        game.close()
    xvfb.terminate()
    xvfb.wait(timeout=5)
