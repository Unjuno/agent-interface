"""Excluded construction probe for MAP01 explicit clock-driving boundary."""
import hashlib
import json
import time
from pathlib import Path

import vizdoom as vd
from session_map01_v13 import _coherent_progress_sample

FIX = Path("/fixture/fixture")
MANIFEST = json.loads((FIX / "fixture.json").read_text())
WAD = Path(vd.__file__).parent / "freedoom2.wad"
OUT = Path("/results/raw.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TraceProxy:
    METHODS = {
        "get_episode_time", "is_episode_finished", "is_player_dead",
        "get_game_variable", "get_ticrate", "is_episode_timeout_reached",
    }

    def __init__(self, game):
        self.game = game
        self.trace = []

    def __getattr__(self, name):
        value = getattr(self.game, name)
        if name not in self.METHODS or not callable(value):
            return value

        def observed(*args, **kwargs):
            start = time.perf_counter_ns()
            result = value(*args, **kwargs)
            end = time.perf_counter_ns()
            self.trace.append({
                "name": name, "start_ns": start, "end_ns": end,
                "args": [str(arg) for arg in args], "result": result,
            })
            return result

        return observed


def new_game():
    game = vd.DoomGame()
    game.set_doom_game_path(str(WAD))
    game.set_doom_scenario_path("")
    game.set_doom_map(MANIFEST["map"])
    game.set_doom_skill(MANIFEST["skill"])
    game.set_seed(MANIFEST["seed"])
    game.set_mode(vd.Mode.ASYNC_SPECTATOR)
    game.set_ticrate(35)
    game.set_window_visible(True)
    game.set_sound_enabled(False)
    game.set_render_hud(False)
    game.set_available_game_variables([
        vd.GameVariable.KILLCOUNT, vd.GameVariable.DEATHCOUNT,
    ])
    game.init()
    game.load(str(FIX / MANIFEST["save_file"]))
    game.advance_action(1, True)  # identical startup refresh in predecessor smoke
    return game


def main():
    result = {
        "schema": "map01-explicit-clock-drive-construction-v1",
        "formal_allocation": False,
        "image_id": "sha256:8d984b04efe5bca7bd9b3808aac4f56bd273a6a1ada76cd51939253b874244ca",
        "vizdoom": vd.__version__, "mode": "ASYNC_SPECTATOR",
        "requested_ticrate": 35,
        "fixture_sha256": sha(FIX / "fixture.json"),
        "save_sha256": sha(FIX / MANIFEST["save_file"]),
        "wad_sha256": sha(WAD), "conditions": [],
    }
    for condition in ("passive", "paced_advance_action_1"):
        game = new_game()
        row = {"condition": condition, "samples": [], "setup": "initialized"}
        try:
            row["start_tic"] = int(game.get_episode_time())
            start_ns = time.perf_counter_ns()
            for index in range(20):
                target = start_ns + (index + 1) * 28_571_429
                while time.perf_counter_ns() < target:
                    time.sleep(min(0.001, max(0, (target - time.perf_counter_ns()) / 1e9)))
                tic_before_drive = int(game.get_episode_time())
                drive_start = time.perf_counter_ns()
                if condition == "paced_advance_action_1":
                    game.advance_action(1, True)
                drive_end = time.perf_counter_ns()
                proxy = TraceProxy(game)
                scorer_start = time.perf_counter_ns()
                score = _coherent_progress_sample(proxy, vd.GameVariable, 600)
                scorer_end = time.perf_counter_ns()
                row["samples"].append({
                    "index": index, "target_elapsed_ns": (index + 1) * 28_571_429,
                    "observed_elapsed_ns": drive_end - start_ns,
                    "tic_before_drive": tic_before_drive,
                    "tic_after_drive": int(game.get_episode_time()),
                    "drive_start_ns": drive_start, "drive_end_ns": drive_end,
                    "scorer_start_ns": scorer_start, "scorer_end_ns": scorer_end,
                    "scorer_return": score.as_dict(), "scorer_getter_trace": proxy.trace,
                })
            row["end_tic"] = int(game.get_episode_time())
            row["closed"] = True
        except BaseException as exc:
            row["error"] = {"type": type(exc).__name__, "message": str(exc)}
            try:
                game.close()
                row["closed"] = True
            except BaseException as close_exc:
                row["closed"] = False
                row["close_error"] = {"type": type(close_exc).__name__, "message": str(close_exc)}
        else:
            game.close()
        result["conditions"].append(row)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "schema": result["schema"], "formal_allocation": False,
        "conditions": [{
            "name": row["condition"], "start_tic": row.get("start_tic"),
            "end_tic": row.get("end_tic"), "rows": len(row["samples"]),
            "closed": row.get("closed"), "error": row.get("error"),
        } for row in result["conditions"]],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
