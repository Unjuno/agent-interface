import hashlib, os, subprocess, time, vizdoom

def h(b):
    return hashlib.sha256(memoryview(b).tobytes()).hexdigest()

x = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1024x768x24", "-nolisten", "tcp"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
g = None
try:
    time.sleep(1)
    os.environ["DISPLAY"] = ":99"
    g = vizdoom.DoomGame()
    p = os.path.dirname(vizdoom.__file__)
    g.set_doom_game_path(os.path.join(p, "freedoom2.wad"))
    g.set_doom_map("MAP01")
    g.set_mode(vizdoom.Mode.PLAYER)
    g.set_screen_resolution(vizdoom.ScreenResolution.RES_320X240)
    g.set_screen_format(vizdoom.ScreenFormat.RGB24)
    g.set_available_buttons([vizdoom.Button.MOVE_FORWARD, vizdoom.Button.USE, vizdoom.Button.TURN_LEFT, vizdoom.Button.TURN_RIGHT])
    g.set_available_game_variables([vizdoom.GameVariable.ANGLE])
    g.set_episode_timeout(100)
    g.set_window_visible(False)
    g.set_sound_enabled(False)
    g.init(); g.new_episode()
    before = g.get_state()
    before_angle = float(g.get_game_variable(vizdoom.GameVariable.ANGLE))
    before_hash = h(before.screen_buffer)
    reward = g.make_action([0, 0, 1, 0], 4)
    after = g.get_state()
    after_angle = float(g.get_game_variable(vizdoom.GameVariable.ANGLE))
    after_hash = h(after.screen_buffer)
    print({"vizdoom": getattr(vizdoom, "__version__", "unknown"), "fixture": "freedoom2.wad/MAP01/RGB24/PLAYER", "action": [0,0,1,0], "tics": 4, "before_angle": before_angle, "after_angle": after_angle, "angle_delta": after_angle-before_angle, "reward": reward, "before_screen_sha256": before_hash, "after_screen_sha256": after_hash, "decision": "PASS_DIRECT_TURN_EFFECT_BOUNDARY" if (after_angle != before_angle or before_hash != after_hash) else "HOLD_NO_MEASURABLE_TURN"})
finally:
    if g is not None: g.close()
    x.terminate(); x.wait(timeout=5)
