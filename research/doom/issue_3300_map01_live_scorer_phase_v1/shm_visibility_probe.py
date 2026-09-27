"""One-session construction probe for external read-only ViZDoom SHM visibility."""
from __future__ import annotations

import ctypes
import json
import mmap
import os
import struct
import time

import vizdoom as vd

WAD = "/assets/freedoom2.wad"
EXPECTED_WAD = "a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b"
import hashlib
if hashlib.sha256(open(WAD, "rb").read()).hexdigest() != EXPECTED_WAD:
    raise SystemExit("STOP_WAD_HASH")

game = vd.DoomGame()
game.set_doom_game_path(WAD)
game.set_doom_scenario_path("")
game.set_doom_map("MAP01")
game.set_mode(vd.Mode.ASYNC_SPECTATOR)
game.set_ticrate(35)
game.set_seed(345334)
game.set_episode_timeout(35 * 60)
game.set_window_visible(False)
game.set_console_enabled(False)
game.set_sound_enabled(False)
game.set_available_buttons([])
game.set_game_args("+viz_debug 2")
game.init()
game.new_episode()

# ViZDoom's named POSIX segment is announced by the engine on stdout. /dev/shm
# directory visibility is expected to expose that object to this same-container
# observer without sending a controller message.
names = os.listdir("/dev/shm")
candidate = next((n for n in names if n.startswith("ViZDoomSM")), None)
result = {
    "setup": "initialized",
    "api_tic": int(game.get_episode_time()),
    "shm_names": names,
    "candidate": candidate,
    "clock_monotonic_ns": time.monotonic_ns(),
}
if candidate:
    libc = ctypes.CDLL(None, use_errno=True)
    fd = libc.shm_open(("/" + candidate).encode(), os.O_RDONLY, 0)
    result["shm_open_fd"] = fd
    result["shm_errno"] = ctypes.get_errno() if fd < 0 else 0
    if fd >= 0:
        result["shm_size"] = os.fstat(fd).st_size
        # Prefix offsets derived from the exact ViZDoom 1.3.0 VIZGameState
        # declaration (seven shared-memory regions, LP64 ABI): GAME_TIC=152,
        # MAP_TIC=216. mmap and fd are both read-only.
        mapped = mmap.mmap(fd, 0, access=mmap.ACCESS_READ)
        os.close(fd)
        deadline = time.monotonic_ns() + 1_500_000_000
        samples = []
        while time.monotonic_ns() < deadline:
            before = time.monotonic_ns()
            samples.append({
                "mono_before_ns": before,
                "game_tic": struct.unpack_from("=I", mapped, 152)[0],
                "map_tic": struct.unpack_from("=I", mapped, 216)[0],
                "api_tic": int(game.get_episode_time()),
                "mono_after_ns": time.monotonic_ns(),
            })
            time.sleep(0.002)
        result["samples"] = samples
        result["sample_count"] = len(samples)
        result["distinct_shm_game_tics"] = sorted({s["game_tic"] for s in samples})
        result["distinct_shm_map_tics"] = sorted({s["map_tic"] for s in samples})
        result["distinct_api_tics"] = sorted({s["api_tic"] for s in samples})
        mapped.close()
game.close()
out = "/results/raw.json"
with open(out, "w") as stream:
    json.dump(result, stream, sort_keys=True, indent=2)
    stream.write("\n")
print("SHM_PROBE_SUMMARY " + json.dumps(
    {k: v for k, v in result.items() if k != "samples"}, sort_keys=True
), flush=True)
